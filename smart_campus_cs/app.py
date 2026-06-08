import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import re
from difflib import get_close_matches

# 页面配置
st.set_page_config(page_title="智能校园客服", page_icon="🤖", layout="wide")

# 自定义CSS（让聊天区域更美观）
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 20px;
        padding: 10px;
    }
    .st-emotion-cache-1v7f65g {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 智能校园客服")
st.markdown("> **升级版** | 自然语言处理 + 校园知识图谱 | 支持课程、设施、政策问答")

# -------------------- 知识图谱数据（已扩充）--------------------
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

# 构建知识图谱（缓存）
@st.cache_resource
def build_graph():
    G = nx.Graph()
    # 添加节点
    for name in courses:
        G.add_node(name, type="课程")
    for name in facilities:
        G.add_node(name, type="设施")
    for name in policies:
        G.add_node(name, type="政策")
    # 课程关系
    for course, info in courses.items():
        teacher = info["教师"]
        G.add_node(teacher, type="教师")
        G.add_edge(course, teacher, relation="讲授")
        room = info["教室"]
        G.add_node(room, type="教室")
        G.add_edge(course, room, relation="在")
        for pre in info["先修"]:
            G.add_edge(pre, course, relation="先修")
    # 设施位置
    for fac, info in facilities.items():
        loc = info["位置"]
        G.add_node(loc, type="位置")
        G.add_edge(fac, loc, relation="位于")
    return G

G = build_graph()

# -------------------- NLP 模块（增强版）--------------------
intent_keywords = {
    "greeting": ["你好", "您好", "hi", "hello", "在吗", "你好呀"],
    "course": ["课程", "学分", "老师", "教室", "先修", "前置", "怎么学"],
    "facility": ["图书馆", "食堂", "体育馆", "校医院", "开放时间", "在哪", "几点", "电话"],
    "policy": ["奖学金", "转专业", "助学金", "政策", "条件", "申请", "多少钱"],
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

def answer_question(intent, entities, text):
    if intent == "greeting":
        return "您好！我是校园智能客服，请问您想咨询课程、设施还是政策？"
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
    return "抱歉，我无法理解。试试“高等数学的学分”、“图书馆几点开门”或“奖学金条件”。"

# 动态子图绘制（优化布局）
def draw_subgraph(entities, G):
    if not entities:
        seeds = ["高等数学", "图书馆", "奖学金"]
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
    pos = nx.spring_layout(subG, seed=42, k=1.8)  # 增大k使节点分散
    node_colors = []
    for node in subG.nodes:
        if node in entities:
            node_colors.append("#ffb74d")  # 橙色高亮
        elif node in courses:
            node_colors.append("#81c784")  # 绿色课程
        elif node in facilities:
            node_colors.append("#64b5f6")  # 蓝色设施
        elif node in policies:
            node_colors.append("#e57373")  # 红色政策
        else:
            node_colors.append("#bdbdbd")  # 灰色辅助
    nx.draw_networkx_nodes(subG, pos, ax=ax, node_color=node_colors, node_size=900, alpha=0.9)
    labels = {node: node for node in subG.nodes}
    nx.draw_networkx_labels(subG, pos, labels, ax=ax, font_size=9,
                            bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=1))
    if subG.edges:
        nx.draw_networkx_edges(subG, pos, ax=ax, edge_color="gray", width=1.5, alpha=0.6, style="dashed")
    ax.set_title("智能校园知识图谱（局部视图）", fontsize=13)
    ax.axis('off')
    plt.tight_layout()
    return fig

# 会话状态
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "您好！我是升级版校园智能客服，请问有什么可以帮您？"}]
if "last_entities" not in st.session_state:
    st.session_state.last_entities = []

# 显示聊天历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 用户输入
if prompt := st.chat_input("请输入您的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    intent = classify_intent(prompt)
    all_entities = {**courses, **facilities, **policies}
    entities = extract_entities(prompt, all_entities)
    st.session_state.last_entities = entities
    answer = answer_question(intent, entities, prompt)
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

# 侧边栏图谱及知识库
with st.sidebar:
    st.header("🗺️ 动态知识图谱")
    fig = draw_subgraph(st.session_state.last_entities, G)
    st.pyplot(fig)
    st.caption("🎨 颜色说明：绿色=课程 | 蓝色=设施 | 红色=政策 | 橙色=本次问题涉及实体")
    st.divider()
    st.subheader("📚 知识库速览")
    with st.expander("📖 课程列表"):
        for c in courses:
            st.write(f"- {c}（{courses[c]['教师']}，{courses[c]['学分']}学分）")
    with st.expander("🏢 设施列表"):
        for f in facilities:
            st.write(f"- {f}（{facilities[f]['位置']}）")
    with st.expander("📜 政策列表"):
        for p in policies:
            st.write(f"- {p}")
    st.divider()
    st.caption("💡 提示：点击左侧聊天输入框即可提问，右侧图谱会动态变化。")