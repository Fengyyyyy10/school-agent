from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import sys
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

import spider
import ai_qa
import campus_notice
import campus_navigation
import library_service
from ai_qa import GLMAgent, get_page_label
from campus_notice import get_notices, search_notices, get_notice_detail
from campus_navigation import get_all_locations, get_locations_by_category, search_locations, get_location_detail
from library_service import search_books, get_borrowed_books, get_borrow_history, get_hot_books, get_book_detail
from workflow import StudentWorkflow

app = FastAPI(title="Campus Information API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '学生信息')
tasks = {}
task_id_counter = 0
workflow = StudentWorkflow(ai_qa)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginInitResponse(BaseModel):
    success: bool
    message: str
    ready: bool = False
    task_id: Optional[str] = None
    username: Optional[str] = None
    local_files: int = 0


class ChatRequest(BaseModel):
    username: str
    question: str


class ChatResponse(BaseModel):
    success: bool
    answer: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = None


class AIQARequest(BaseModel):
    question: str
    username: Optional[str] = None


class RefreshRequest(BaseModel):
    username: str
    password: str


class QARequest(BaseModel):
    username: str
    password: str
    question: str


class QAResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    answer: Optional[str] = None
    source: Optional[str] = None


def get_student_dir(username: str) -> str:
    return os.path.join(DATA_DIR, username)


def has_local_pdf_data(username: str) -> bool:
    student_dir = get_student_dir(username)
    if not os.path.exists(student_dir):
        return False
    for filename in os.listdir(student_dir):
        if filename.endswith('.pdf'):
            return True
    return False


def count_local_pdf_files(username: str) -> int:
    student_dir = get_student_dir(username)
    if not os.path.exists(student_dir):
        return 0
    return sum(1 for f in os.listdir(student_dir) if f.endswith('.pdf'))


def load_pdf_paths(username: str) -> list:
    student_dir = get_student_dir(username)
    paths = []
    if not os.path.exists(student_dir):
        return paths
    for filename in os.listdir(student_dir):
        if filename.endswith('.pdf'):
            paths.append(os.path.join(student_dir, filename))
    return sorted(paths, key=lambda x: os.path.basename(x))


def build_pdfs_summary(username: str) -> dict:
    student_dir = get_student_dir(username)
    summary = {}
    if not os.path.exists(student_dir):
        return summary
    for filename in os.listdir(student_dir):
        if filename.endswith('.pdf'):
            filepath = os.path.join(student_dir, filename)
            size = os.path.getsize(filepath)
            summary[filename] = {
                'label': get_page_label(filename),
                'size_bytes': size,
            }
    return summary


async def verify_credentials(username: str, password: str) -> bool:
    s = spider.CuitSpider()
    s.save_dir = get_student_dir(username)
    os.makedirs(s.save_dir, exist_ok=True)
    try:
        await s.start_browser()
        return await s.login(username, password)
    finally:
        try:
            await s.stop_browser()
        except Exception:
            pass


async def run_crawler_only(username: str, password: str):
    s = spider.CuitSpider()
    s.username = username
    s.save_dir = get_student_dir(username)
    os.makedirs(s.save_dir, exist_ok=True)
    try:
        await s.start_browser()
        if not await s.login(username, password):
            return False, "Login failed"
        await s.get_all_student_data(username)
        return True, "Crawl complete"
    except Exception as e:
        return False, f"Crawl error: {str(e)}"
    finally:
        try:
            await s.stop_browser()
        except Exception:
            pass


async def crawler_task(task_id: str, username: str, password: str):
    global tasks
    try:
        tasks[task_id]["status"] = "running"
        tasks[task_id]["progress"] = "Crawling student data..."
        success, message = await run_crawler_only(username, password)
        if success:
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["progress"] = "Crawl complete"
            tasks[task_id]["local_files"] = count_local_pdf_files(username)
        else:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = message
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)


@app.post("/api/login", response_model=LoginInitResponse)
async def login(request: LoginRequest):
    global task_id_counter
    local_count = await asyncio.to_thread(count_local_pdf_files, request.username)
    if local_count > 0:
        return LoginInitResponse(
            success=True,
            message=f"Login success, {local_count} local PDFs found",
            ready=True,
            username=request.username,
            local_files=local_count
        )
    try:
        valid = await verify_credentials(request.username, request.password)
    except Exception as e:
        return LoginInitResponse(
            success=False,
            message=f"Login error: {str(e)}",
            ready=False,
            username=request.username
        )
    if not valid:
        return LoginInitResponse(
            success=False,
            message="Login failed, please check credentials",
            ready=False,
            username=request.username
        )
    task_id = f"task_{task_id_counter}"
    task_id_counter += 1
    tasks[task_id] = {
        "status": "running",
        "username": request.username,
        "password": request.password,
        "progress": "Crawling student data..."
    }
    asyncio.create_task(crawler_task(task_id, request.username, request.password))
    return LoginInitResponse(
        success=True,
        message="Login success, fetching data...",
        ready=False,
        task_id=task_id,
        username=request.username,
        local_files=0
    )



@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in tasks:
        return {"success": False, "message": "Task not found"}
    task = tasks[task_id]
    resp = {"success": True, "task_id": task_id, "status": task["status"], "message": task.get("progress", "")}
    if task["status"] == "completed":
        resp["local_files"] = task.get("local_files", 0)
        resp["ready"] = True
        if "answer" in task: resp["answer"] = task["answer"]
    elif task["status"] == "failed":
        resp["error"] = task.get("error", "Unknown error")
        resp["ready"] = False
    else: resp["ready"] = False
    return resp


@app.post("/api/ai/qa")
async def ai_qa_endpoint(request: AIQARequest):
    try:
        answer = None; source = "none"
        if request.username:
            student_dir = get_student_dir(request.username)
            if os.path.exists(student_dir):
                txt_files = [f for f in os.listdir(student_dir) if f.endswith('.txt')]
                if txt_files:
                    agent = GLMAgent()
                    answer = await asyncio.to_thread(agent.analyze_texts, request.question, student_dir)
                    source = "Text knowledge base"
            if not answer:
                pdf_paths = load_pdf_paths(request.username)
                agent = GLMAgent()
                answer = await asyncio.to_thread(agent.analyze_pdfs, request.question, pdf_paths)
                source = f"Local PDF ({len(pdf_paths)} docs)"
        if not answer:
            return {"success": False, "message": "No username/data", "answer": None}
        return {"success": True, "answer": answer, "message": f"Based on {source}"}
    except Exception as e:
        return {"success": False, "message": f"AI QA: {str(e)}", "answer": None}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        pdf_paths = load_pdf_paths(request.username)
        if not pdf_paths:
            return ChatResponse(success=False, message="No local PDF data", source="none")
        agent = GLMAgent()
        answer = await asyncio.to_thread(agent.analyze_pdfs, request.question, pdf_paths)
        return ChatResponse(success=True, answer=answer, source="pdf_knowledge_base")
    except Exception as e:
        return ChatResponse(success=False, message=f"Chat failed: {str(e)}")


@app.post("/api/refresh")
async def refresh_data(request: RefreshRequest):
    global task_id_counter
    if not await asyncio.to_thread(has_local_pdf_data, request.username):
        return {"success": False, "message": "No local data, login first"}
    task_id = f"task_{task_id_counter}"
    task_id_counter += 1
    tasks[task_id] = {"status": "running", "username": request.username, "password": request.password, "progress": "Refreshing..."}
    asyncio.create_task(crawler_task(task_id, request.username, request.password))
    return {"success": True, "task_id": task_id, "message": "Refresh submitted"}


@app.post("/api/task/submit")
async def submit_task(request: QARequest):
    global task_id_counter
    task_id = f"task_{task_id_counter}"
    task_id_counter += 1
    tasks[task_id] = {"status": "running", "username": request.username, "password": request.password, "question": request.question, "progress": "Running workflow..."}
    async def wf():
        try:
            result = await asyncio.to_thread(workflow.run, request.username, request.password, request.question)
            if result.get("status") == "completed" and result.get("answer"):
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["progress"] = "Workflow complete"
                tasks[task_id]["answer"] = result["answer"]
            else:
                tasks[task_id]["status"] = "failed"
                tasks[task_id]["error"] = result.get("error", "Unknown")
        except Exception as e:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = str(e)
    asyncio.create_task(wf())
    return {"success": True, "task_id": task_id, "message": "Task submitted"}


@app.get("/api/student/{username}")
async def get_student_data(username: str):
    try:
        pdfs = build_pdfs_summary(username)
        if not pdfs: return {"success": False, "message": "No PDF data"}
        return {"success": True, "data": {"username": username, "pages": pdfs, "total_files": len(pdfs)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/students")
async def get_students():
    try:
        if not os.path.exists(DATA_DIR): return {"students": []}
        students = []
        for item in os.listdir(DATA_DIR):
            p = os.path.join(DATA_DIR, item)
            if os.path.isdir(p):
                cnt = sum(1 for f in os.listdir(p) if f.endswith(".pdf"))
                students.append({"username": item, "image_count": cnt, "ready": cnt > 0})
        return {"students": students}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/student/{username}/status")
async def get_student_status(username: str):
    d = get_student_dir(username)
    if not os.path.exists(d): return {"exists": False, "image_count": 0, "ready": False}
    c = count_local_pdf_files(username)
    return {"exists": True, "image_count": c, "ready": c > 0}


@app.get("/api/student/{username}/pages")
async def get_student_pages(username: str):
    pdfs = build_pdfs_summary(username)
    if not pdfs: return {"success": False, "message": "No PDF data"}
    return {"success": True, "data": {"username": username, "pages": pdfs, "total_files": len(pdfs)}}


@app.get("/api/student/{username}/page/{filename}")
async def get_student_page(username: str, filename: str):
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, detail="Invalid filename")
    fp = os.path.join(get_student_dir(username), filename)
    if not os.path.exists(fp): raise HTTPException(404, detail="Not found")
    import base64
    b64 = base64.b64encode(open(fp, "rb").read()).decode()
    return {"success": True, "data": {"username": username, "filename": filename, "label": get_page_label(filename), "pdf_base64": f"data:application/pdf;base64,{b64}"}}


@app.get("/api/notices")
async def api_notices(type: str = "", page: int = 1, page_size: int = 20):
    return get_notices(type, page, page_size)

@app.get("/api/notices/search")
async def api_notices_search(keyword: str = ""):
    if not keyword: return {"success": False, "notices": [], "total": 0}
    return search_notices(keyword)

@app.get("/api/notices/{notice_id}")
async def api_notice_detail(notice_id: int):
    return get_notice_detail(notice_id)


@app.get("/api/navigation/locations")
async def api_nav_locations(category: str = ""):
    if category: return get_locations_by_category(category)
    return get_all_locations()

@app.get("/api/navigation/search")
async def api_nav_search(keyword: str = ""):
    if not keyword: return {"success": False, "locations": [], "total": 0}
    return search_locations(keyword)

@app.get("/api/navigation/location/{location_id}")
async def api_nav_detail(location_id: str):
    return get_location_detail(location_id)


@app.get("/api/library/search")
async def api_lib_search(keyword: str = "", page: int = 1, page_size: int = 20):
    if not keyword: return {"success": False, "books": [], "total": 0}
    return search_books(keyword, page, page_size)

@app.get("/api/library/borrowed")
async def api_lib_borrowed(username: str = ""):
    return get_borrowed_books(username)

@app.get("/api/library/history")
async def api_lib_history(username: str = ""):
    return get_borrow_history(username)

@app.get("/api/library/hot")
async def api_lib_hot(limit: int = 10):
    return get_hot_books(limit)

@app.get("/api/library/book/{book_id}")
async def api_lib_book_detail(book_id: str):
    return get_book_detail(book_id)


@app.get("/")
async def root():
    return {"message": "Campus API", "version": "2.0.0", "backend": "FastAPI", "llm": "GLM-4.6V", "features": ["ai_qa","notices","navigation","library","crawler"]}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)