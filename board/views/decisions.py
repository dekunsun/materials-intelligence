"""Decisions: every investment with its decision, constraining resource and checkable continue / stop conditions.
Near-term commercial impact and long-term science are listed separately, never merged into one score."""

from __future__ import annotations

import streamlit as st

from board.data import load, t


def render(lang: str) -> None:
    d = load()
    st.header(t(lang, "Decisions", "决策"))
    st.write(t(lang,
        "Every recommendation is an inference from public evidence. Each item has a condition to continue and, where one exists, a condition to stop. No ROI is given: there is no reliable cost data.",
        "所有建议都是基于公开证据的推断。每一项都有继续条件，有停止条件的也写上。没有可靠的成本数据，所以不写投资回报率。"))
    names = d["directions"].set_index("id")["name_zh" if lang == "zh" else "name_en"]
    dec = d["decisions"].copy()
    sfx = "zh" if lang == "zh" else "en"
    for horizon, en, zh in [("near-term", "Near-term commercial impact", "近期商业影响"), ("long-term science", "Long-term scientific value", "长期科学价值")]:
        sub = dec[dec.horizon == horizon]
        st.subheader(t(lang, en, zh))
        for x in sub.itertuples():
            stop = getattr(x, f"stop_if_{sfx}")
            lines = [f"**{getattr(x, f'decision_{sfx}')}** · {getattr(x, f'investment_{sfx}')}  ",
                     f"<span style='color:rgba(128,128,128,.95);font-size:.85rem'>{names.get(x.direction, x.direction)} · "
                     f"{t(lang, 'constraining resource', '卡住的资源')}: {x.resource}</span>",
                     f"- {t(lang, 'Rationale', '理由')}: {getattr(x, f'rationale_{sfx}')}",
                     f"- {t(lang, 'Continue if', '继续条件')}: {getattr(x, f'continue_if_{sfx}')}"]
            if isinstance(stop, str) and stop:
                lines.append(f"- {t(lang, 'Stop if', '停止条件')}: {stop}")
            st.markdown("\n".join(lines), unsafe_allow_html=True)
