"""Module results: the figure and headline numbers of each technical module, with links to the reports."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from board.data import ROOT, t

MODULES = [
    ("Solid-state electrolytes", "固态电池电解质", "results/battery_20261121T080824Z/discovery_curves.png", "modules/battery/REPORT.md",
     ["Within known families, prior data: about 30 → 5 experiments to find 5 hits (random vs screening)",
      "Series held out: screening 7.6–12.9; only 3–4 better than the chemical-family rule",
      "Transfer: works for sulfides, fails for oxides; RL has no stable advantage (one policy)"],
     ["已知家族内，先验数据：找到 5 个过线材料从约 30 次降到 5 次（随机对筛选）",
      "按系列留出：筛选 7.6–12.9 次，只比化学家族规则多省 3–4 次",
      "迁移：硫化物有效，氧化物失效；强化学习没有稳定优势（只训练一个策略）"]),
    ("Chip cooling", "芯片散热", "results/thermal_20261121T174521Z/thermal_summary.png", "modules/thermal/REPORT.md",
     ["62 models re-scored; exact leaderboard match", "Better half: 28 of 31 give the same top 10 (easy test set)",
      "DFT 10–27% below measurement for 6 of 7 materials; gate: buyers point to cooling architecture"],
     ["62 个模型重新计分，和排行榜完全一致", "较好的一半：31 个里 28 个前 10 名相同（测试集太容易）",
      "7 个材料里 6 个 DFT 比实测低 10–27%；关卡结论：买家指向冷却架构"]),
    ("Stability screening & CSP", "稳定性筛选与 CSP", "results/csp_screening_20261121T192919Z/screening_summary.png", "modules/csp/REPORT.md",
     ["73 models re-scored; 146/146 leaderboard metric sets match", "1% budget: 48 models ≥ 95% stable (random 15.5%); wasted share 1.5% / 3.0% / 13.4%",
      "Predicted just below the hull: top models ~90% right, CHGNet 39%"],
     ["73 个模型重新计分，146 组指标全部一致", "1% 预算：48 个模型 ≥ 95% 稳定（随机 15.5%）；浪费比例 1.5% / 3.0% / 13.4%",
      "预测刚好在凸包下方：前列模型约 90% 对，CHGNet 39%"]),
]


def render(lang: str) -> None:
    st.header(t(lang, "Module results", "模块结果"))
    for en, zh, fig, report, pts_en, pts_zh in MODULES:
        st.subheader(zh if lang == "zh" else en)
        for p in (pts_zh if lang == "zh" else pts_en):
            st.markdown(f"- {p}")
        path = ROOT / fig
        if path.exists():
            st.image(str(path), width="stretch")
        else:
            st.warning(t(lang, f"Figure not found: {fig}", f"找不到图：{fig}"))
        st.caption(t(lang, f"Full report: {report}", f"完整报告：{report}"))
        st.divider()
