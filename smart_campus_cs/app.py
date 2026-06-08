import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import re
from difflib import get_close_matches
from collections import defaultdict

st.set_page_config(page_title="吉利学院智能客服", page_icon="🤖", layout="wide")

st.title("🏫 吉利学院智能客服")
st.markdown("> **基于知识图谱 + 智能意图识别** | 数据源自吉利学院官方资料")

# ==================== 1. 数据层 ====================
# 课程
courses = {
    "高等数学": {"学分": 5, "教师": "王建国", "教室": "教学楼101", "先修": []},
    "线性代数": {"学分": 3, "教师": "李芳", "教室": "教学楼203", "先修": []},
    "离散数学": {"学分": 4, "教师": "张明", "教室": "计科楼302", "先修": ["高等数学"]},
    "数据结构": {"学分": 4, "教师": "陈丽", "教室": "计科楼401", "先修": ["离散数学"]},
    "数据库原理": {"学分": 3, "教师": "刘强", "教室": "计科楼405", "先修": ["数据结构"]},
    "机器学习": {"学分": 4, "教师": "孙颖", "教室": "AI楼101", "先修": ["线性代数", "高等数学"]},
}

# 设施
facilities = {
    "图书馆": {"开放时间": "8:00-22:00", "位置": "图书馆楼", "服务": "借书、自习"},
    "体育馆": {"开放时间": "9:00-21:00", "位置": "东区体育场", "项目": "篮球、羽毛球、游泳"},
    "第一食堂": {"开放时间": "6:30-20:00", "位置": "生活区", "特色": "麻辣烫、小笼包、奶茶"},
    "校医院": {"开放时间": "24小时", "位置": "北门旁", "电话": "87654321"},
}

# 政策
policies = {
    "奖学金": {"条件": "绩点≥3.5且无挂科", "金额": "一等5000元，二等3000元", "申请时间": "每年9月"},
    "转专业": {"条件": "第一学年成绩排名前30%", "流程": "提交申请→院系面试→学校审批", "时间": "第二学期第5周"},
    "助学金": {"条件": "家庭经济困难，成绩合格", "金额": "2000-4000元", "申请时间": "每年10月"},
}

# 校史（时间线）
history = {
    "1999年筹备": {"时间": "1999年", "事件": "吉利控股集团筹备创办北京吉利大学"},
    "2001年批准设立": {"时间": "2001年6月", "事件": "北京市教委批准设立北京吉利大学（专科）"},
    "2007年荣誉": {"时间": "2007年5月", "事件": "获'北京市民办教育特色项目试点学校'"},
    "2011年荣誉": {"时间": "2011年", "事件": "获'中国民办高等教育优秀院校'"},
    "2012年评估": {"时间": "2012年", "事件": "获评'5A级社会组织'"},
    "2014年升格本科": {"时间": "2014年4月", "事件": "升格为本科高校，更名为北京吉利学院"},
    "2018年学士学位授予权": {"时间": "2018年4月", "事件": "获批学士学位授予单位"},
    "2019年再获5A": {"时间": "2019年4月", "事件": "再次获评'5A级社会组织'"},
    "2020年迁址成都": {"时间": "2020年4月", "事件": "整体搬迁至成都市，更名为吉利学院"},
    "2020年开学": {"时间": "2020年9月", "事件": "成都校区举行首次开学典礼"},
    "2021年平安校园": {"时间": "2022年2月", "事件": "荣获石盘街道'平安建设工作先进单位'"},
}

# 优秀校友
famous_alumni = {
    "马承阳": {"职务": "中国气象局气象影视中心气象信息技术初级工程师"},
    "赵小龙": {"职务": "北京中海百信科技有限公司总经理"},
    "叶万芳": {"职务": "吉利控股集团企业社会责任高级经理"},
    "魏选": {"职务": "中央电视台综艺频道导演，央视《信中国》栏目导演，北京2022冬奥会、冬残奥会（张家口赛区）火炬传递活动总导演"},
    "梁岩": {"职务": "北京美像天真文化传媒有限公司创办人"},
    "张盛": {"职务": "北京博卉景观工程有限公司董事"},
}

# 荣誉（年份 -> 列表）
honors = {
    "2018年": ["品牌实力民办高校", "深受学生欢迎民办高校"],
    "2019年": ["中国民办高校领导品牌", "5A级社会组织", "北京市筹备和服务保障新中国成立70周年庆祝活动先进集体", "中国-东盟民办大学联盟轮值副主席单位"],
    "2020年": ["华人影响力民办高校", "实力标杆民办高校"],
    "2021年": ["四川高校平安校园建设先进单位", "校友会中国民办高校排名第17位", "最受考生青睐本科高校", "实力典范民办高校", "教育部'优秀工程勘察设计'规划设计一等奖", "四川省高校'平安校园'建设先进单位"],
    "2022年": ["四川普通高等学校招生工作先进集体", "校友会排名'中国一流应用型大学'", "全国社会责任贡献奖", "全国产教融合典范高校", "全国品牌影响力本科高校", "全国创新创业典范高校"],
    "2023年": ["获批四川省新增硕士学位授予立项建设单位", "机械工程获批'双一流'建设贡嘎计划培育学科", "省级重大教学改革项目立项", "工业互联网产业学院获批省级现代产业学院", "全国工商联人才交流服务中心产教融合示范实训基地", "校友会中国民办大学第10名", "中国产教融合百强院校", "新媒体传播创新本科高校"],
    "2024年": ["校友会中国民办大学I类院校第8名", "'智能车星路云协同感知与安全技术重点实验室'获批四川省高校重点实验室", "四川省'心理健康教育研究与实践基地'", "发明创业奖创新奖二等奖", "新媒体影响力本科高校"],
    "2025年": ["全国应用型标杆高校", "获批四川省首批'博士创新站'", "汽车创新设计产业学院获批省级现代产业学院", "车辆工程专业获批省级应用型品牌专业", "智能车星路云协同感知与安全技术实验室获批省级重点实验室", "鸿雁成长训练营获批国家级一流本科课程"],
}

# 行政管理（领导）
leaders = {
    "董事长": "李书福",
    "校长": "阙海宝",
    "党委书记、督导专员、副校长": "王培民",
    "党委副书记、副校长": "王桂琴",
    "副校长": ["王敏", "王桂琴", "刘召"],
    "校长助理": ["边保旗", "张泽明", "王茜"],
}

# 校区
campuses = {
    "北京校区": "位于北京市中关村国家创新示范区昌平园区，占地1300亩，总建筑面积45万平方米。2020年整体搬迁成都，原址改建为北京大学昌平校区。",
    "成都校区": "位于成都市简州新城龙泉湖畔，距成都市中心40公里，占地约2000亩，总规划建筑面积120万平方米。2020年9月1日招生开学。现有39个本科专业，设立智能制造学院、智能科技学院、商学院、金融科技学院、艺术设计学院等13个二级学院。",
}

# 校园文化
campus_culture = {
    "校徽": "圆形，主体图形由'吉'字构成，寓意吉祥圆满；'吉'字的'士'字寓意读书人、学者、大学士，造型似弓箭，寓意教育事业蓄势待发。1999年为创办元年。",
    "校训": "走进校园是为了更好地走向社会",
    "人才培养目标": "培养基础理论实、实践能力强、综合素质高，具有创新精神和国际视野的德智体美劳全面发展的应用型人才。",
    "发展目标": "建成高质量产教融合和数字化特色鲜明的高水平应用型大学。",
    "服务面向": "根植川渝，面向全国，辐射全球，服务行业与区域经济社会发展。",
    "使命": "为学生成长奠基，为教师发展铺路，为行业和区域发展提供高质量服务。",
    "愿景": "成为受人尊敬、学生热爱的吉利大学。",
}

# 社团（去重）
clubs_raw = {
    "文化艺术类": ["蜂鸟数字媒体技术工作室", "吉利幻月动漫社", "吉利鎏世手工社", "艺起美好非遗社", "造影影音社团", "有戏戏剧社", "艺术文创社", "嗨熊智慧文创工作室", "舞龙舞狮社团", "新闻社", "日语社", "云裳汉服社", "时光媒体收集社", "历史文学社", "乐夏音乐社", "民族文化社", "嘻哈社", "艺术绘画社", "吉他社", "图书社", "ACGN文化研究社", "吉利即说社", "挽雾配音社", "MH电影社", "摄影青年协会", "WZ流行摇滚乐队"],
    "志愿公益类": ["法律援助中心社团"],
    "创新创业类": ["e电商协会", "新象智创工作室"],
    "学术类": ["红蚁考研社团", "金融兴趣社", "英语翻译专业社团"],
    "体育类": ["跆拳道社团", "S.F.G街舞社", "武道社", "气排球社", "吉利羽毛球社", "足球协会", "健身协会", "排球社团", "吉利乒乓球社", "搏击社", "吉利CDG电竞社", "网球社", "OR滑板社", "体育舞蹈社", "健美操社"],
    "其他类": ["江海辩论社", "JL拓展社", "道客驴友社", "演讲辩论社", "裁判协会"],
}
# 去重（ACGN文化研究社出现在文化艺术类和其他类，保留第一个）
clubs = {}
for cat, members in clubs_raw.items():
    clubs[cat] = list(set(members))  # 类别内去重
# 跨类别去重（简单处理：遍历所有，记录已出现社团）
seen = set()
for cat in clubs:
    unique_members = []
    for m in clubs[cat]:
        if m not in seen:
            seen.add(m)
            unique_members.append(m)
    clubs[cat] = unique_members

# 构建实体词典（仅用于提取具体对象，不包含属性关键词）
entity_dict = {}
entity_dict.update({c: "课程" for c in courses})
entity_dict.update({f: "设施" for f in facilities})
entity_dict.update({a: "校友" for a in famous_alumni})
entity_dict.update({h: "校史事件" for h in history})
entity_dict.update({c: "校区" for c in campuses})
entity_dict.update({item: "文化" for item in campus_culture})
# 社团
for cat, members in clubs.items():
    for m in members:
        entity_dict[m] = "社团"
# 领导姓名
leader_names = set()
leader_names.add(leaders["董事长"])
leader_names.add(leaders["校长"])
leader_names.add(leaders["党委书记、督导专员、副校长"])
leader_names.add(leaders["党委副书记、副校长"])
leader_names.update(leaders["副校长"])
leader_names.update(leaders["校长助理"])
for ln in leader_names:
    entity_dict[ln] = "领导"
# 荣誉条目本身不作为实体，保留年份作为实体用于查询特定年份
for year in honors:
    entity_dict[year] = "荣誉年份"

# ==================== 2. 知识图谱构建 ====================
@st.cache_resource
def build_graph():
    G = nx.Graph()
    G.add_node("吉利学院", type="学校")
    
    # 课程相关
    for name in courses:
        G.add_node(name, type="课程")
        info = courses[name]
        teacher = info["教师"]
        room = info["教室"]
        G.add_node(teacher, type="教师")
        G.add_node(room, type="教室")
        G.add_edge(name, teacher, relation="讲授")
        G.add_edge(name, room, relation="在")
        for pre in info["先修"]:
            G.add_edge(pre, name, relation="先修")
    
    # 设施
    for name in facilities:
        G.add_node(name, type="设施")
        loc = facilities[name]["位置"]
        G.add_node(loc, type="位置")
        G.add_edge(name, loc, relation="位于")
    
    # 政策
    for name in policies:
        G.add_node(name, type="政策")
        G.add_edge("吉利学院", name, relation="政策")
    
    # 校史事件
    for event_name in history:
        G.add_node(event_name, type="校史")
        G.add_edge("吉利学院", event_name, relation="历史事件")
    
    # 校友
    for name in famous_alumni:
        G.add_node(name, type="校友")
        G.add_edge("吉利学院", name, relation="知名校友")
    
    # 荣誉：年份节点 + 每个荣誉条目节点
    for year, entries in honors.items():
        G.add_node(year, type="年份")
        G.add_edge("吉利学院", year, relation="荣誉年份")
        for entry in entries:
            node_name = f"{year}_{entry[:20]}"  # 避免过长，但保证唯一
            G.add_node(node_name, type="荣誉", full_name=entry, year=year)
            G.add_edge(year, node_name, relation="获得")
    
    # 领导
    for title, name in leaders.items():
        if isinstance(name, list):
            for n in name:
                G.add_node(n, type="领导")
                G.add_edge("吉利学院", n, relation=f"担任{title}")
        else:
            G.add_node(name, type="领导")
            G.add_edge("吉利学院", name, relation=f"担任{title}")
    
    # 校区
    for campus in campuses:
        G.add_node(campus, type="校区")
        G.add_edge("吉利学院", campus, relation="校区")
    
    # 文化
    for item in campus_culture:
        G.add_node(item, type="文化")
        G.add_edge("吉利学院", item, relation="文化")
    
    # 社团
    for cat, members in clubs.items():
        G.add_node(cat, type="社团类别")
        G.add_edge("吉利学院", cat, relation="社团类别")
        for club in members:
            G.add_node(club, type="社团")
            G.add_edge(cat, club, relation="包含")
    
    return G

G = build_graph()

# 缓存图布局
@st.cache_resource
def get_graph_layout():
    return nx.spring_layout(G, seed=42, k=1.8)

# ==================== 3. 自然语言理解模块 ====================
# 意图关键词（优先级从高到低排列）
intent_patterns = [
    ("course", ["课程", "学分", "老师", "教室", "先修", "选修", "必修"]),
    ("facility", ["图书馆", "食堂", "体育馆", "校医院", "开放时间", "几点开门", "位置在哪", "电话", "设施"]),
    ("policy", ["奖学金", "转专业", "助学金", "政策", "条件", "申请", "补助"]),
    ("history", ["历史", "校史", "创办", "升格", "迁址", "搬迁", "发展历程", "什么时候成立"]),
    ("alumni", ["校友", "知名", "毕业", "成就", "优秀校友", "杰出校友"]),
    ("honor", ["荣誉", "获奖", "排名", "称号", "奖项", "评估", "获得过什么"]),
    ("leader", ["校长", "书记", "董事长", "领导", "现任领导", "校领导", "谁是"]),
    ("campus", ["校区", "北京校区", "成都校区", "校园面积", "占地面积"]),
    ("culture", ["校训", "校徽", "使命", "愿景", "校风", "精神", "文化", "人才培养目标"]),
    ("club", ["社团", "协会", "俱乐部", "学生组织", "有哪些社团"]),
    ("greeting", ["你好", "您好", "hi", "hello", "在吗", "嗨"]),
]

def classify_intent(text):
    text_lower = text.lower()
    for intent, keywords in intent_patterns:
        if any(k in text_lower for k in keywords):
            return intent
    return "unknown"

def extract_entities(text, entity_dict):
    """仅提取实体词典中的具体实体，返回列表"""
    candidates = list(entity_dict.keys())
    found = []
    # 精确匹配
    for ent in candidates:
        if ent in text:
            found.append(ent)
    # 模糊匹配（只对长度>=2的中文）
    if not found:
        words = re.findall(r'[\u4e80-\u9fff]{2,}', text)
        for w in words:
            match = get_close_matches(w, candidates, n=1, cutoff=0.6)
            if match:
                found.append(match[0])
    # 去重并按长度降序（优先长实体）
    found = list(set(found))
    found.sort(key=lambda x: len(x), reverse=True)
    return found

# 辅助：根据领导姓名查职务
def get_leader_position(name, leaders):
    for title, val in leaders.items():
        if isinstance(val, list) and name in val:
            return title
        elif isinstance(val, str) and val == name:
            return title
    return "未知职务"

# 多轮对话的实体继承
def resolve_entities(current_entities, last_entities, text):
    """如果当前没有实体但上一轮有，且文本包含指代词（它、这个），则继承上一轮"""
    if not current_entities and last_entities:
        if any(word in text for word in ["它", "这个", "那个", "该"]):
            return last_entities
    return current_entities

# ==================== 4. 问答生成 ====================
def answer_question(intent, entities, original_text, last_entities):
    # 实体解析（继承）
    final_entities = resolve_entities(entities, last_entities, original_text)
    
    # 意图处理
    if intent == "greeting":
        return "您好！我是吉利学院智能客服，数据涵盖校史、校友、荣誉、领导、校区、文化、社团等。请问您想了解什么？"
    
    elif intent == "course":
        if not final_entities:
            return "吉利学院开设多门课程，例如高等数学、数据结构等。请具体说出课程名称。"
        for ent in final_entities:
            if ent in courses:
                info = courses[ent]
                prereq = "、".join(info["先修"]) if info["先修"] else "无"
                return f"📘 **吉利学院《{ent}》**\n- 学分：{info['学分']}\n- 教师：{info['教师']}\n- 教室：{info['教室']}\n- 先修：{prereq}"
        return "未找到该课程，可尝试“高等数学”、“数据结构”等。"
    
    elif intent == "facility":
        if not final_entities:
            # 如果文本中有“设施”但没有具体名称，返回列表
            if "设施" in original_text:
                return f"🏢 **吉利学院设施包括**：{', '.join(facilities.keys())}。您也可以具体询问某个设施，如“图书馆几点开门？”"
            return "请问您想了解吉利学院的哪个设施？例如“图书馆”、“体育馆”、“第一食堂”、“校医院”。"
        for ent in final_entities:
            if ent in facilities:
                info = facilities[ent]
                extra = info.get("电话", info.get("项目", info.get("特色", info.get("服务", ""))))
                return f"🏢 **吉利学院{ent}**\n- 开放时间：{info['开放时间']}\n- 位置：{info['位置']}\n- {extra}"
        return "未找到该设施，吉利学院设施有：图书馆、体育馆、第一食堂、校医院。"
    
    elif intent == "policy":
        if not final_entities:
            return "吉利学院的相关政策有：奖学金、转专业、助学金。您想了解哪一项？"
        for ent in final_entities:
            if ent in policies:
                info = policies[ent]
                return f"📜 **吉利学院{ent}**\n- 条件：{info['条件']}\n- {info.get('金额', info.get('流程', ''))}\n- 时间：{info.get('申请时间', info.get('时间', '请咨询教务处'))}"
        return "未找到该政策。"
    
    elif intent == "history":
        if not final_entities:
            timeline = "\n".join([f"- {v['时间']}：{v['事件']}" for v in history.values()])
            return f"📜 **吉利学院校史**\n{timeline}"
        text_lower = original_text.lower()
        if "创办" in text_lower:
            return "吉利学院的前身北京吉利大学于1999年筹备，2001年正式批准设立。"
        if "升格" in text_lower:
            return "2014年4月，教育部批准升格为本科高校，更名为北京吉利学院。"
        if "迁址" in text_lower or "搬迁" in text_lower:
            return "2020年4月，教育部批准整体搬迁至成都市，更名为吉利学院。"
        # 如果有具体事件实体
        for ent in final_entities:
            if ent in history:
                return f"📜 {history[ent]['时间']}：{history[ent]['事件']}"
        return "请具体询问，如“吉利学院创办时间”、“升格本科”、“迁址成都”等。"
    
    elif intent == "alumni":
        if not final_entities:
            names = "、".join(famous_alumni.keys())
            return f"🎓 **吉利学院知名校友**：{names}。想了解哪位校友的详细信息？"
        for ent in final_entities:
            if ent in famous_alumni:
                return f"🎓 **吉利学院校友{ent}**：{famous_alumni[ent]['职务']}"
        return "未找到该校友信息。"
    
    elif intent == "honor":
        if "荣誉" in original_text or "获奖" in original_text or "获得过什么" in original_text:
            summary = "\n".join([f"**{year}年**：{', '.join(lst[:3])}{'...' if len(lst)>3 else ''}" for year, lst in honors.items()])
            return f"🏆 **吉利学院主要荣誉**\n{summary}\n（更多详情可询问具体年份，如“2023年荣誉”）"
        # 检查是否有年份实体
        for ent in final_entities:
            if ent in honors:
                return f"🏆 **{ent}吉利学院荣誉**：{', '.join(honors[ent])}"
        return "您可以问“吉利学院获得过什么荣誉”或指定年份如“2023年荣誉”。"
    
    elif intent == "leader":
        # 优先使用提取出的领导姓名实体
        for ent in final_entities:
            if ent in leader_names:
                pos = get_leader_position(ent, leaders)
                return f"👤 {ent} 担任 {pos}。"
        # 否则根据职位关键词
        text_lower = original_text.lower()
        if "董事长" in text_lower:
            return f"👤 吉利学院董事长：{leaders['董事长']}"
        if "校长" in text_lower:
            return f"👤 吉利学院校长：{leaders['校长']}"
        if "书记" in text_lower:
            return f"👤 吉利学院党委书记、督导专员：{leaders['党委书记、督导专员、副校长']}"
        # 默认返回所有领导
        leader_str = f"董事长：{leaders['董事长']}；校长：{leaders['校长']}；党委书记：{leaders['党委书记、督导专员、副校长']}；党委副书记、副校长：{leaders['党委副书记、副校长']}；副校长：{', '.join(leaders['副校长'])}；校长助理：{', '.join(leaders['校长助理'])}"
        return f"👥 **吉利学院现任领导**\n{leader_str}"
    
    elif intent == "campus":
        text_lower = original_text.lower()
        if "北京校区" in text_lower:
            return f"🏛️ **北京校区**：{campuses['北京校区']}"
        if "成都校区" in text_lower:
            return f"🏛️ **成都校区**：{campuses['成都校区']}"
        if "面积" in text_lower:
            return f"北京校区占地1300亩，成都校区占地约2000亩。"
        return f"🏛️ **吉利学院校区**\n- 北京校区：{campuses['北京校区'][:80]}...\n- 成都校区：{campuses['成都校区'][:100]}..."
    
    elif intent == "culture":
        text_lower = original_text.lower()
        if "校训" in text_lower:
            return f"📖 **校训**：{campus_culture['校训']}"
        if "校徽" in text_lower:
            return f"🔵 **校徽**：{campus_culture['校徽']}"
        if "使命" in text_lower:
            return f"🎯 **使命**：{campus_culture['使命']}"
        if "愿景" in text_lower:
            return f"🌟 **愿景**：{campus_culture['愿景']}"
        if "人才培养" in text_lower:
            return f"🎓 **人才培养目标**：{campus_culture['人才培养目标']}"
        return f"✨ **吉利学院文化**\n- 校训：{campus_culture['校训']}\n- 使命：{campus_culture['使命']}\n- 愿景：{campus_culture['愿景']}\n- 发展目标：{campus_culture['发展目标']}"
    
    elif intent == "club":
        if not final_entities:
            cats = "、".join(clubs.keys())
            return f"🎉 **吉利学院社团分类**：{cats}。您可以问“文化艺术类社团有哪些”或具体社团名称。"
        # 检查是否为类别
        for cat in clubs:
            if cat in original_text:
                club_list = "、".join(clubs[cat][:10]) + ("..." if len(clubs[cat])>10 else "")
                return f"🎨 **{cat}**包括：{club_list}。"
        # 检查是否为具体社团
        for cat, lst in clubs.items():
            for club in lst:
                if club in original_text:
                    return f"🎭 **{club}** 属于{cat}，是吉利学院的学生社团。"
        return "未找到相关社团，您可以问“文化艺术类社团”或“体育类社团”。"
    
    else:
        return "抱歉，我无法理解。试试问“吉利学院校史”、“知名校友有哪些”、“获得过什么荣誉”、“校长是谁”、“成都校区”、“校训”、“社团有哪些”等。"

# ==================== 5. 图谱可视化（优化性能） ====================
def draw_subgraph(entities, G, full_layout, max_nodes=30):
    """绘制局部子图，限制节点数量"""
    if not entities:
        seeds = ["吉利学院", "高等数学", "图书馆", "校训"]
        nodes = set()
        for s in seeds:
            if s in G:
                nodes.add(s)
                nodes.update(nx.single_source_shortest_path_length(G, s, cutoff=1).keys())
        if len(nodes) > max_nodes:
            nodes = set(list(nodes)[:max_nodes])
        subG = G.subgraph(nodes).copy()
    else:
        nodes_to_keep = set(entities)
        for ent in entities:
            if ent in G:
                nodes_to_keep.update(nx.single_source_shortest_path_length(G, ent, cutoff=1).keys())
        if len(nodes_to_keep) > max_nodes:
            nodes_to_keep = set(list(nodes_to_keep)[:max_nodes])
        subG = G.subgraph(nodes_to_keep).copy()
    
    fig, ax = plt.subplots(figsize=(8, 6))
    if subG.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "无相关实体", ha='center', va='center')
        ax.axis('off')
        return fig
    
    # 使用缓存布局中的位置（仅保留子图中节点）
    pos = {node: full_layout[node] for node in subG.nodes if node in full_layout}
    # 如果某些节点不在缓存中，用spring_layout补充
    missing = [n for n in subG.nodes if n not in pos]
    if missing:
        sub_subG = G.subgraph(missing).copy()
        extra_pos = nx.spring_layout(sub_subG, seed=42, k=1.5)
        pos.update(extra_pos)
    
    node_colors = []
    for node in subG.nodes:
        if node in entities:
            node_colors.append("#ffb74d")
        elif node in courses: node_colors.append("#81c784")
        elif node in facilities: node_colors.append("#64b5f6")
        elif node in policies: node_colors.append("#e57373")
        elif node in history: node_colors.append("#f9a825")
        elif node in famous_alumni: node_colors.append("#ab47bc")
        elif node in honors: node_colors.append("#f06292")
        elif node in leader_names: node_colors.append("#ffa270")
        elif node in campuses: node_colors.append("#4fc3f7")
        elif node in campus_culture: node_colors.append("#26c6da")
        elif node in clubs or any(node in lst for lst in clubs.values()): node_colors.append("#aed581")
        elif node == "吉利学院": node_colors.append("#ff7043")
        else: node_colors.append("#bdbdbd")
    
    nx.draw_networkx_nodes(subG, pos, ax=ax, node_color=node_colors, node_size=600, alpha=0.9)
    labels = {node: node for node in subG.nodes}
    nx.draw_networkx_labels(subG, pos, labels, ax=ax, font_size=7,
                            bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=1))
    if subG.edges:
        nx.draw_networkx_edges(subG, pos, ax=ax, edge_color="gray", width=0.8, alpha=0.6, style="dashed")
    ax.set_title("吉利学院知识图谱（局部视图）", fontsize=12)
    ax.axis('off')
    plt.tight_layout()
    return fig

# ==================== 6. UI 会话管理 ====================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "您好！我是吉利学院智能客服，已整合校史、校友、荣誉、领导、校区、文化、社团等数据。请问您想了解什么？"}]
if "last_entities" not in st.session_state:
    st.session_state.last_entities = []
if "last_intent" not in st.session_state:
    st.session_state.last_intent = None

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("请输入您的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    intent = classify_intent(prompt)
    entities = extract_entities(prompt, entity_dict)
    # 多轮实体继承
    final_entities = resolve_entities(entities, st.session_state.last_entities, prompt)
    answer = answer_question(intent, final_entities, prompt, st.session_state.last_entities)
    
    # 存储本次结果供下一轮使用
    st.session_state.last_entities = final_entities
    st.session_state.last_intent = intent
    
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
        with st.expander("🔍 自然语言处理过程"):
            st.markdown(f"**意图识别**: {intent}")
            st.markdown(f"**提取实体**: {', '.join(final_entities) if final_entities else '无'}")
            st.markdown(f"**实体来源**: {'继承自上一轮' if final_entities and not entities else '当前问题提取'}")
            st.markdown("**推理依据**: 基于吉利学院知识图谱，回答中自动补全校名。")

# 侧边栏
with st.sidebar:
    st.header("🗺️ 知识图谱")
    # 获取缓存的完整布局
    full_layout = get_graph_layout()
    fig = draw_subgraph(st.session_state.last_entities, G, full_layout, max_nodes=25)
    st.pyplot(fig)
    st.caption("所有节点均属于吉利学院 | 子图限制25个节点")
    st.divider()
    
    st.subheader("📚 吉利学院知识库")
    with st.expander("🏫 校史"): 
        for k, v in history.items():
            st.write(f"- {v['时间']}：{v['事件']}")
    with st.expander("🎓 知名校友"):
        for name, info in famous_alumni.items():
            st.write(f"- {name}：{info['职务'][:30]}...")
    with st.expander("🏆 荣誉（近三年）"):
        for year in ["2023年", "2024年", "2025年"]:
            if year in honors:
                st.write(f"- {year}：{', '.join(honors[year][:2])}")
    with st.expander("👥 现任领导"):
        st.write(f"董事长：{leaders['董事长']}")
        st.write(f"校长：{leaders['校长']}")
    with st.expander("🏛️ 校区"):
        for name, desc in campuses.items():
            st.write(f"- {name}：{desc[:60]}...")
    with st.expander("✨ 校园文化"):
        st.write(f"校训：{campus_culture['校训']}")
        st.write(f"使命：{campus_culture['使命']}")
    with st.expander("🎉 社团统计"):
        for cat, lst in clubs.items():
            st.write(f"- {cat}：{len(lst)}个社团")
    
    st.divider()
    st.subheader("💡 示例问题")
    example_questions = [
        "高等数学的学分是多少？", "图书馆几点开门？", "奖学金申请条件？",
        "吉利学院创办时间？", "知名校友有哪些？", "2023年获得什么荣誉？",
        "校长是谁？", "成都校区面积多大？", "校训是什么？", "文化艺术类社团有哪些？"
    ]
    for q in example_questions:
        st.caption(f"• {q}")