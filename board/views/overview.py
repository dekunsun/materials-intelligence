"""Overview: each direction on three independent evidence dimensions, plus its current decision.

No composite score and no 'gate reached' ranking across directions: a commercial
product being bought does not show that AI added anything, so the dimensions stay apart.
"""

from __future__ import annotations

import html

import streamlit as st

from board.data import DIMENSIONS, DIM_ZH, load, t
from board.views.common import CSS


def cell(ev, lang: str) -> str:
    if ev.empty:
        return f'<span class="muted">{t(lang, "no evidence collected", "尚未收集证据")}</span>'
    ver = ev[ev.status == "verified"]
    parts = []
    n_rep = int((ver.source_type == "reproduced here").sum())
    n_pri = int((ver.source_type == "primary").sum())
    n_comp = int((ev.status == "company claim").sum())
    n_unv = int((ev.status == "unverified").sum())
    if n_rep: parts.append(t(lang, f"{n_rep} reproduced here", f"本项目复现 {n_rep}"))
    if n_pri: parts.append(t(lang, f"{n_pri} primary", f"一手 {n_pri}"))
    if n_comp: parts.append(t(lang, f"{n_comp} company claim", f"公司说法 {n_comp}"))
    if n_unv: parts.append(f'<span class="muted">{t(lang, f"{n_unv} unverified", f"未核实 {n_unv}")}</span>')
    top_gate = int(ver.gate.max()) if not ver.empty else None
    gate_txt = (t(lang, f"furthest verified gate: {top_gate}", f"已核实的最远关卡：{top_gate}") if top_gate
                else t(lang, "nothing verified yet", "尚无已核实证据"))
    return "<br>".join(parts) + f'<br><span class="muted">{gate_txt}</span>'


def render(lang: str) -> None:
    d = load()
    st.markdown(CSS, unsafe_allow_html=True)
    st.header(t(lang, "Overview: three independent evidence dimensions", "总览：三个独立的证据维度"))
    st.write(t(lang,
        "Each direction is shown on market demand, scientific validation and AI's added value separately. "
        "There is no total score, and gate numbers are not compared across directions.",
        "每个方向分别显示市场需求、科学验证和 AI 增量优势，不合成总分，也不跨方向比较\"过了第几关\"。"))
    head = "".join(f"<th>{html.escape(DIM_ZH[x] if lang == 'zh' else x)}</th>" for x in DIMENSIONS)
    rows = []
    for r in d["directions"].itertuples():
        ev = d["evidence"][d["evidence"].direction == r.id]
        name = r.name_zh if lang == "zh" else r.name_en
        dec = r.decision_zh if lang == "zh" else r.decision_en
        cells = "".join(f"<td>{cell(ev[ev.dimension == dim], lang)}</td>" for dim in DIMENSIONS)
        rows.append(f"<tr><td><b>{html.escape(name)}</b><br><span class='muted'>{html.escape(r.kind)}</span></td>{cells}"
                    f"<td>{html.escape(dec)}</td></tr>")
    st.markdown(f"<table class='mx'><tr><th>{t(lang, 'Direction', '方向')}</th>{head}<th>{t(lang, 'Current decision', '当前决定')}</th></tr>"
                + "".join(rows) + "</table>", unsafe_allow_html=True)
    st.caption(t(lang,
        "'Reproduced here' = computed in this project from public data. 'Primary' = the source itself was read. "
        "Grey = not yet checked against a primary source (mostly the series' Layer 1 numbers).",
        "\"本项目复现\"指在本项目里用公开数据算出来的；\"一手\"指读过原始来源；灰色表示还没有对照一手来源核实（大多是系列文章市场层的数字）。"))
