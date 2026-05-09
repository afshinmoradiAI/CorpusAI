from app.schemas.papers import Chunk
from app.services.retrieval import ChunkIndex


def _chunk(text: str, idx: int = 0) -> Chunk:
    return Chunk(chunk_id=f"c{idx}", ref_id="r1", text=text, page=1)


def test_index_returns_most_relevant_chunk_first() -> None:
    index = ChunkIndex()
    index.add(
        [
            _chunk("CRISPR Cas9 off-target effects in human T cells", 0),
            _chunk("RNA-seq protocols for budding yeast", 1),
            _chunk("Mitochondrial dynamics during apoptosis", 2),
        ]
    )

    matches = index.search("crispr off-target", k=2)
    assert len(matches) == 2
    assert matches[0].chunk.chunk_id == "c0"
    assert matches[0].score > matches[1].score


def test_empty_index_returns_no_matches() -> None:
    assert ChunkIndex().search("anything") == []
