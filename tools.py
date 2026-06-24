import os
import sys
from langchain.tools import tool
from typing import Optional, List, Dict

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '学生信息')


def get_student_dir(username: str) -> str:
   return os.path.join(DATA_DIR, username)


def load_pdf_paths(username: str) -> List[str]:
   student_dir = get_student_dir(username)
   paths = []
   if not os.path.exists(student_dir):
       return paths
   for filename in os.listdir(student_dir):
       if filename.endswith('.pdf'):
           paths.append(os.path.join(student_dir, filename))
   return sorted(paths, key=lambda x: os.path.basename(x))


@tool
def login_and_crawl(username: str, password: str) -> Dict[str, str]:
   """
   登录教务系统并爬取学生数据PDF

   Args:
       username: 学号
       password: 密码

   Returns:
       爬取结果信息，包含状态和消息
   """
   import spider
   spider_instance = spider.CuitSpider()
   spider_instance.username = username
   spider_instance.save_dir = get_student_dir(username)
   os.makedirs(spider_instance.save_dir, exist_ok=True)
   spider_instance.start_browser()
   try:
       if not spider_instance.login(username, password):
           return {"status": "failed", "message": "登录失败，请检查账号密码"}
       spider_instance.get_all_student_data(username)
       pdf_count = len(load_pdf_paths(username))
       return {
           "status": "success",
           "message": f"爬取完成，共获取 {pdf_count} 个PDF",
           "image_count": pdf_count
       }
   except Exception as e:
       return {"status": "failed", "message": f"爬取异常: {str(e)}"}
   finally:
       try:
           spider_instance.stop_browser()
       except Exception:
           pass


@tool
def check_local_data(username: str) -> Dict[str, str]:
   """
   检查本地是否已有学生数据PDF

   Args:
       username: 学号

   Returns:
       本地数据状态，包含PDF数量和是否就绪
   """
   pdf_paths = load_pdf_paths(username)
   return {
       "has_data": len(pdf_paths) > 0,
       "image_count": len(pdf_paths),
       "ready": len(pdf_paths) > 0,
       "message": f"本地已有 {len(pdf_paths)} 个PDF数据" if pdf_paths else "本地暂无PDF数据"
   }


@tool
def load_images_for_analysis(username: str) -> Dict[str, List[str]]:
   """
   加载学生的PDF数据用于AI分析

   Args:
       username: 学号

   Returns:
       PDF路径列表和数量
   """
   pdf_paths = load_pdf_paths(username)
   if not pdf_paths:
       return {"status": "failed", "message": "本地暂无PDF数据"}
   return {
       "status": "success",
       "image_paths": pdf_paths,
       "image_count": len(pdf_paths),
       "message": f"成功加载 {len(pdf_paths)} 个PDF"
   }
