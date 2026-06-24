"""
图书馆查询模块
"""
from typing import Optional
from datetime import datetime, timedelta


MOCK_BOOKS = [
    {"id": "b1", "title": "Python深度学习", "author": "Francois Chollet", "publisher": "人民邮电出版社", "isbn": "9787115471600",
     "cover": "\U0001f4d8", "status": "available", "copy_count": 3, "location": "TP312PY/102", "summary": "深度学习领域经典教材，从基础到实践全面讲解。"},
    {"id": "b2", "title": "算法导论（第3版）", "author": "Thomas H. Cormen", "publisher": "机械工业出版社", "isbn": "9787111407010",
     "cover": "\U0001f4d7", "status": "borrowed", "copy_count": 1, "location": "TP301.6/24", "summary": "计算机算法领域权威教材，涵盖排序、图算法等核心内容。"},
    {"id": "b3", "title": "计算机网络：自顶向下方法", "author": "James F. Kurose", "publisher": "机械工业出版社", "isbn": "9787111626213",
     "cover": "\U0001f4d5", "status": "available", "copy_count": 5, "location": "TP393/156", "summary": "计算机网络经典教材，自顶向下方法深入浅出。"},
    {"id": "b4", "title": "统计学习方法（第2版）", "author": "李航", "publisher": "清华大学出版社", "isbn": "9787302550389",
     "cover": "\U0001f4d9", "status": "available", "copy_count": 2, "location": "TP181/45", "summary": "统计学习方法权威教材，覆盖主要机器学习算法。"},
    {"id": "b5", "title": "深入理解计算机系统", "author": "Randal E. Bryant", "publisher": "机械工业出版社", "isbn": "9787111544937",
     "cover": "\U0001f4bb", "status": "available", "copy_count": 4, "location": "TP303/38", "summary": "计算机系统核心知识，从硬件到操作系统全面覆盖。"},
    {"id": "b6", "title": "机器学习（西瓜书）", "author": "周志华", "publisher": "清华大学出版社", "isbn": "9787302427711",
     "cover": "\U0001f349", "status": "available", "copy_count": 3, "location": "TP181/12", "summary": "国内机器学习领域经典入门教材。"},
    {"id": "b7", "title": "数据库系统概念", "author": "Abraham Silberschatz", "publisher": "机械工业出版社", "isbn": "9787111637530",
     "cover": "\U0001f4be", "status": "available", "copy_count": 2, "location": "TP311.13/67", "summary": "数据库权威教材，覆盖关系数据库、SQL、事务处理等。"},
    {"id": "b8", "title": "C++ Primer Plus（第6版）", "author": "Stephen Prata", "publisher": "人民邮电出版社", "isbn": "9787115366777",
     "cover": "\U0001f4da", "status": "borrowed", "copy_count": 1, "location": "TP312C/204", "summary": "C++编程经典入门教材，内容全面系统。"},
]


def search_books(keyword: str, page: int = 1, page_size: int = 20) -> dict:
    """搜索图书"""
    kw = keyword.lower()
    results = [b for b in MOCK_BOOKS 
               if kw in b["title"].lower() or kw in b["author"].lower() or kw in b.get("isbn", "").lower()]
    
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "success": True,
        "books": results[start:end],
        "total": total,
        "page": page,
        "has_more": end < total
    }


def get_book_detail(book_id: str) -> dict:
    """获取图书详情"""
    for b in MOCK_BOOKS:
        if b["id"] == book_id:
            return {"success": True, "book": b}
    return {"success": False, "message": "图书不存在"}


def get_borrowed_books(username: str) -> dict:
    """获取用户当前借阅（模拟数据）"""
    borrowed = [
        {"id": "bb1", "title": "Python深度学习", "borrow_date": "2026-05-20", "due_date": "2026-06-20", "is_overdue": True},
        {"id": "bb2", "title": "算法导论（第3版）", "borrow_date": "2026-06-01", "due_date": "2026-07-01", "is_overdue": False},
        {"id": "bb3", "title": "计算机网络：自顶向下方法", "borrow_date": "2026-06-10", "due_date": "2026-07-10", "is_overdue": False},
    ]
    return {"success": True, "books": borrowed, "total": len(borrowed)}


def get_borrow_history(username: str) -> dict:
    """获取用户借阅历史（模拟数据）"""
    history = [
        {"id": "bh1", "title": "数据结构与算法分析", "borrow_date": "2026-03-01", "return_date": "2026-04-15"},
        {"id": "bh2", "title": "操作系统概论", "borrow_date": "2026-02-10", "return_date": "2026-03-20"},
        {"id": "bh3", "title": "数据库系统概念", "borrow_date": "2025-12-05", "return_date": "2026-01-15"},
    ]
    return {"success": True, "books": history, "total": len(history)}


def get_hot_books(limit: int = 10) -> dict:
    """获取热门图书排行"""
    ranking = [
        {"id": "r1", "title": "人工智能：现代方法", "author": "Stuart Russell", "publisher": "清华大学出版社", "cover": "\U0001f916", "borrow_count": 156},
        {"id": "r2", "title": "Python编程：从入门到实践", "author": "Eric Matthes", "publisher": "人民邮电出版社", "cover": "\U0001f40d", "borrow_count": 142},
        {"id": "r3", "title": "深入理解计算机系统", "author": "Randal E. Bryant", "publisher": "机械工业出版社", "cover": "\U0001f4bb", "borrow_count": 128},
        {"id": "r4", "title": "机器学习（西瓜书）", "author": "周志华", "publisher": "清华大学出版社", "cover": "\U0001f349", "borrow_count": 115},
        {"id": "r5", "title": "C++ Primer Plus", "author": "Stephen Prata", "publisher": "人民邮电出版社", "cover": "\U0001f4da", "borrow_count": 98},
    ]
    return {"success": True, "books": ranking[:limit], "total": min(len(ranking), limit)}
