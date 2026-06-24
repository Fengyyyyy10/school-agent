from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Dict, List

from tools import login_and_crawl, check_local_data, load_images_for_analysis


class StudentDataState(TypedDict):
    username: str
    password: str
    question: Optional[str]
    answer: Optional[str]
    error: Optional[str]
    has_local_data: bool
    image_count: int
    image_paths: List[str]
    crawl_result: Optional[Dict]
    status: str


class StudentWorkflow:
    def __init__(self, ai_module):
        self.ai = ai_module
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(StudentDataState)

        workflow.add_node("check_local", self.check_local_node)
        workflow.add_node("crawl_data", self.crawl_data_node)
        workflow.add_node("load_pdfs", self.load_pdfs_node)
        workflow.add_node("ai_qa", self.ai_qa_node)

        workflow.set_entry_point("check_local")

        workflow.add_conditional_edges(
            "check_local",
            self._should_crawl,
            {
                "crawl": "crawl_data",
                "skip": "load_pdfs"
            }
        )

        workflow.add_edge("crawl_data", "load_pdfs")
        workflow.add_edge("load_pdfs", "ai_qa")
        workflow.add_edge("ai_qa", END)

        return workflow.compile()

    def _should_crawl(self, state: StudentDataState) -> str:
        if state.get("has_local_data") and state.get("image_count", 0) > 0:
            return "skip"
        return "crawl"

    def check_local_node(self, state: StudentDataState) -> StudentDataState:
        try:
            result = check_local_data.invoke({"username": state["username"]})
            state["has_local_data"] = result.get("has_data", False)
            state["image_count"] = result.get("image_count", 0)
            state["status"] = "checked"
            state["error"] = None
            return state
        except Exception as e:
            state["error"] = f"检查本地数据失败: {str(e)}"
            state["status"] = "failed"
            return state

    def crawl_data_node(self, state: StudentDataState) -> StudentDataState:
        if state.get("error"):
            return state

        try:
            state["status"] = "crawling"
            result = login_and_crawl.invoke({
                "username": state["username"],
                "password": state["password"]
            })
            state["crawl_result"] = result
            if result.get("status") == "success":
                state["image_count"] = result.get("image_count", 0)
                state["status"] = "crawled"
                state["error"] = None
            else:
                state["error"] = result.get("message", "爬取失败")
                state["status"] = "failed"
            return state
        except Exception as e:
            state["error"] = f"爬取数据失败: {str(e)}"
            state["status"] = "failed"
            return state

    def load_pdfs_node(self, state: StudentDataState) -> StudentDataState:
        if state.get("error"):
            return state

        try:
            result = load_images_for_analysis.invoke({"username": state["username"]})
            if result.get("status") == "success":
                state["image_paths"] = result.get("image_paths", [])
                state["image_count"] = result.get("image_count", 0)
                state["status"] = "pdfs_loaded"
                state["error"] = None
            else:
                state["error"] = result.get("message", "加载PDF失败")
                state["status"] = "failed"
            return state
        except Exception as e:
            state["error"] = f"加载PDF失败: {str(e)}"
            state["status"] = "failed"
            return state

    def ai_qa_node(self, state: StudentDataState) -> StudentDataState:
        if state.get("error"):
            return state

        if not state.get("question"):
            state["answer"] = "请提供问题"
            state["status"] = "completed"
            return state

        if not state.get("image_paths") or len(state["image_paths"]) == 0:
            state["error"] = "没有可用的PDF数据"
            state["status"] = "failed"
            return state

        try:
            state["status"] = "analyzing"
            agent = self.ai.GLMAgent()
            answer = agent.analyze_pdfs(state["question"], state["image_paths"])
            state["answer"] = answer
            state["status"] = "completed"
            state["error"] = None
            return state
        except Exception as e:
            state["answer"] = None
            state["error"] = f"AI问答失败: {str(e)}"
            state["status"] = "failed"
            return state

    def run(self, username: str, password: str, question: str):
        initial_state = {
            'username': username,
            'password': password,
            'question': question,
            'answer': None,
            'error': None,
            'has_local_data': False,
            'image_count': 0,
            'image_paths': [],
            'crawl_result': None,
            'status': 'started'
        }

        result = self.graph.invoke(initial_state)
        return result