"""Безопасный разбор и отображение таблиц и графиков из ответа ИИ."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import pandas as pd
import streamlit as st


VISUAL_BLOCK_PATTERN = re.compile(
    r"```(?P<kind>vlom-table|vlom-chart)\s*\n?"
    r"(?P<payload>\{.*?\})\s*```",
    flags=re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class VisualBlock:
    kind: str
    payload: dict[str, Any]


def extract_visual_blocks(content: str) -> list[VisualBlock]:
    """Возвращает только корректные визуальные блоки."""

    blocks: list[VisualBlock] = []

    for match in VISUAL_BLOCK_PATTERN.finditer(content or ""):
        try:
            payload = json.loads(match.group("payload"))
        except (json.JSONDecodeError, TypeError):
            continue

        kind = match.group("kind").lower()

        if kind == "vlom-table" and _is_valid_table(payload):
            blocks.append(VisualBlock(kind=kind, payload=payload))
        elif kind == "vlom-chart" and _is_valid_chart(payload):
            blocks.append(VisualBlock(kind=kind, payload=payload))

    return blocks


def remove_visual_blocks(content: str) -> str:
    """Удаляет служебные JSON-блоки из основного текста конспекта."""

    return VISUAL_BLOCK_PATTERN.sub("", content or "").strip()


def raw_visual_blocks(content: str) -> str:
    """Возвращает исходные блоки для сохранения после редактирования."""

    return "\n\n".join(
        match.group(0).strip()
        for match in VISUAL_BLOCK_PATTERN.finditer(content or "")
    )


def render_visual_blocks(content: str, *, key_prefix: str) -> None:
    """Отображает таблицы и графики, найденные в конспекте."""

    blocks = extract_visual_blocks(content)
    if not blocks:
        return

    st.markdown("### 📊 Таблицы и графики")

    for index, block in enumerate(blocks):
        payload = block.payload
        title = str(payload.get("title") or "Визуализация")

        with st.container(border=True):
            st.markdown(f"#### {title}")

            if block.kind == "vlom-table":
                _render_table(payload, key=f"{key_prefix}_table_{index}")
            else:
                _render_chart(payload)

            description = payload.get("description")
            if description:
                st.caption(str(description))


def _is_valid_table(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False

    columns = payload.get("columns")
    rows = payload.get("rows")

    if not isinstance(columns, list) or not columns:
        return False
    if not all(isinstance(column, str) and column.strip() for column in columns):
        return False
    if not isinstance(rows, list) or not rows:
        return False

    width = len(columns)
    return all(isinstance(row, list) and len(row) == width for row in rows)


def _is_valid_chart(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False

    chart_type = payload.get("type")
    x_key = payload.get("x")
    y_key = payload.get("y")
    data = payload.get("data")

    if chart_type not in {"bar", "line", "area", "scatter"}:
        return False
    if not isinstance(x_key, str) or not x_key.strip():
        return False
    if not isinstance(y_key, str) or not y_key.strip():
        return False
    if not isinstance(data, list) or len(data) < 2:
        return False

    return all(
        isinstance(row, dict) and x_key in row and y_key in row
        for row in data
    )


def _render_table(payload: dict[str, Any], *, key: str) -> None:
    frame = pd.DataFrame(payload["rows"], columns=payload["columns"])
    st.dataframe(frame, use_container_width=True, hide_index=True)


def _render_chart(payload: dict[str, Any]) -> None:
    chart_type = payload["type"]
    x_key = payload["x"]
    y_key = payload["y"]

    frame = pd.DataFrame(payload["data"])
    frame[y_key] = pd.to_numeric(frame[y_key], errors="coerce")
    frame = frame.dropna(subset=[y_key])

    if len(frame) < 2:
        st.warning("График не построен: недостаточно корректных числовых данных.")
        return

    if chart_type == "scatter":
        # Для scatter обе оси должны быть числовыми.
        frame[x_key] = pd.to_numeric(frame[x_key], errors="coerce")
        frame = frame.dropna(subset=[x_key])
        if len(frame) < 2:
            st.warning("График не построен: ось X не содержит числовых данных.")
            return
        st.scatter_chart(frame, x=x_key, y=y_key, use_container_width=True)
        return

    indexed = frame.set_index(x_key)[[y_key]]

    if chart_type == "bar":
        st.bar_chart(indexed, use_container_width=True)
    elif chart_type == "line":
        st.line_chart(indexed, use_container_width=True)
    else:
        st.area_chart(indexed, use_container_width=True)
