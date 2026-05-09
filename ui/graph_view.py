import json
import re
import streamlit as st
from huggingface_hub import InferenceClient
from config.constants import GRAPH_PROMPT, CHAR_LIMIT


def _call_llm_for_graph(hf_token: str, model_name: str, text: str) -> dict | None:
    """Запрашивает у LLM JSON с узлами и рёбрами графа."""
    text_for_llm = text[:CHAR_LIMIT]
    client = InferenceClient(model=model_name, token=hf_token)
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": GRAPH_PROMPT},
            {"role": "user", "content": f"Текст:\n{text_for_llm}"},
        ],
        max_tokens=2000,
        temperature=0.1,
    )
    raw = response.choices[0].message.content.strip()

    # Вырезаем JSON из возможных markdown-блоков ```json ... ```
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        return None
    return json.loads(match.group())


def _build_plotly_figure(graph_data: dict):
    """Строит интерактивный Plotly-граф из словаря nodes/edges."""
    import networkx as nx
    import plotly.graph_objects as go

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    if not nodes:
        return None

    G = nx.DiGraph()
    for node in nodes:
        G.add_node(node["id"], label=node.get("label", node["id"]))
    for edge in edges:
        G.add_edge(edge["source"], edge["target"], label=edge.get("label", ""))

    pos = nx.spring_layout(G, seed=42, k=2.5)

    # Рёбра
    edge_traces = []
    for src, dst, data in G.edges(data=True):
        if src not in pos or dst not in pos:
            continue
        x0, y0 = pos[src]
        x1, y1 = pos[dst]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        edge_traces.append(
            go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line=dict(width=1.5, color="#888"),
                hoverinfo="none",
                showlegend=False,
            )
        )
        edge_label = data.get("label", "")
        if edge_label:
            edge_traces.append(
                go.Scatter(
                    x=[mx],
                    y=[my],
                    mode="text",
                    text=[edge_label],
                    textfont=dict(size=9, color="#aaa"),
                    hoverinfo="none",
                    showlegend=False,
                )
            )

    # Узлы
    node_x, node_y, node_text, node_hover = [], [], [], []
    for node_id in G.nodes():
        if node_id not in pos:
            continue
        x, y = pos[node_id]
        node_x.append(x)
        node_y.append(y)
        label = G.nodes[node_id].get("label", node_id)
        node_text.append(label)
        degree = G.degree(node_id)
        node_hover.append(f"{label}<br>Связей: {degree}")

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        textfont=dict(size=11),
        hovertext=node_hover,
        hoverinfo="text",
        marker=dict(
            size=18,
            color="#4C9BE8",
            line=dict(width=2, color="#1a5fa8"),
        ),
        showlegend=False,
    )

    fig = go.Figure(
        data=edge_traces + [node_trace],
        layout=go.Layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font=dict(color="#fff"),
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=520,
            hovermode="closest",
        ),
    )
    return fig


def render_graph_section(hf_token: str, model_name: str, extracted_text: str):
    """Отрисовывает секцию построения графа понятий."""
    st.write("---")
    st.subheader("🕸️ Граф понятий")
    st.caption("ИИ извлечёт ключевые понятия из текста и покажет связи между ними.")

    if st.button("🔗 Построить граф", key="build_graph_btn"):
        hf_token = hf_token.strip() if hf_token else ""
        if not hf_token or not hf_token.startswith("hf_"):
            st.warning("⚠️ Введите корректный ключ доступа Hugging Face в меню слева.")
            return

        with st.spinner("🤖 Извлекаем понятия и связи..."):
            try:
                graph_data = _call_llm_for_graph(hf_token, model_name, extracted_text)
            except Exception as e:
                st.error(f"❌ Ошибка при обращении к ИИ: {e}")
                return

        if not graph_data:
            st.error("❌ Не удалось разобрать ответ модели. Попробуйте другую модель.")
            return

        st.session_state.graph_data = graph_data

    if st.session_state.get("graph_data"):
        graph_data = st.session_state.graph_data
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        col1, col2 = st.columns([2, 1])
        with col1:
            st.metric("Понятий", len(nodes))
        with col2:
            st.metric("Связей", len(edges))

        try:
            fig = _build_plotly_figure(graph_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Граф пустой — модель не вернула понятия.")
        except ImportError:
            st.error("❌ Установите зависимости: `pip install plotly networkx`")
        except Exception as e:
            st.error(f"❌ Ошибка построения графа: {e}")

        with st.expander("📋 Данные графа (JSON)"):
            st.json(graph_data)
