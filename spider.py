import os, re, random, asyncio
from playwright.async_api import async_playwright


class CuitSpider:
    def __init__(self, headless=True):
        self.pw = self.browser = self.ctx = self.page = None
        self.logged_in = False; self.save_dir = ""; self.headless = headless

    async def _delay(self, a=500, b=2000):
        await asyncio.sleep(random.uniform(a/1000, b/1000))

    async def start_browser(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(headless=self.headless, args=["--no-sandbox","--disable-gpu"])
        self.ctx = await self.browser.new_context(viewport={"width":1920,"height":1080}, locale="zh-CN")
        self.page = await self.ctx.new_page()

    async def stop_browser(self):
        try:
            if self.ctx: await self.ctx.close()
            if self.browser: await self.browser.close()
        except: pass
        try:
            if self.pw: await self.pw.stop()
        except: pass

    async def login(self, u, p):
        for i in range(2):
            try:
                if await self._login(u,p): return True
                await self._delay(2000,4000)
            except: await self._delay(2000,4000)
        return False

    async def _login(self, u, p):
        print("[Login] Starting...")
        try:
            await self.page.goto("https://ywtb.cuit.edu.cn/#/login", timeout=60000)
            await self._delay(2000,4000)
            await self.page.wait_for_load_state("networkidle", timeout=30000)
            for attempt in range(5):
                iv = await self.page.query_selector_all("input")
                if len(iv) >= 2:
                    await iv[0].click(); await self._delay(200,500)
                    await iv[0].fill(""); await self._delay(200,500)
                    await iv[0].fill(u)
                    await self._delay(500,1000)
                    await iv[1].click(); await self._delay(200,500)
                    await iv[1].fill(""); await self._delay(200,500)
                    await iv[1].fill(p)
                    print("[Login] Filled credentials")
                    break
                await asyncio.sleep(2)
            await self._delay(1000,2000)
            for _ in range(5):
                await self.page.keyboard.press("Enter")
                await self._delay(800, 1200)
                if "login" not in self.page.url.lower():
                    self.logged_in = True; print("[Login] OK"); return True
            if "login" in self.page.url.lower():
                await self.page.evaluate('document.querySelectorAll("button").forEach(b => { var t = b.textContent; if(t.indexOf("登录")>=0 || t.indexOf("登")>=0) b.click() })')
                print("[Login] Clicked login button via JS")
                await self._delay(3000, 5000)
            if "login" in self.page.url.lower():
                await self.page.evaluate("document.querySelectorAll('button,[type=submit]').forEach(el => el.dispatchEvent(new Event('click', {bubbles:true})))")
                print("[Login] Dispatched click events")
                await self._delay(3000, 5000)
            if "login" not in self.page.url.lower():
                self.logged_in = True; print("[Login] OK"); return True
            await self._delay(2000,3000)
            if "login" not in self.page.url.lower(): self.logged_in = True; return True
            print("[Login] Failed:", self.page.url)
            return False
        except Exception as e:
            print("[Login] Exception:", e)
            return False

    def _resolve_captcha(self, q):
        q = q.replace("?","?").replace("=","=").replace(" ","")
        m = re.search(r"(\d+)\s*([+\-\u00d7x*])\s*(\d+)", q)
        if m:
            a,op,b = int(m.group(1)), m.group(2), int(m.group(3))
            if op=="+": return str(a+b)
            if op=="-": return str(a-b)
            if op in ("\u00d7","x","*"): return str(a*b)
        return None

    async def _fill_captcha(self, a):
        for s in ['input[placeholder*="验证码"]','input[placeholder*="code"]']:
            try:
                el = await self.page.query_selector(s)
                if el: await el.fill(a); return True
            except: pass
        return False

    async def save_pdf(self, fn):
        if not self.save_dir or not self.page: return
        os.makedirs(self.save_dir, exist_ok=True)
        p = os.path.join(self.save_dir, fn.replace(".html",".pdf"))
        await self.page.pdf(path=p, format="A4", print_background=True, margin={"top":"10mm","bottom":"10mm","left":"10mm","right":"10mm"})

    async def save_text(self, fn):
        if not self.save_dir or not self.page: return
        os.makedirs(self.save_dir, exist_ok=True)
        try:
            text = await self.page.inner_text("body")
        except:
            text = await self.page.evaluate("document.body.innerText")
        with open(os.path.join(self.save_dir, fn.replace(".html",".txt")), "w", encoding="utf-8") as f:
            f.write(text or "")
    
    async def fetch_page(self, url, fn, w=5000):
        if not self.logged_in: return False
        try:
            await self.page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await self._delay(1000,2000)
            try: await self.page.wait_for_load_state("networkidle", timeout=15000)
            except: pass
            await asyncio.sleep(w/1000)
            await self.save_pdf(fn)
            await self.save_text(fn)
            return True
        except: return False
    
    async def get_jwgl_home(self):
        return await self.fetch_page("http://jwgl.cuit.edu.cn/eams/home.action","home.html",8000)

    async def get_jwgl_courses(self):
        if not await self.get_jwgl_home(): return False
        print("[Course] Navigating to course table...")
        await self.page.goto("http://jwgl.cuit.edu.cn/eams/courseTableForStd!courseTable.action", timeout=30000, wait_until="domcontentloaded")
        try:
            await self.page.wait_for_load_state("networkidle", timeout=30000)
        except:
            print("[Course] networkidle timeout")
        await self._delay(2000, 3000)
        for _ in range(20):
            table = await self.page.query_selector("table,.grid,.gridtable,.course-table")
            if table: break
            await asyncio.sleep(1)
        await self._delay(2000, 3000)
        table = await self.page.query_selector("table,.grid,.gridtable,.course-table")
        if table:
            rows = await table.query_selector_all("tr")
            rows_t = []
            for r in rows:
                cells = await r.query_selector_all("td,th")
                ct = [(await c.inner_text()).strip() for c in cells]
                rows_t.append(" | ".join(ct))
            text = "\n".join(rows_t)
        else:
            text = await self.page.inner_text("body")
        tp = os.path.join(self.save_dir, "course_table.txt")
        os.makedirs(self.save_dir, exist_ok=True)
        with open(tp, "w", encoding="utf-8") as f: f.write(text or "")
        print("[Course] Saved " + str(len(text or "")) + " chars")
        return True

    async def get_jwgl_scores(self, sid="906"):
        return await self.fetch_page("http://jwgl.cuit.edu.cn/eams/teach/grade/course/person!search.action?semesterId="+sid+"&projectType=", "scores_"+sid+".html")

    async def get_jwgl_exams(self, eid="5228", sn="大三下学期"):
        return await self.fetch_page("http://jwgl.cuit.edu.cn/eams/stdExamTable!examTable.action?examBatch.id="+eid, "exams_"+sn+"_"+eid+".html" if sn else "exams_"+eid+".html", 8000)

    async def get_jwgl_credits(self):
        return await self.fetch_page("http://jwgl.cuit.edu.cn/eams/myPlanCompl.action","credits.html",8000)

    async def get_all_student_data(self, username):
        for n,f in [("Course",self.get_jwgl_courses),("Scores",self.get_jwgl_scores),("Credits",self.get_jwgl_credits),("Exams",self.get_jwgl_exams)]:
            try: await f()
            except Exception as e: print("[Spider]", n, "failed:", e)
            await self._delay(2000,4000)
