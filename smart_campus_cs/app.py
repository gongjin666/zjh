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

# ==================== 知识图谱数据（完全基于文档）====================
# （所有 courses, facilities, policies, history, famous_alumni, honors, leaders, campuses, campus_culture, clubs 定义保持不变，此处省略以节省篇幅，实际使用时请全部保留）

# 注意：数据定义必须放在最前面，确保全局可用。

# ==================== 构建知识图谱 ====================
@st.cache_resource
def build_graph():
    G = nx.Graph()
    G.add_node("吉利学院", type="学校")
    # ...（所有节点和边的添加，与原代码完全相同）
    return G

G = build_graph()

# ==================== NLP 意图识别（与原代码一致）====================
# 所有 intent_keywords, classify_intent, extract_entities, answer_question 函数
# 保持原样，此处不再重复。

# ==================== 使用 pyvis 生成交互式图谱（修正版）====================
def build_pyvis_html(G, highlight_nodes=None, height="600px", width="100%"):
    """
    生成 pyvis 网络图的 HTML 字符串。
    所有节点类型直接从 G 的节点属性中读取，不再依赖外部字典。
    """
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

    # 确定要显示的子图
    if highlight_nodes:
        nodes_to_keep = set(highlight_nodes)
        for node in highlight_nodes:
            if node in G:
                nodes_to_keep.update(nx.single_source_shortest_path_length(G, node, cutoff=1).keys())
        subG = G.subgraph(nodes_to_keep).copy()
    else:
        subG = G
        # 防止节点过多导致浏览器卡顿（保留核心节点）
        if subG.number_of_nodes() > 200:
            core = set()
            if "吉利学院" in G:
                core.add("吉利学院")
                core.update(nx.single_source_shortest_path_length(G, "吉利学院", cutoff=2).keys())
            subG = G.subgraph(core).copy()

    # 颜色映射（与节点类型对应）
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
        # 直接从图中读取节点类型，若无则默认为"其他"
        node_type = G.nodes[node].get('type', '其他')
        color = color_map.get(node_type, "#bdbdbd")
        border_color = "red" if highlight_nodes and node in highlight_nodes else color
        title = f"{node}\n类型: {node_type}"
        net.add_node(node, label=node, color=color, borderWidth=2,
                     title=title, font={"size": 14}, shape="dot", size=20)

    for u, v in subG.edges:
        # 获取关系（如果有）
        relation = G[u][v].get('relation', '')
        net.add_edge(u, v, title=relation, width=1)

    # 保存为临时HTML文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        net.save_graph(f.name)
        return f.name

# ==================== 会话状态初始化 ====================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "您好！我是吉利学院智能客服，已整合校史、校友、荣誉、领导、校区、文化、社团等数据。请问您想了解什么？"}]
if "last_entities" not in st.session_state:
    st.session_state.last_entities = []

# ==================== 使用 Tabs 分割界面 ====================
tab1, tab2 = st.tabs(["💬 智能客服", "🗺️ 知识图谱探索"])

# ---------- Tab1: 聊天界面 ----------
with tab1:
    # 显示对话历史
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("请输入您的问题..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        intent = classify_intent(prompt)
        # 构建实体字典（用于提取）
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

    # 侧边栏（显示小图谱）
    with st.sidebar:
        st.header("🗺️ 知识图谱（局部）")
        highlight = st.session_state.last_entities if st.session_state.last_entities else ["吉利学院"]
        html_path = build_pyvis_html(G, highlight_nodes=highlight, height="350px")
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=380)
        os.unlink(html_path)  # 清理临时文件
        st.caption("🖱️ 可拖拽、缩放 | 红色边框为查询实体")

        st.divider()
        st.subheader("📚 吉利学院知识库")
        with st.expander("🏫 校史"):
            for k, v in history.items():
                st.write(f"- {v['时间']}：{v['事件']}")
        with st.expander("🎓 知名校友"):
            for name, info in famous_alumni.items():
                st.write(f"- {name}：{info['职务'][:30]}...")
        # 其他展开项略（与原来相同）

# ---------- Tab2: 知识图谱探索 ----------
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