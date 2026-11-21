"""Direction detail: the six gates for one direction, with every evidence row placed at its gate."""

from __future__ import annotations

import streamlit as st

from board.data import DIM_ZH, load, t
from board.views.common import CSS, evidence_item


def render(lang: str) -> None:
    d = load()
    st.markdown(CSS, unsafe_allow_html=True)
    dirs = d["directions"]
    ids = dirs.id.tolist()
    q = st.query_params.get("direction")
    pick = st.selectbox(t(lang, "Direction", "方向"), ids, index=ids.index(q) if q in ids else 0,
                        format_func=lambda i: dirs.set_index("id").loc[i, "name_zh" if lang == "zh" else "name_en"])
    if pick != q:
        st.query_params["direction"] = pick
    r = dirs.set_index("id").loc[pick]
    st.header(r.name_zh if lang == "zh" else r.name_en)
    st.markdown(f"**{t(lang, 'Business question', '商业问题')}:** {r.business_question_zh if lang == 'zh' else r.business_question_en}")
    if isinstance(r.module_report, str) and r.module_report:
        st.caption(t(lang, f"Module report: {r.module_report}", f"模块报告：{r.module_report}"))
    ev = d["evidence"][d["evidence"].direction == pick]
    for g in d["gates"].itertuples():
        items = ev[ev.gate == g.gate]
        title = f"{g.gate}. {g.name_zh if lang == 'zh' else g.name_en}"
        with st.expander(f"{title}  ·  {len(items)}", expanded=not items.empty):
            st.caption(g.criterion_zh if lang == "zh" else g.criterion_en)
            if items.empty:
                st.markdown(t(lang, "_No evidence at this gate yet._", "_这一关还没有证据。_"))
            for dim, grp in items.groupby("dimension", sort=False):
                st.markdown(f"**{DIM_ZH[dim] if lang == 'zh' else dim}**")
                st.markdown("".join(evidence_item(x, lang) for x in grp.itertuples()), unsafe_allow_html=True)
    dec = d["decisions"][d["decisions"].direction == pick]
    st.subheader(t(lang, "Decisions for this direction", "这个方向的决策"))
    if dec.empty:
        st.write(t(lang, "Not evaluated in this version.", "这一版没有评估。"))
    for x in dec.itertuples():
        inv = x.investment_zh if lang == "zh" else x.investment_en
        st.markdown(f"- **{x.decision_zh if lang == 'zh' else x.decision_en}** · {inv}")
