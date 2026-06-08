import streamlit as st
import re
from difflib import get_close_matches
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib

# 设置中文字体，防止乱码
try:
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'Arial Unicode MS']
    matplotlib.rcParams['axes.unicode_minus'] = False
except:
    pass

st.set_page_config(page_title="吉利学院智能客服", page_icon="🤖", layout="wide")

st.title("🏫 吉利学院智能客服")
st.markdown("> **基于自然语言处理 + 意图识别 + 知识图谱** | 数据源自吉利学院官方资料")

# ==================== 数据层 ====================
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
    "2014年升格本科": {"时间": "2014年4月", "事件": "升格为本科高校，更名为北京吉利学院"},
    "2020年迁址成都": {"时间": "2020年4月", "事件": "整体搬迁至成都市，更名为吉利学院"},
}

famous_alumni = {
    "马承阳": {"职务": "中国气象局气象影视中心气象信息技术初级工程师"},
    "魏选": {"职务": "中央电视台综艺频道导演"},
    "叶万芳": {"职务": "吉利控股集团企业社会责任高级经理"},
}

honors = {
    "2023年": ["获批四川省新增硕士学位授予立项建设单位", "校友会中国民办大学第10名"],
    "2024年": ["校友会中国民办大学I类院校第8名", "新媒体影响力本科高校"],
    "2025年": ["全国应用型标杆高校", "获批四川省首批'博士创新站'"],
}

leaders = {
    "董事长": "李书福",
    "校长": "阙海宝",
    "党委书记": "王培民",
    "副校长": ["王敏", "王桂琴"],
    "校长助理": ["边保旗", "张泽明"],
}

campuses = {
    "北京校区": "位于北京市昌平区...",
    "成都校区": "位于成都市简州新城..."
}

campus_culture = {
    "校训": "走进校园是为了更好地走向社会",
    "使命": "为学生成长奠基",
    "愿景": "成为受人尊敬、学生热爱的吉利大学",
}

clubs = {
    "文化艺术类": ["动漫社", "汉服社", "音乐社"],
    "体育类": ["篮球社", "羽毛球社", "电竞社"],
    "学术类": ["考研社", "英语社"],
}

# 实体词典（用于实体提取）
entity_dict = {}
entity_dict.update({c: "课程" for c in courses})
entity_dict.update({f: "设施" for f in facilities})
entity_dict.update({a: "校友" for a in famous_alumni})
entity_dict.update({h: "校史事件" for h in history})
entity_dict.update({c: "校区" for c in campuses})
entity_dict.update({item: "文化" for item in campus_culture})
for cat, members in clubs.items():
    for m in members:
        entity_dict[m] = "社团"
leader_names = set([leaders["董事长"], leaders["校长"], leaders["党委书记"]]) | set(leaders["副校长"]) | set(leaders["校长助理"])
for ln in leader_names:
    entity_dict[ln] = "领导"
for year in honors:
    entity_dict[year] = "荣誉年份"

# ==================== NLP 模块 ====================
intent_patterns = [
    ("course", ["课程", "学分", "老师"]),
    ("facility", ["图书馆", "食堂", "开放时间"]),
    ("policy", ["奖学金", "转专业"]),
    ("history", ["历史", "校史", "创办"]),
    ("alumni", ["校友"]),
    ("honor", ["荣誉", "获奖"]),
    ("leader", ["校长", "董事长"]),
    ("campus", ["校区"]),
    ("culture", ["校训", "使命"]),
    ("club", ["社团"]),
    ("greeting", ["你好", "您好"]),
]

def classify_intent(text):
    text_lower = text.lower()
    for intent, keywords in intent_patterns:
        if any(k in text_lower for k in keywords):
            return intent
    return "unknown"

def extract_entities(text, entity_dict):
    candidates = list(entity_dict.keys())
    found = []
    for ent in candidates:
        if ent in text:
            found.append(ent)
    if not found:
        words = re.findall(r'[\u4e80-\u9fff]{2,}', text)
        for w in words:
            match = get_close_matches(w, candidates, n=1, cutoff=0.6)
            if match:
                found.append(match[0])
    found = list(set(found))
    found.sort(key=lambda x: len(x), reverse=True)
    return found

def get_leader_position(name, leaders):
    for title, val in leaders.items():
        if isinstance(val, list) and name in val:
            return title
        elif isinstance(val, str) and val == name:
            return title
    return "未知职务"

def resolve_entities(current_entities, last_entities, text):
    if not current_entities and last_entities and any(w in text for w in ["它", "这个"]):
        return last_entities
    return current_entities

def answer_question(intent, entities, original_text, last_entities):
    final_entities = resolve_entities(entities, last_entities, original_text)
    
    if intent == "greeting":
        return "您好！我是吉利学院智能客服，请问您想了解什么？"
    elif intent == "course":
        if not final_entities:
            return "吉利学院开设高等数学、数据结构等课程。请具体说出课程名称。"
        for ent in final_entities:
            if ent in courses:
                info = courses[ent]
                prereq = "、".join(info["先修"]) if info["先修"] else "无"
                return f"📘 **{ent}**\n学分：{info['学分']}\n教师：{info['教师']}\n先修：{prereq}"
        return "未找到该课程。"
    elif intent == "facility":
        if not final_entities:
            return "吉利学院有图书馆、体育馆、第一食堂、校医院。请问您想了解哪个？"
        for ent in final_entities:
            if ent in facilities:
                info = facilities[ent]
                return f"🏢 **{ent}**\n开放时间：{info['开放时间']}\n位置：{info['位置']}"
        return "未找到该设施。"
    elif intent == "policy":
        if not final_entities:
            return "相关政策有：奖学金、转专业、助学金。"
        for ent in final_entities:
            if ent in policies:
                info = policies[ent]
                return f"📜 **{ent}**\n条件：{info['条件']}\n{info.get('金额', info.get('流程', ''))}"
        return "未找到该政策。"
    elif intent == "history":
        if "创办" in original_text:
            return "吉利学院前身北京吉利大学1999年筹备，2001年批准设立。"
        if "升格" in original_text:
            return "2014年升格为本科高校，更名为北京吉利学院。"
        if "迁址" in original_text:
            return "2020年整体搬迁至成都，更名为吉利学院。"
        return "请具体询问，如“创办时间”、“升格本科”、“迁址成都”。"
    elif intent == "alumni":
        if not final_entities:
            return f"知名校友：{', '.join(famous_alumni.keys())}"
        for ent in final_entities:
            if ent in famous_alumni:
                return f"🎓 {ent}：{famous_alumni[ent]['职务']}"
        return "未找到该校友。"
    elif intent == "honor":
        if "2023" in original_text:
            return f"2023年荣誉：{', '.join(honors['2023年'])}"
        if "2024" in original_text:
            return f"2024年荣誉：{', '.join(honors['2024年'])}"
        if "2025" in original_text:
            return f"2025年荣誉：{', '.join(honors['2025年'])}"
        return "近三年获得多项荣誉，如2023年硕士学位授予立项建设单位等。"
    elif intent == "leader":
        if "董事长" in original_text:
            return f"董事长：{leaders['董事长']}"
        if "校长" in original_text:
            return f"校长：{leaders['校长']}"
        return f"董事长：{leaders['董事长']}；校长：{leaders['校长']}"
    elif intent == "campus":
        if "北京" in original_text:
            return f"北京校区：{campuses['北京校区']}"
        if "成都" in original_text:
            return f"成都校区：{campuses['成都校区']}"
        return "吉利学院有北京校区（原址已改建）和成都校区（现主校区）。"
    elif intent == "culture":
        if "校训" in original_text:
            return f"校训：{campus_culture['校训']}"
        return f"校训：{campus_culture['校训']}；使命：{campus_culture['使命']}"
    elif intent == "club":
        if not final_entities:
            return "社团分为文化艺术类、体育类、学术类等。您想问哪一类？"
        for cat in clubs:
            if cat in original_text:
                return f"{cat}包括：{', '.join(clubs[cat])}"
        return "未找到相关社团。"
    else:
        return "请尝试询问课程、设施、政策、校史、校友、荣誉、领导、校区、文化或社团。"

# ==================== 知识图谱构建 ====================
@st.cache_resource
def build_knowledge_graph():
    """构建知识图谱（NetworkX有向图）并返回图形对象"""
    G = nx.DiGraph()
    
    # 1. 课程节点 + 先修关系 + 教师关系
    teachers_set = set()
    for course, info in courses.items():
        G.add_node(course, type="课程")
        teacher = info["教师"]
        teachers_set.add(teacher)
        # 教师-课程关系边
        G.add_node(teacher, type="教师")
        G.add_edge(teacher, course, relation="讲授")
        # 先修关系
        for prereq in info["先修"]:
            if prereq in courses:
                G.add_edge(prereq, course, relation="先修")
    
    # 2. 领导与职务关系
    for title, name in leaders.items():
        if isinstance(name, str):
            G.add_node(title, type="职务")
            G.add_node(name, type="领导")
            G.add_edge(name, title, relation="担任")
        elif isinstance(name, list):
            for n in name:
                G.add_node(title, type="职务")
                G.add_node(n, type="领导")
                G.add_edge(n, title, relation="担任")
    
    # 3. 社团关系：类别 -> 社团
    for category, members in clubs.items():
        cat_node = f"社团类别-{category}"
        G.add_node(cat_node, type="社团类别")
        for club in members:
            G.add_node(club, type="社团")
            G.add_edge(cat_node, club, relation="包含")
    
    # 4. 校友节点
    for alumni in famous_alumni.keys():
        G.add_node(alumni, type="校友")
    
    # 5. 添加一个“校训”文化节点（可选）
    G.add_node(campus_culture["校训"], type="文化")
    
    return G

def draw_knowledge_graph(G):
    """使用matplotlib绘制知识图谱，显示节点名称"""
    plt.figure(figsize=(14, 10))
    
    # 根据节点类型设置颜色
    color_map = []
    for node, data in G.nodes(data=True):
        typ = data.get("type", "")
        if typ == "课程":
            color_map.append("#4CAF50")   # 绿色
        elif typ == "教师":
            color_map.append("#2196F3")   # 蓝色
        elif typ == "领导":
            color_map.append("#FF9800")   # 橙色
        elif typ == "职务":
            color_map.append("#9C27B0")   # 紫色
        elif typ == "社团类别":
            color_map.append("#00BCD4")   # 青色
        elif typ == "社团":
            color_map.append("#FFC107")   # 琥珀色
        elif typ == "校友":
            color_map.append("#E91E63")   # 粉色
        elif typ == "文化":
            color_map.append("#795548")   # 棕色
        else:
            color_map.append("#AAAAAA")
    
    # 布局：使用 Kamada-Kawai 布局（更美观）
    pos = nx.kamada_kawai_layout(G)
    
    # 绘制节点
    nx.draw_networkx_nodes(G, pos, node_color=color_map, node_size=1600, alpha=0.9)
    # 绘制边（带箭头，有向图）
    nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True, arrowsize=15, arrowstyle="->", width=1.2)
    # 绘制标签（显示名字）
    nx.draw_networkx_labels(G, pos, font_size=9, font_family="sans-serif")
    
    # 绘制边标签（可选，显示关系类型）
    edge_labels = {(u, v): d["relation"] for u, v, d in G.edges(data=True) if "relation" in d}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7, font_color="darkblue")
    
    plt.title("吉利学院知识图谱（实体名称与关系）", fontsize=16)
    plt.axis("off")
    plt.tight_layout()
    return plt.gcf()

# ==================== 会话管理 ====================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "您好！我是吉利学院智能客服，请问您想了解什么？"}]
if "last_entities" not in st.session_state:
    st.session_state.last_entities = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("请输入您的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    intent = classify_intent(prompt)
    entities = extract_entities(prompt, entity_dict)
    final_entities = resolve_entities(entities, st.session_state.last_entities, prompt)
    answer = answer_question(intent, final_entities, prompt, st.session_state.last_entities)
    
    st.session_state.last_entities = final_entities
    
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
        with st.expander("🔍 自然语言处理过程"):
            st.markdown(f"**意图识别**: {intent}")
            st.markdown(f"**提取实体**: {', '.join(final_entities) if final_entities else '无'}")
            st.markdown(f"**实体来源**: {'继承自上一轮' if final_entities and not entities else '当前问题提取'}")

# ==================== 侧边栏（含知识图谱） ====================
with st.sidebar:
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
    with st.expander("🎉 社团分类"):
        for cat, lst in clubs.items():
            st.write(f"- {cat}：{len(lst)}个社团")
    
    st.divider()
    # 新增知识图谱展示区域
    st.subheader("🗺️ 知识图谱（显示名称）")
    with st.expander("📊 展开查看吉利学院知识图谱", expanded=False):
        st.markdown("节点显示实体名称，边表示关系（先修、讲授、担任、包含等）")
        G = build_knowledge_graph()
        fig = draw_knowledge_graph(G)
        st.pyplot(fig)
        st.caption("💡 提示：图中展示了课程、教师、领导、社团、校友等实体及其关联关系。")
    
    st.divider()
    st.subheader("💡 示例问题")
    example_questions = [
        "高等数学的学分是多少？", "图书馆几点开门？", "奖学金申请条件？",
        "吉利学院创办时间？", "知名校友有哪些？", "2023年获得什么荣誉？",
        "校长是谁？", "成都校区面积多大？", "校训是什么？", "文化艺术类社团有哪些？"
    ]
    for q in example_questions:
        st.caption(f"• {q}")