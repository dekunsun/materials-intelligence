"""Small shared helpers for the board views: evidence chips that stay readable in light and dark themes."""

from __future__ import annotations

import html

from board.data import SOURCE_ZH, STATUS_ZH

# One neutral grey for unverified items; verified items use the theme's text colour.
CSS = """
<style>
.ev {margin: 0 0 .55rem 0; line-height: 1.45;}
.ev .tag {display:inline-block; font-size:.72rem; padding:0 .4rem; margin-right:.35rem; border-radius:4px;
          border:1px solid rgba(128,128,128,.45);}
.ev.unverified, .ev.unverified .tag {color: rgba(128,128,128,.95);}
.ev .src {font-size:.75rem; color: rgba(128,128,128,.95);}
table.mx {border-collapse: collapse; width: 100%;}
table.mx th, table.mx td {border-bottom: 1px solid rgba(128,128,128,.3); padding: .45rem .5rem; text-align: left; vertical-align: top;}
table.mx td.num {white-space: nowrap;}
.muted {color: rgba(128,128,128,.95); font-size: .8rem;}
</style>
"""


def label(lang: str, source_type: str, status: str) -> str:
    if lang == "zh":
        return f"{SOURCE_ZH.get(source_type, source_type)} · {STATUS_ZH.get(status, status)}"
    return f"{source_type} · {status}"


def evidence_item(row, lang: str) -> str:
    cls = "ev" if row.status == "verified" else "ev unverified"
    claim = row.claim_zh if lang == "zh" else row.claim_en
    note = f" · {html.escape(str(row.note))}" if isinstance(row.note, str) and row.note else ""
    return (f'<div class="{cls}"><span class="tag">{html.escape(label(lang, row.source_type, row.status))}</span>'
            f'{html.escape(claim)}<br><span class="src">{html.escape(str(row.source))}{note}</span></div>')
