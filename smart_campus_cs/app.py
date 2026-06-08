import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import re
from difflib import get_close_matches

st.set_page_config(page_title="智能校园客服-吉利学院", page_icon="🤖", layout="wide")

st.title("🤖 智能校园客服 · 吉利学院专版")
st.markdown("> **自然语言处理（NLP）驱动** | 意图识别 + 实体提取 + 知识图谱推理")

# -------------------- 知识图谱数据（含学校特色）--------------------
courses = {
    "高等数学": {"学分": 5, "教师": "王建国", "教室": "教学楼101", "先修": []},
    "线性代数": {"学分": 3, "教师": "李芳", "教室": "教学楼203", "先修": []},
    "离散数学": {"学分": 4, "教师": "张明", "教室": "计科楼302", "先修": ["高等数学"]},
    "数据结构": {"学分": 4, "教师": "陈丽", "教室": "计科楼401", "先修": ["离散数学"]},
    "数据库原理": {"学分": 3, "教师": "刘强", "教室": "计科楼405", "先修": ["数据结构"]},
    "机器学习": {"学分": 4, "教师": "孙颖", "教室": "AI楼101", "先修": ["线性代数", "高等数学"]},
}
facilities = {
    "图书馆": {"开放时间": "8:00-22:00", "位置": "图书馆楼", "电话": "12345678", "服务": "借书、自习"},
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
    "吉利学院创办": {"时间": "1999年", "事件": "吉利集团投资创办，初名北京吉利大学"},
    "升格本科": {"时间": "2014年", "事件": "经教育部批准升格为本科高校，更名为北京吉利学院"},
    "迁址成都": {"时间": "2020年", "事件": "整体搬迁至成都市，更名为吉利学院"},
    "获批硕士点": {"时间": "2023年", "事件": "获批硕士学位授予单位，开启研究生教育"},
}
famous_alumni = {
    "张强": {"毕业年份": "2010年", "专业": "计算机科学与技术", "成就": "创办科技公司，获亿元融资"},
    "李丽": {"毕业年份": "2012年", "专业": "艺术设计", "成就": "知名插画师，作品多次获国际大奖"},
    "王磊": {"毕业年份": "2015年", "专业": "车辆工程", "成就": "吉利汽车研究院高级工程师"},
    "陈芳": {"毕业年份": "2018年", "专业": "工商管理", "成就": "入选福布斯30岁以下精英榜"},
}
# 新增：吉利学院特色
features = {
    "校训": "走进校园是为了更好地走向社会",
    "办学理念": "以质量求生存，以特色求发展，以服务求支持",
    "优势学科": ["车辆工程", "计算机科学与技术", "工商管理", "艺术设计"],
    "产教融合": "与吉利集团、领克、极氪等企业共建产业学院，实施“双元制”人才培养",
    "校园文化": "吉利大讲堂、创新创业大赛、汽车文化节",
    "国际合作": "与英国、马来西亚等多所高校开展交换生项目",
    "办学定位": "建设具有国际影响的高水平应用型大学",
}

# 构建知识图谱（含特色节点）
@st.cache_resource
def build_graph():
    G = nx.Graph()
    G.add_node("吉利学院", type="学校")
    
    for name in courses: G.add_node(name, type="课程")
    for name in facilities: G.add_node(name, type="设施")
    for name in policies: G.add_node(name, type="政策")
    for name in history: G.add_node(name, type="校史")
    for name in famous_alumni: G.add_node(name, type="校友")
    for name in features: G.add_node(name, type="特色")
    
    # 课程关系
    for course, info in courses.items():
        teacher = info["教师"]; G.add_node(teacher, type="教师")
        G.add_edge(course, teacher, relation="讲授")
        room = info["教室"]; G.add_node(room, type="教室")
        G.add_edge(course, room, relation="在")
        for pre in info["先修"]: G.add_edge(pre, course, relation="先修")
    # 设施位置
    for fac, info in facilities.items():
        loc = info["位置"]; G.add_node(loc, type="位置")
        G.add_edge(fac, loc, relation="位于")
    # 校史、校友、特色均与学校相连
    for event in history: G.add_edge("吉利学院", event, relation="历史事件")
    for alumni in famous_alumni: G.add_edge("吉利学院", alumni, relation="知名校友")
    for ft in features: G.add_edge("吉利学院", ft, relation="特色")
    return G

G = build_graph()

# -------------------- NLP 模块 --------------------
intent_keywords = {
    "greeting": ["你好", "您好", "hi", "hello", "在吗"],
    "course": ["课程", "学分", "老师", "教室", "先修"],
    "facility": ["图书馆", "食堂", "体育馆", "校医院", "开放时间", "在哪", "几点", "电话"],
    "policy": ["奖学金", "转专业", "助学金", "政策", "条件", "申请"],
    "history": ["历史", "创办", "升格", "迁址", "校史"],
    "alumni": ["校友", "知名", "毕业", "成就"],
    "feature": ["特色", "校训", "理念", "优势专业", "产教融合", "校园文化", "国际合作", "办学定位"],
}

def classify_intent(text):
    """基于关键词匹配的意图识别"""
    text_lower = text.lower()
    for intent, words in intent_keywords.items():
        if any(w in text_lower for w in words):
            return intent
    return "unknown"

def extract_entities(text, entity_dict):
    """提取文本中的实体（精确匹配 + 模糊匹配）"""
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
    """根据意图和实体生成回答，并展示自然语言处理中间结果"""
    # 先处理特色类（直接匹配关键词，因为 features 是字典非实体列表）
    if intent == "feature":
        text_lower = original_text.lower()
        if "校训" in text_lower:
            return f"📖 **校训**：{features['校训']}"
        if "理念" in text_lower:
            return f"💡 **办学理念**：{features['办学理念']}"
        if "优势专业" in text_lower or "优势学科" in text_lower:
            return f"🏆 **优势学科**：{', '.join(features['优势学科'])}"
        if "产教融合" in text_lower:
            return f"🔧 **产教融合**：{features['产教融合']}"
        if "校园文化" in text_lower:
            return f"🎉 **校园文化**：{features['校园文化']}"
        if "国际合作" in text_lower:
            return f"🌍 **国际合作**：{features['国际合作']}"
        if "办学定位" in text_lower:
            return f"🎯 **办学定位**：{features['办学定位']}"
        # 默认返回所有特色
        return f"✨ **吉利学院特色**\n- 校训：{features['校训']}\n- 理念：{features['办学理念']}\n- 优势学科：{', '.join(features['优势学科'])}\n- 产教融合：{features['产教融合']}\n- 校园文化：{features['校园文化']}"
    
    if intent == "greeting":
        return "您好！我是吉利学院智能客服，请问您想了解校史、校友、特色、课程、设施还是政策？"
    
    if intent == "course":
        if not entities:
            return "请提供课程名称，例如“高等数学的学分是多少？”"
        for ent in entities:
            if ent in courses:
                info = courses[ent]
                prereq = "、".join(info["先修"]) if info["先修"] else "无"
                return f"📘 **{ent}**\n- 学分：{info['学分']}\n- 教师：{info['教师']}\n- 教室：{info['教室']}\n- 先修：{prereq}"
        return "未找到该课程，可尝试“高等数学”、“数据结构”、“机器学习”等。"
    
    if intent == "facility":
        if not entities:
            return "请指定设施名称，如“图书馆”、“体育馆”、“第一食堂”或“校医院”。"
        for ent in entities:
            if ent in facilities:
                info = facilities[ent]
                extra = info.get("电话", info.get("项目", info.get("特色", info.get("服务", ""))))
                return f"🏢 **{ent}**\n- 开放时间：{info['开放时间']}\n- 位置：{info['位置']}\n- {extra}"
        return "未找到该设施，可尝试“图书馆”、“体育馆”等。"
    
    if intent == "policy":
        if not entities:
            return "您可以问“奖学金”、“转专业”或“助学金”。"
        for ent in entities:
            if ent in policies:
                info = policies[ent]
                return f"📜 **{ent}**\n- 条件：{info['条件']}\n- {info.get('金额', info.get('流程', ''))}\n- 时间：{info.get('申请时间', info.get('时间', '请咨询教务处'))}"
        return "未找到该政策，请尝试“奖学金”、“转专业”或“助学金”。"
    
    if intent == "history":
        if not entities:
            timeline = "\n".join([f"- {k}（{v['时间']}）：{v['事件']}" for k, v in history.items()])
            return f"📜 **吉利学院校史**\n{timeline}"
        for key in entities:
            if key in history:
                info = history[key]
                return f"📜 **{key}**：{info['时间']}，{info['事件']}"
        if "创办" in original_text:
            return f"📜 吉利学院创办于1999年，初名北京吉利大学。"
        if "迁址" in original_text or "搬到" in original_text:
            return f"📜 吉利学院于2020年整体迁至成都市，更名为吉利学院。"
        return "请具体询问，如“吉利学院创办时间”、“迁址成都”等。"
    
    if intent == "alumni":
        if not entities:
            names = "、".join(famous_alumni.keys())
            return f"🎓 **知名校友**：{names}。想了解哪位校友的详细信息？"
        for name in entities:
            if name in famous_alumni:
                info = famous_alumni[name]
                return f"🎓 **{name}**（{info['毕业年份']}，{info['专业']}）：{info['成就']}"
        if "有哪些" in original_text or "谁" in original_text:
            return f"🎓 吉利学院知名校友包括：{', '.join(famous_alumni.keys())}。"
        return "未找到该校友信息，可尝试“张强”、“李丽”等。"
    
    return "抱歉，我无法理解。试试“吉利学院特色”、“校训是什么”、“知名校友有哪些”、“高等数学的学分”等。"

# 动态子图绘制（含特色节点）
def draw_subgraph(entities, G):
    if not entities:
        seeds = ["吉利学院", "高等数学", "图书馆", "校训"]
        nodes = set()
        for s in seeds:
            if s in G:
                nodes.add(s)
                nodes.update(nx.single_source_shortest_path_length(G, s, cutoff=1).keys())
        subG = G.subgraph(nodes).copy()
    else:
        nodes_to_keep = set(entities)
        for ent in entities:
            if ent in G:
                nodes_to_keep.update(nx.single_source_shortest_path_length(G, ent, cutoff=1).keys())
        subG = G.subgraph(nodes_to_keep).copy()
    fig, ax = plt.subplots(figsize=(8, 6))
    if subG.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "无相关实体", ha='center', va='center')
        ax.axis('off')
        return fig
    pos = nx.spring_layout(subG, seed=42, k=1.8)
    node_colors = []
    for node in subG.nodes:
        if node in entities:
            node_colors.append("#ffb74d")
        elif node in courses: node_colors.append("#81c784")
        elif node in facilities: node_colors.append("#64b5f6")
        elif node in policies: node_colors.append("#e57373")
        elif node in history: node_colors.append("#f9a825")
        elif node in famous_alumni: node_colors.append("#ab47bc")
        elif node in features: node_colors.append("#26c6da")   # 特色用青色
        elif node == "吉利学院": node_colors.append("#ff7043")
        else: node_colors.append("#bdbdbd")
    nx.draw_networkx_nodes(subG, pos, ax=ax, node_color=node_colors, node_size=900, alpha=0.9)
    labels = {node: node for node in subG.nodes}
    nx.draw_networkx_labels(subG, pos, labels, ax=ax, font_size=9,
                            bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=1))
    if subG.edges:
        nx.draw_networkx_edges(subG, pos, ax=ax, edge_color="gray", width=1.5, alpha=0.6, style="dashed")
    ax.set_title("吉利学院知识图谱（局部视图）", fontsize=13)
    ax.axis('off')
    plt.tight_layout()
    return fig

# -------------------- 会话UI --------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "您好！我是吉利学院智能客服，请问您想了解**特色**、校史、校友、课程、设施还是政策？"}]
if "last_entities" not in st.session_state:
    st.session_state.last_entities = []
if "last_nlp" not in st.session_state:
    st.session_state.last_nlp = None

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("请输入您的问题..."):
    # 用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # NLP 处理
    intent = classify_intent(prompt)
    all_entities = {**courses, **facilities, **policies, **history, **famous_alumni, "吉利学院": None}
    entities = extract_entities(prompt, all_entities)
    st.session_state.last_entities = entities
    st.session_state.last_nlp = {"intent": intent, "entities": entities}
    
    # 生成回答
    answer = answer_question(intent, entities, prompt)
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
        # 显示 NLP 处理结果（自然语言处理过程可视化）
        with st.expander("🔍 自然语言处理过程"):
            st.markdown(f"**意图识别**: {intent}")
            st.markdown(f"**提取实体**: {', '.join(entities) if entities else '无'}")
            st.markdown("**规则匹配**: 基于关键词词典 + 正则表达式 + 模糊匹配")
            st.markdown("**知识图谱查询**: 匹配实体节点 → 提取属性 → 生成回答")

# 侧边栏
with st.sidebar:
    st.header("🗺️ 动态知识图谱")
    fig = draw_subgraph(st.session_state.last_entities, G)
    st.pyplot(fig)
    st.caption("🎨 颜色：课程绿 | 设施蓝 | 政策红 | 校史橙 | 校友紫 | 特色青 | 学校橙红")
    st.divider()
    st.subheader("📚 知识库速览")
    with st.expander("🏫 学校特色"):
        for k, v in features.items():
            if isinstance(v, list):
                st.write(f"- {k}: {', '.join(v)}")
            else:
                st.write(f"- {k}: {v}")
    with st.expander("📖 课程"):
        for c in courses: st.write(f"- {c}")
    with st.expander("🏢 设施"):
        for f in facilities: st.write(f"- {f}")
    with st.expander("📜 政策"):
        for p in policies: st.write(f"- {p}")
    with st.expander("📅 校史"):
        for e in history: st.write(f"- {e}（{history[e]['时间']}）")
    with st.expander("🎓 知名校友"):
        for a in famous_alumni: st.write(f"- {a}（{famous_alumni[a]['专业']}）")
    st.divider()
    st.caption("💡 自然语言处理示例：问“吉利学院有什么特色？” → 意图feature → 实体无 → 返回所有特色")