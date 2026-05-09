from app.services.chunker import chunk_pages
from app.services.pdf_reader import PageText


def _para(n_words: int) -> str:
    return " ".join(f"word{i}" for i in range(n_words))


def test_chunker_emits_target_sized_chunks() -> None:
    pages = [
        PageText(page=1, text="\n\n".join([_para(100)] * 5)),
        PageText(page=2, text="\n\n".join([_para(100)] * 5)),
    ]
    chunks = chunk_pages(pages, ref_id="r1")

    assert len(chunks) >= 2
    for c in chunks:
        word_count = len(c.text.split())
        assert word_count <= 600
        assert c.ref_id == "r1"
        assert c.page in (1, 2)


def test_chunker_skips_empty_pages() -> None:
    pages = [PageText(page=1, text=""), PageText(page=2, text=_para(50))]
    chunks = chunk_pages(pages, ref_id="r1")
    assert len(chunks) == 1
    assert chunks[0].page == 2
