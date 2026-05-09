"""Convert the assembled paper markdown into a .docx byte stream.

The paper format is well-constrained (we wrote the assembler ourselves),
so a small line-by-line walker handles every shape we emit:

    # Title              -> Heading 0
    ## Section           -> Heading 1
    ### Subsection       -> Heading 2
    [N] citation         -> numbered reference paragraph
    plain line           -> body paragraph
    blank line           -> paragraph break (already implied)
"""

from __future__ import annotations

import io

from docx import Document  # type: ignore[import-untyped]


def paper_to_docx(markdown: str) -> bytes:
    doc = Document()
    for line in markdown.splitlines():
        stripped = line.rstrip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            doc.add_heading(stripped[2:].strip(), level=0)
        elif stripped.startswith("## "):
            doc.add_heading(stripped[3:].strip(), level=1)
        elif stripped.startswith("### "):
            doc.add_heading(stripped[4:].strip(), level=2)
        else:
            doc.add_paragraph(stripped)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
