"""On-disk figure storage for the Thesis pipeline.

Figures are uploaded once per session and referenced by `figure_id`.
Each chapter can include zero or more figures; the LLM writer is told
about available figures and emits `[fig=ID]` / `<<FIG=ID>>` markers
in its output. The assembler resolves IDs into globally numbered
captions, and the DOCX exporter embeds the actual image bytes.

Storage layout:
    {DATA_DIR}/figures/<figure_id>.<ext>

There is no per-user isolation in this MVP. The figure_id (UUID4) is
the only handle, so accidental enumeration is the only risk.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from app.core.config import get_settings

_ALLOWED_EXTS: frozenset[str] = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp"})


class FigureStoreError(Exception):
    pass


def _root() -> Path:
    root = Path(get_settings().data_dir) / "figures"
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_figure(filename: str, data: bytes) -> tuple[str, Path]:
    """Save figure bytes under a new UUID and return (figure_id, path)."""
    suffix = Path(filename).suffix.lower()
    if suffix not in _ALLOWED_EXTS:
        raise FigureStoreError(
            f"Unsupported figure extension {suffix!r}. "
            f"Allowed: {', '.join(sorted(_ALLOWED_EXTS))}"
        )
    figure_id = uuid.uuid4().hex
    out = _root() / f"{figure_id}{suffix}"
    out.write_bytes(data)
    return figure_id, out


def path_for(figure_id: str) -> Path | None:
    """Return the on-disk path for `figure_id`, or None if missing."""
    root = _root()
    for ext in _ALLOWED_EXTS:
        candidate = root / f"{figure_id}{ext}"
        if candidate.exists():
            return candidate
    return None
