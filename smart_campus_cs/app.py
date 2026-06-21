import streamlit as st
import networkx as nx
import re
from difflib import get_close_matches
from pyvis.network import Network
import tempfile
import os

st.set_page_config(page_title="吉利学院智能客服", page_icon="🤖", layout="wide")

st.title("🏫 吉利学院智能客服")
st.markdown("> **基于自然语言处理 + 知识图谱** | 数据源自吉利学院官方资料")

# ==================== 1. 知识图谱数据（定义在顶部，全局可用）====================
courses = {
    "高等数学": {"学分": 5, "教师": "王建国", "教室": "教学楼101", "先修": []},
    "线性代数": {"学分": 3, "教师": "李芳", "教室": "教学楼203", "先修": []},
    "离散数学": {"学分": 4, "教师": "张明", "教室": "计科楼302", "先修": ["高等数学"]},
    "数据结构": {"学分": 4, "教师": "陈丽", "教室": "计科楼401", "先修": ["离散数学"]},
    "数据库原理": {"学分": 3, "教师": "刘强", "教室": "计科楼405", "先修": ["数据结构"]},
    "机器学习": {"学分": 4, "教师": "孙颖", "教室": "AI楼101", "先修": ["线性代数", "高等数学"]},
}

facilities = {
    "图书馆": {"开放时间": "8:00-22:00", "位置": "图书馆楼", "服务": "借书、自习"},
    "体育馆": {"开放时间": "9:00-21:00", "位置": "东区体育场", "项目": "篮球、羽毛球、游泳"},
    "第一食堂": {"开放时间": "6:30-20:00", "位置": "生活区", "特色": "麻辣烫、小笼包、奶茶"},
    "校医院": {"开放时间": "24小时", "位置": "北门旁", "电话": "87654321"},
}

policies = {
    "奖学金": {"条件": "绩点≥3.5且无挂科", "金额": "一等5000元，二等3000元", "申请时间": "每年9月"},
    "转专业": {"条件": "第一学年成绩排名前30%", "流程": "提交申请→院系面试→学校审批", "时间": "第二学期第5周"},
    "助学金": {"条件": "家庭经济困难，成绩合格", "金额": "2000-4000元", "申请时间": "每年10月"},
}

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

famous_alumni = {
    "马承阳": {"职务": "中国气象局气象影视中心气象信息技术初级工程师"},
    "赵小龙": {"职务": "北京中海百信科技有限公司总经理"},
    "叶万芳": {"职务": "吉利控股集团企业社会责任高级经理"},
    "魏选": {"职务": "中央电视台综艺频道导演，央视《信中国》栏目导演，北京2022冬奥会、冬残奥会（张家口赛区）火炬传递活动总导演"},
    "梁岩": {"职务": "北京美像天真文化传媒有限公司创办人"},
    "张盛": {"职务": "北京博卉景观工程有限公司董事"},
}

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

leaders = {
    "董事长": "李书福",
    "校长": "阙海宝",
    "党委书记、督导专员、副校长": "王培民",
    "党委副书记、副校长": "王桂琴",
    "副校长": ["王敏", "王桂琴", "刘召"],
    "校长助理": ["边保旗", "张泽明", "王茜"],
}

campuses = {
    "北京校区": "位于北京市中关村国家创新示范区昌平园区，占地1300亩，总建筑面积45万平方米。2020年整体搬迁成都，原址改建为北京大学昌平校区。",
    "成都校区": "位于成都市简州新城龙泉湖畔，距成都市中心40公里，占地约2000亩，总规划建筑面积120万平方米。2020年9月1日招生开学。现有39个本科专业，设立智能制造学院、智能科技学院、商学院、金融科技学院、艺术设计学院等13个二级学院。",
}

campus_culture = {
    "校徽": "圆形，主体图形由'吉'字构成，寓意吉祥圆满；'吉'字的'士'字寓意读书人、学者、大学士，造型似弓箭，寓意教育事业蓄势待发。1999年为创办元年。",
    "校训": "走进校园是为了更好地走向社会",
    "人才培养目标": "培养基础理论实、实践能力强、综合素质高，具有创新精神和国际视野的德智体美劳全面发展的应用型人才。",
    "发展目标": "建成高质量产教融合和数字化特色鲜明的高水平应用型大学。",
    "服务面向": "根植川渝，面向全国，辐射全球，服务行业与区域经济社会发展。",
    "使命": "为学生成长奠基，为教师发展铺路，为行业和区域发展提供高质量服务。",
    "愿景": "成为受人尊敬、学生热爱的吉利大学。",
}

clubs = {
    "文化艺术类": ["蜂鸟数字媒体技术工作室", "吉利幻月动漫社", "吉利鎏世手工社", "艺起美好非遗社", "造影影音社团", "有戏戏剧社", "艺术文创社", "嗨熊智慧文创工作室", "舞龙舞狮社团", "新闻社", "日语社", "云裳汉服社", "时光媒体收集社", "历史文学社", "乐夏音乐社", "民族文化社", "嘻哈社", "艺术绘画社", "吉他社", "图书社", "ACGN文化研究社", "吉利即说社", "挽雾配音社", "MH电影社", "摄影青年协会", "WZ流行摇滚乐队"],
    "志愿公益类": ["法律援助中心社团"],
    "创新创业类": ["e电商协会", "新象智创工作室"],
    "学术类": ["红蚁考研社团", "金融兴趣社", "英语翻译专业社团"],
    "体育类": ["跆拳道社团", "S.F.G街舞社", "武道社", "气排球社", "吉利羽毛球社", "足球协会", "健身协会", "排球社团", "吉利乒乓球社", "搏击社", "吉利CDG电竞社", "网球社", "OR滑板社", "体育舞蹈社", "健美操社"],
    "其他类": ["江海辩论社", "JL拓展社", "ACGN文化研究社", "道客驴友社", "演讲辩论社", "裁判协会"],
}

# ==================== 2. 构建知识图谱 ====================
@st.cache_resource
def build_graph():
    G = nx.Graph()
    G.add_node("吉利学院", type="学校")
    
    for name in courses: G.add_node(name, type="课程")
    for name in facilities: G.add_node(name, type="设施")
    for name in policies: G.add_node(name, type="政策")
    for name in history: G.add_node(name, type="校史")
    for name in famous_alumni: G.add_node(name, type="校友")
    for name in honors: G.add_node(name, type="荣誉年份")
    for name in leaders:
        if isinstance(leaders[name], list):
            for sub in leaders[name]:
                G.add_node(sub, type="领导")
        else:
            G.add_node(leaders[name], type="领导")
    for name in campuses: G.add_node(name, type="校区")
    for name in campus_culture: G.add_node(name, type="文化")
    for cat, club_list in clubs.items():
        G.add_node(cat, type="社团类别")
        for club in club_list:
            G.add_node(club, type="社团")
            G.add_edge(cat, club, relation="包含")
    
    for course, info in courses.items():
        teacher = info["教师"]
        G.add_node(teacher, type="教师")
        G.add_edge(course, teacher, relation="讲授")
        room = info["教室"]
        G.add_node(room, type="教室")
        G.add_edge(course, room, relation="在")
        for pre in info["先修"]:
            G.add_edge(pre, course, relation="先修")
    for fac, info in facilities.items():
        loc = info["位置"]
        G.add_node(loc, type="位置")
        G.add_edge(fac, loc, relation="位于")
    for event in history:
        G.add_edge("吉利学院", event, relation="历史事件")
    for alumni in famous_alumni:
        G.add_edge("吉利学院", alumni, relation="知名校友")
    for year in honors:
        G.add_edge("吉利学院", year, relation="荣誉年份")
    for leader_name in [leaders["董事长"], leaders["校长"], leaders["党委书记、督导专员、副校长"], leaders["党委副书记、副校长"]]:
        G.add_edge("吉利学院", leader_name, relation="领导")
    for campus in campuses:
        G.add_edge("吉利学院", campus, relation="校区")
    for culture in campus_culture:
        G.add_edge("吉利学院", culture, relation="文化")
    for cat in clubs:
        G.add_edge("吉利学院", cat, relation="社团类别")
    
    return G

G = build_graph()

# ==================== 3. NLP 意图识别 ====================
intent_keywords = {
    "greeting": ["你好", "您好", "hi", "hello", "在吗"],
    "course": ["课程", "学分", "老师", "教室", "先修"],
    "facility": ["图书馆", "食堂", "体育馆", "校医院", "开放时间", "在哪", "几点", "电话", "设施"],
    "policy": ["奖学金", "转专业", "助学金", "政策", "条件", "申请"],
    "history": ["历史", "校史", "创办", "升格", "迁址", "搬迁", "发展历程"],
    "alumni": ["校友", "知名", "毕业", "成就", "优秀校友"],
    "honor": ["荣誉", "获奖", "排名", "称号", "奖项", "评估"],
    "leader": ["校长", "书记", "董事长", "领导", "现任领导", "校领导"],
    "campus": ["校区", "北京校区", "成都校区", "校园", "占地面积"],
    "culture": ["校训", "校徽", "使命", "愿景", "校风", "精神", "文化"],
    "club": ["社团", "协会", "俱乐部", "学生组织"],
}

def classify_intent(text):
    text_lower = text.lower()
    for intent, words in intent_keywords.items():
        if any(w in text_lower for w in words):
            return intent
    return "unknown"

def extract_entities(text, entity_dict):
    candidates = list(entity_dict.keys())
    found = []
    for ent in candidates:
        if ent in text:
            found.append(ent)
    if not found:
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        for w in words:
            match = get_close_matches(w, candidates, n=1, cutoff=0.6)
            if match:
                found.append(match[0])
    return list(set(found))

def answer_question(intent, entities, original_text):
    if intent == "course":
        if not entities:
            return "吉利学院开设多门课程，例如高等数学、数据结构等。请具体说出课程名称。"
        for ent in entities:
            if ent in courses:
                info = courses[ent]
                prereq = "、".join(info["先修"]) if info["先修"] else "无"
                return f"📘 **吉利学院《{ent}》**\n- 学分：{info['学分']}\n- 教师：{info['教师']}\n- 教室：{info['教室']}\n- 先修：{prereq}"
        return "未找到该课程，可尝试“高等数学”、“数据结构”等。"
    
    if intent == "facility":
        if not entities:
            if "设施" in original_text:
                return f"🏢 **吉利学院设施包括**：{', '.join(facilities.keys())}。您也可以具体询问某个设施。"
            return "请问您想了解吉利学院的哪个设施？例如“图书馆几点开门？”"
        for ent in entities:
            if ent in facilities:
                info = facilities[ent]
                extra = info.get("电话", info.get("项目", info.get("特色", info.get("服务", ""))))
                return f"🏢 **吉利学院{ent}**\n- 开放时间：{info['开放时间']}\n- 位置：{info['位置']}\n- {extra}"
        return "未找到该设施，吉利学院设施有：图书馆、体育馆、第一食堂、校医院。"
    
    if intent == "policy":
        if not entities:
            return "吉利学院的相关政策有：奖学金、转专业、助学金。您想了解哪一项？"
        for ent in entities:
            if ent in policies:
                info = policies[ent]
                return f"📜 **吉利学院{ent}**\n- 条件：{info['条件']}\n- {info.get('金额', info.get('流程', ''))}\n- 时间：{info.get('申请时间', info.get('时间', '请咨询教务处'))}"
        return "未找到该政策。"
    
    if intent == "history":
        if not entities:
            timeline = "\n".join([f"- {v['时间']}：{v['事件']}" for v in history.values()])
            return f"📜 **吉利学院校史**\n{timeline}"
        text_lower = original_text.lower()
        if "创办" in text_lower:
            return "吉利学院的前身北京吉利大学于1999年筹备，2001年正式批准设立。"
        if "升格" in text_lower:
            return "2014年4月，教育部批准升格为本科高校，更名为北京吉利学院。"
        if "迁址" in text_lower or "搬迁" in text_lower:
            return "2020年4月，教育部批准整体搬迁至成都市，更名为吉利学院。"
        return "请具体询问，如“吉利学院创办时间”、“升格本科”、“迁址成都”等。"
    
    if intent == "alumni":
        if not entities:
            names = "、".join(famous_alumni.keys())
            return f"🎓 **吉利学院知名校友**：{names}。想了解哪位校友的详细信息？"
        for name in entities:
            if name in famous_alumni:
                info = famous_alumni[name]
                return f"🎓 **吉利学院校友{name}**：{info['职务']}"
        if "有哪些" in original_text:
            return f"🎓 吉利学院知名校友包括：{', '.join(famous_alumni.keys())}。"
        return "未找到该校友信息。"
    
    if intent == "honor":
        if "荣誉" in original_text or "获奖" in original_text:
            summary = "\n".join([f"**{year}年**：{', '.join(lst)}" for year, lst in honors.items()])
            return f"🏆 **吉利学院主要荣誉**\n{summary}"
        for ent in entities:
            if ent in honors:
                return f"🏆 **{ent}年吉利学院荣誉**：{', '.join(honors[ent])}"
        return "您可以问“吉利学院获得过什么荣誉”或指定年份如“2023年荣誉”。"
    
    if intent == "leader":
        if "董事长" in original_text:
            return f"👤 吉利学院董事长：{leaders['董事长']}"
        if "校长" in original_text:
            return f"👤 吉利学院校长：{leaders['校长']}"
        if "书记" in original_text:
            return f"👤 吉利学院党委书记、督导专员：{leaders['党委书记、督导专员、副校长']}"
        leader_str = f"董事长：{leaders['董事长']}；校长：{leaders['校长']}；党委书记：{leaders['党委书记、督导专员、副校长']}；党委副书记、副校长：{leaders['党委副书记、副校长']}；副校长：{', '.join(leaders['副校长'])}；校长助理：{', '.join(leaders['校长助理'])}"
        return f"👥 **吉利学院现任领导**\n{leader_str}"
    
    if intent == "campus":
        if "北京校区" in original_text:
            return f"🏛️ **北京校区**：{campuses['北京校区']}"
        if "成都校区" in original_text:
            return f"🏛️ **成都校区**：{campuses['成都校区']}"
        return f"🏛️ **吉利学院校区**\n- 北京校区：{campuses['北京校区'][:80]}...\n- 成都校区：{campuses['成都校区'][:100]}..."
    
    if intent == "culture":
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
    
    if intent == "club":
        if not entities:
            cats = "、".join(clubs.keys())
            return f"🎉 **吉利学院社团分类**：{cats}。您可以问“文化艺术类社团有哪些”或具体社团。"
        for cat in clubs:
            if cat in original_text:
                club_list = "、".join(clubs[cat])
                return f"🎨 **{cat}**包括：{club_list}。"
        for cat, lst in clubs.items():
            for club in lst:
                if club in original_text:
                    return f"🎭 **{club}** 属于{cat}，是吉利学院的学生社团。"
        return "未找到相关社团，您可以问“文化艺术类社团”或“体育类社团”。"
    
    if intent == "greeting":
        return "您好！我是吉利学院智能客服，数据涵盖校史、校友、荣誉、领导、校区、文化、社团等。请问您想了解什么？"
    
    return "抱歉，我无法理解。试试问“吉利学院校史”、“知名校友有哪些”、“获得过什么荣誉”、“校长是谁”、“成都校区”、“校训”、“社团有哪些”等。"

# ==================== 4. 使用 pyvis 生成交互式图谱 ====================
def build_pyvis_html(G, highlight_nodes=None, height="600px", width="100%"):
    net = Network(height=height, width=width, bgcolor="#ffffff", font_color="black")
    net.set_options("""
    var options = {
      "physics": {
        "enabled": true,
        "stabilization": {"iterations": 100},
        "barnesHut": {"gravitationalConstant": -8000, "centralGravity": 0.3}
      }
    }
    """)

    if highlight_nodes:
        nodes_to_keep = set(highlight_nodes)
        for node in highlight_nodes:
            if node in G:
                nodes_to_keep.update(nx.single_source_shortest_path_length(G, node, cutoff=1).keys())
        subG = G.subgraph(nodes_to_keep).copy()
    else:
        subG = G
        if subG.number_of_nodes() > 200:
            core = set()
            if "吉利学院" in G:
                core.add("吉利学院")
                core.update(nx.single_source_shortest_path_length(G, "吉利学院", cutoff=2).keys())
            subG = G.subgraph(core).copy()

    color_map = {
        "学校": "#ff7043",
        "课程": "#81c784",
        "设施": "#64b5f6",
        "政策": "#e57373",
        "校史": "#f9a825",
        "校友": "#ab47bc",
        "荣誉年份": "#f06292",
        "领导": "#ffa270",
        "校区": "#4fc3f7",
        "文化": "#26c6da",
        "社团类别": "#aed581",
        "社团": "#aed581",
        "教师": "#ffb74d",
        "教室": "#90a4ae",
        "位置": "#78909c",
        "其他": "#bdbdbd",
    }

    for node in subG.nodes:
        node_type = G.nodes[node].get('type', '其他')
        color = color_map.get(node_type, "#bdbdbd")
        border_color = "red" if highlight_nodes and node in highlight_nodes else color
        title = f"{node}\n类型: {node_type}"
        net.add_node(node, label=node, color=color, borderWidth=2,
                     title=title, font={"size": 14}, shape="dot", size=20)

    for u, v in subG.edges:
        relation = G[u][v].get('relation', '')
        net.add_edge(u, v, title=relation, width=1)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        net.save_graph(f.name)
        return f.name

# ==================== 5. 会话状态初始化 ====================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "您好！我是吉利学院智能客服，已整合校史、校友、荣誉、领导、校区、文化、社团等数据。请问您想了解什么？"}]
if "last_entities" not in st.session_state:
    st.session_state.last_entities = []

# ==================== 6. 界面布局（Tabs） ====================
tab1, tab2 = st.tabs(["💬 智能客服", "🗺️ 知识图谱探索"])

# ---------- Tab1: 聊天 ----------
with tab1:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("请输入您的问题..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        intent = classify_intent(prompt)
        all_entities = {**courses, **facilities, **policies, **history, **famous_alumni, **honors,
                        "吉利学院": None, **leaders, **campuses, **campus_culture}
        for clist in clubs.values():
            for c in clist:
                all_entities[c] = None
        entities = extract_entities(prompt, all_entities)
        st.session_state.last_entities = entities
        answer = answer_question(intent, entities, prompt)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
            with st.expander("🔍 自然语言处理过程"):
                st.markdown(f"**意图识别**: {intent}")
                st.markdown(f"**提取实体**: {', '.join(entities) if entities else '无'}")
                st.markdown("**推理依据**: 基于吉利学院知识图谱，回答中自动补全校名。")

    # 侧边栏
    with st.sidebar:
        st.header("🗺️ 知识图谱（局部）")
        highlight = st.session_state.last_entities if st.session_state.last_entities else ["吉利学院"]
        html_path = build_pyvis_html(G, highlight_nodes=highlight, height="350px")
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=380)
        os.unlink(html_path)
        st.caption("🖱️ 可拖拽、缩放 | 红色边框为查询实体")

        st.divider()
        st.subheader("📚 吉利学院知识库")
        with st.expander("🏫 校史"):
            for k, v in history.items():
                st.write(f"- {v['时间']}：{v['事件']}")
        with st.expander("🎓 知名校友"):
            for name, info in famous_alumni.items():
                st.write(f"- {name}：{info['职务'][:30]}...")
        with st.expander("🏆 荣誉（部分）"):
            for year, lst in list(honors.items())[-3:]:
                st.write(f"- {year}：{', '.join(lst[:2])}")
        with st.expander("👥 现任领导"):
            st.write(f"董事长：{leaders['董事长']}")
            st.write(f"校长：{leaders['校长']}")
        with st.expander("🏛️ 校区"):
            for name, desc in campuses.items():
                st.write(f"- {name}：{desc[:60]}...")
        with st.expander("✨ 校园文化"):
            st.write(f"校训：{campus_culture['校训']}")
            st.write(f"使命：{campus_culture['使命']}")
        with st.expander("🎉 社团分类"):
            for cat, lst in clubs.items():
                st.write(f"- {cat}：{len(lst)}个社团")

# ---------- Tab2: 图谱探索 ----------
with tab2:
    st.subheader("🔍 全局知识图谱探索")
    col1, col2 = st.columns([3, 1])
    with col2:
        search_term = st.text_input("搜索节点", placeholder="输入课程/校友/设施名...")
    with col1:
        st.write("下方图谱可拖拽、滚轮缩放，节点悬停显示详细信息。")

    if search_term:
        all_nodes = list(G.nodes)
        matches = get_close_matches(search_term, all_nodes, n=5, cutoff=0.6)
        highlight_nodes = matches if matches else [search_term] if search_term in G else None
    else:
        highlight_nodes = None

    html_path = build_pyvis_html(G, highlight_nodes=highlight_nodes, height="700px")
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    st.components.v1.html(html_content, height=750)
    os.unlink(html_path)
    st.caption("💡 提示：输入节点名称可高亮显示该节点及其直接关联邻居（红色边框）。")