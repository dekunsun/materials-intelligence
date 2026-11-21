"""Read-only loaders for the Portfolio Board. Every table lives in data/board/*.csv."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "data" / "board"

DIMENSIONS = ["Market Demand", "Scientific Validation", "AI Incremental Advantage"]
DIM_ZH = {"Market Demand": "市场需求", "Scientific Validation": "科学验证", "AI Incremental Advantage": "AI 增量优势"}
SOURCE_ORDER = ["reproduced here", "primary", "secondary", "series article"]
SOURCE_ZH = {"reproduced here": "本项目复现", "primary": "一手来源", "secondary": "二手来源", "series article": "系列文章"}
STATUS_ZH = {"verified": "已核实", "unverified": "未核实", "company claim": "公司说法"}


@st.cache_data
def load() -> dict[str, pd.DataFrame]:
    return {name: pd.read_csv(BOARD / f"{name}.csv") for name in ("directions", "evidence", "decisions", "gates")}


def t(lang: str, en: str, zh: str) -> str:
    return zh if lang == "zh" else en
