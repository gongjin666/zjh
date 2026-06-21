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
# 数据部分保持不变（略，与原代码一致，此处省略重复内容以节省篇幅）
# 实际使用时请将原 courses, facilities, policies, history, famous_alumni,
# honors, leaders, campuses, campus_culture, clubs 全部保留。

# ==================== 构建知识图谱 ====================
@st.cache_resource
def build_graph():
    G = nx.Graph()
    G.add_node("吉利学院", type="学校")
    # ... 所有节点和边的添加逻辑与原代码完全相同（此处省略，实际保留）
    return G

G = build_graph()

# ==================== NLP 意图识别（与原代码一致） ====================
# 所有 intent_keywords, classify_intent, extract_entities, answer_question
# 均保持不变（此处省略，实际保留）

# ==================== 使用 pyvis 生成交互式图谱 ====================
def build_pyvis_html(G, highlight_nodes=None, height="600px", width="100%"):
    """
    生成 pyvis 网络图的 HTML 字符串。
    highlight_nodes: 需要高亮显示的节点列表（及其邻居），若为 None 则显示全部节点。
    """
    net = Network(height=height, width=width, bgcolor="#ffffff", font_color="black")
    # 设置物理布局，使节点更分散
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
        subG = G  # 全图（但节点过多时可能卡顿，建议限制层级）

    # 如果子图太大（>200节点），只显示核心节点（可优化）
    if subG.number_of_nodes() > 200:
        # 只保留吉利学院及其2跳邻居
        core = set()
        if "吉利学院" in G:
            core.add("吉利学院")
            core.update(nx.single_source_shortest_path_length(G, "吉利学院", cutoff=2).keys())
        subG = G.subgraph(core).copy()

    # 添加节点，并设置颜色、大小、标题（悬停显示）
    color_map = {
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
        "学校": "#ff7043",
        "教师": "#ffb74d",
        "教室": "#90a4ae",
        "位置": "#78909c",
    }

    # 预先构建类型映射（根据节点属性或所属字典）
    type_dict = {}
    for node in subG.nodes:
        if node in courses: type_dict[node] = "课程"
        elif node in facilities: type_dict[node] = "设施"
        elif node in policies: type_dict[node] = "政策"
        elif node in history: type_dict[node] = "校史"
        elif node in famous_alumni: type_dict[node] = "校友"
        elif node in honors: type_dict[node] = "荣誉年份"
        elif node in [leaders[k] for k in leaders if isinstance(leaders[k], str)] + \
                [item for sublist in [leaders[k] for k in leaders if isinstance(leaders[k], list)] for item in sublist]:
            type_dict[node] = "领导"
        elif node in campuses: type_dict[node] = "校区"
        elif node in campus_culture: type_dict[node] = "文化"
        elif node in clubs: type_dict[node] = "社团类别"
        elif any(node in lst for lst in clubs.values()): type_dict[node] = "社团"
        elif node == "吉利学院": type_dict[node] = "学校"
        else: type_dict[node] = "其他"

    for node in subG.nodes:
        node_type = type_dict.get(node, "其他")
        color = color_map.get(node_type, "#bdbdbd")
        # 如果是高亮节点，使用红色边框
        border_color = "red" if highlight_nodes and node in highlight_nodes else color
        title = f"{node}\n类型: {node_type}"  # 悬停显示
        net.add_node(node, label=node, color=color, borderWidth=2,
                     title=title, font={"size": 14}, shape="dot", size=20)

    # 添加边
    for u, v in subG.edges:
        # 获取关系（如有）
        relation = ""
        if u in courses and v in courses: relation = "先修"  # 简单示例
        net.add_edge(u, v, title=relation, width=1)

    # 生成HTML并保存到临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        net.save_graph(f.name)
        return f.name  # 返回文件路径，以便用 st.components.v1.html 嵌入

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

    # 输入框
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

    # 侧边栏（放在Tab1内部，显示小图谱）
    with st.sidebar:
        st.header("🗺️ 知识图谱（局部）")
        # 生成交互式小图（基于最近实体）
        if st.session_state.last_entities:
            highlight = st.session_state.last_entities
        else:
            highlight = ["吉利学院"]
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

# ---------- Tab2: 知识图谱探索 ----------
with tab2:
    st.subheader("🔍 全局知识图谱探索")
    col1, col2 = st.columns([3, 1])
    with col2:
        search_term = st.text_input("搜索节点", placeholder="输入课程/校友/设施名...")
    with col1:
        st.write("下方图谱可拖拽、滚轮缩放，节点悬停显示详细信息。")

    # 根据搜索词高亮
    if search_term:
        # 模糊匹配
        all_node_names = list(G.nodes)
        matches = get_close_matches(search_term, all_node_names, n=5, cutoff=0.6)
        highlight_nodes = matches if matches else [search_term] if search_term in G else None
    else:
        highlight_nodes = None  # 显示全图（但限制节点数以防卡顿）

    html_path = build_pyvis_html(G, highlight_nodes=highlight_nodes, height="700px")
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    st.components.v1.html(html_content, height=750)
    os.unlink(html_path)

    st.caption("💡 提示：输入节点名称可高亮显示该节点及其直接关联邻居（红色边框）。")