"""
校园导航数据与查询模块
"""
from typing import Optional


LOCATIONS = [
    {"id": "t1", "name": "第一教学楼", "address": "航空港校区·校园中心区", "icon": "\U0001f3eb", "hours": "6:30-22:00", "category": "teaching",
     "description": "主要教学楼，设有普通教室和多媒体教室，共5层。", "phone": "028-85966001", "tags": ["教室", "教学楼", "上课"]},
    {"id": "t2", "name": "第二教学楼", "address": "航空港校区·校园东区", "icon": "\U0001f3eb", "hours": "6:30-22:00", "category": "teaching",
     "description": "含阶梯教室和多媒体教室，共6层。", "phone": "028-85966002", "tags": ["教室", "教学楼", "上课"]},
    {"id": "t3", "name": "第三教学楼", "address": "航空港校区·校园西区", "icon": "\U0001f3eb", "hours": "6:30-22:00", "category": "teaching",
     "description": "配有智慧教室和研讨室，共5层。", "tags": ["教室", "教学楼", "上课"]},
    {"id": "t4", "name": "第四教学楼", "address": "航空港校区·校园北区", "icon": "\U0001f3eb", "hours": "6:30-22:00", "category": "teaching",
     "description": "含计算机机房和语音实验室，共6层。", "tags": ["机房", "教学楼", "实验室"]},
    {"id": "t5", "name": "信息楼", "address": "航空港校区·校园南区", "icon": "\U0001f3db\ufe0f", "hours": "7:00-21:30", "category": "teaching",
     "description": "信息工程学院办公及实验楼。", "tags": ["学院楼", "信息工程"]},
    {"id": "l1", "name": "第一食堂", "address": "航空港校区·生活区东侧", "icon": "\U0001f35c", "hours": "6:30-21:30", "category": "living",
     "description": "主营中餐，设有大众窗口和特色窗口。", "tags": ["食堂", "餐饮", "吃饭"]},
    {"id": "l2", "name": "第二食堂", "address": "航空港校区·生活区西侧", "icon": "\U0001f35b", "hours": "6:30-22:00", "category": "living",
     "description": "设有清真餐厅和民族风味窗口。", "tags": ["食堂", "餐饮", "清真"]},
    {"id": "l3", "name": "第三食堂", "address": "航空港校区·生活区北侧", "icon": "\U0001f95f", "hours": "7:00-21:00", "category": "living",
     "description": "以小吃和简餐为主，价格实惠。", "tags": ["食堂", "小吃"]},
    {"id": "l4", "name": "学生公寓1-10栋", "address": "航空港校区·生活区", "icon": "\U0001f3e0", "hours": "6:00-23:00", "category": "living",
     "description": "标准六人间宿舍，配备空调和热水。", "tags": ["宿舍", "住宿"]},
    {"id": "l5", "name": "学生公寓11-20栋", "address": "航空港校区·北区生活区", "icon": "\U0001f3e0", "hours": "6:00-23:00", "category": "living",
     "description": "标准四人间和六人间，配备独立卫浴。", "tags": ["宿舍", "住宿"]},
    {"id": "l6", "name": "校园超市", "address": "航空港校区·生活区中心", "icon": "\U0001f6d2", "hours": "7:30-22:30", "category": "living",
     "description": "提供日用百货、零食饮料等。", "tags": ["超市", "购物"]},
    {"id": "l7", "name": "校医院", "address": "航空港校区·校园东门", "icon": "\U0001f3e5", "hours": "24小时值班", "category": "living",
     "description": "提供基本医疗服务和急诊。", "phone": "028-85966020", "tags": ["医院", "医疗"]},
    {"id": "s1", "name": "图书馆", "address": "航空港校区·校园中心", "icon": "\U0001f4da", "hours": "7:30-22:00", "category": "study",
     "description": "馆藏丰富，设有自习区和电子阅览室，共6层。", "phone": "028-85966030", "tags": ["图书馆", "自习", "借书"]},
    {"id": "s2", "name": "自习室（一教）", "address": "第一教学楼2-4层", "icon": "\U0001f4d6", "hours": "6:30-22:00", "category": "study",
     "description": "空闲教室均可自习，可通过教务系统查询空闲教室。", "tags": ["自习", "学习"]},
    {"id": "s3", "name": "自习室（二教）", "address": "第二教学楼3-5层", "icon": "\U0001f4d6", "hours": "6:30-22:00", "category": "study",
     "description": "空闲教室均可自习。", "tags": ["自习", "学习"]},
    {"id": "s4", "name": "实验中心", "address": "航空港校区·校园南区", "icon": "\U0001f52c", "hours": "8:00-21:00", "category": "study",
     "description": "计算机实验室、物理实验室和工程实训中心。", "phone": "028-85966040", "tags": ["实验", "机房", "实训"]},
    {"id": "a1", "name": "行政楼", "address": "航空港校区·校园南门", "icon": "\U0001f3e2", "hours": "8:30-17:30（工作日）", "category": "admin",
     "description": "学校行政办公所在地。", "phone": "028-85966000", "tags": ["行政", "办公"]},
    {"id": "a2", "name": "学生事务中心", "address": "行政楼一楼", "icon": "\U0001f4cb", "hours": "8:30-17:30（工作日）", "category": "admin",
     "description": "办理学生证、成绩单、学籍证明等。", "phone": "028-85966111", "tags": ["事务", "学籍", "证明"]},
    {"id": "a3", "name": "就业指导中心", "address": "行政楼二楼", "icon": "\U0001f4bc", "hours": "8:30-17:30（工作日）", "category": "admin",
     "description": "提供就业指导、招聘信息等。", "phone": "028-85966222", "tags": ["就业", "招聘"]},
    {"id": "a4", "name": "信息技术中心", "address": "信息楼一楼", "icon": "\U0001f5a5\ufe0f", "hours": "8:30-17:30（工作日）", "category": "admin",
     "description": "处理校园网络、一卡通等事务。", "phone": "028-85966333", "tags": ["网络", "一卡通", "IT"]},
]

CATEGORY_MAP = {
    "teaching": "\U0001f3eb 教学区",
    "living": "\U0001f35c 生活区",
    "study": "\U0001f4da 学习区",
    "admin": "\U0001f3e2 行政办公",
}


def get_all_locations() -> dict:
    """获取所有地点"""
    return {"success": True, "locations": LOCATIONS, "total": len(LOCATIONS)}


def get_locations_by_category(category: str) -> dict:
    """按类别获取地点"""
    cat_name = CATEGORY_MAP.get(category, category)
    items = [loc for loc in LOCATIONS if loc.get("category") == category]
    return {"success": True, "category": cat_name, "locations": items, "total": len(items)}


def search_locations(keyword: str) -> dict:
    """搜索地点"""
    kw = keyword.lower()
    results = []
    for loc in LOCATIONS:
        if kw in loc["name"].lower() or kw in loc["address"].lower():
            results.append(loc)
            continue
        for tag in loc.get("tags", []):
            if kw in tag.lower():
                results.append(loc)
                break
    return {"success": True, "locations": results, "total": len(results)}


def get_location_detail(location_id: str) -> dict:
    """获取地点详情"""
    for loc in LOCATIONS:
        if loc["id"] == location_id:
            return {"success": True, "location": loc}
    return {"success": False, "message": "地点不存在"}
