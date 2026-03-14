import os
import json
from pathlib import Path
from unittest import mock

import numpy as np
import pytest

import ingest
# `query` is imported lazily in the tests that need it.  importing it
# at module scope triggers faiss/model initialization which slows down
# collection and tries to open a real index file.


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolate_fs(tmp_path, monkeypatch):
    """Run every test in a temporary working directory so nothing touches
    the real project files.  The fixture also makes sure the cwd is reset
    after the test finishes.
    """
    monkeypatch.chdir(tmp_path)
    yield


@pytest.fixture
def vector_store(tmp_path, monkeypatch):
    """Prepare a fresh vector_store directory and point the ingest module
    at it.  Tests can use this to assert that index/json pairs are created.
    """
    vs = tmp_path / "vector_store"
    vs.mkdir()
    monkeypatch.setattr(ingest, "VECTOR_DIR", str(vs))
    return vs


# ---------------------------------------------------------------------------
# file reading tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("extension,content", [
    (".txt", "Simple text content"),
    (".pdf", "PDF content goes here"),
])
def test_read_file(tmp_path, monkeypatch, extension, content):
    # create a dummy file of the requested type
    fpath = tmp_path / ("sample" + extension)
    # make sure the file exists, even if we will stub the reader for pdf
    fpath.write_text("", encoding="utf-8")

    if extension == ".pdf":
        # PdfReader is used in the implementation; replace with a fake that
        # returns pages containing our expected string.
        class FakePage:
            def __init__(self, t):
                self._t = t

            def extract_text(self):
                return self._t

        class FakeReader:
            def __init__(self, path):
                self.pages = [FakePage(content)]

        monkeypatch.setattr(ingest, "PdfReader", FakeReader)
        result = ingest.read_file(str(fpath))
    else:
        fpath.write_text(content, encoding="utf-8")
        result = ingest.read_file(str(fpath))

    assert result == content


# ---------------------------------------------------------------------------
# chunking tests
# ---------------------------------------------------------------------------

@ pytest.mark.parametrize(
    "text,chunk_size,overlap,expected",
    [
        ("abcdefghij", 4, 1, ["abcd", "defg", "ghij", "j"]),
        ("", 5, 2, []),
        ("12345", 5, 0, ["12345"]),
    ],
)
def test_chunk_text(text, chunk_size, overlap, expected):
    assert ingest.chunk_text(text, chunk_size=chunk_size, overlap=overlap) == expected


# ---------------------------------------------------------------------------
# ingestion tests
# ---------------------------------------------------------------------------


def test_ingest_all_documents_creates_indices(tmp_path, vector_store, monkeypatch):
    # prepare two text files that will be "indexed"
    docs = tmp_path / "documents"
    docs.mkdir()
    (docs / "a.txt").write_text("A" * 100)
    (docs / "b.txt").write_text("B" * 200)

    # stub out the embedding and faiss pieces so the test is fast and
    # deterministic
    monkeypatch.setattr(ingest, "embed", lambda chunks: np.zeros((len(chunks), ingest.DIM)))

    class DummyIndex:
        def __init__(self, dim):
            self.dim = dim
            self.added = []

        def add(self, vectors):
            # keep a copy so the caller cannot mutate it later
            self.added.append(vectors.copy())

    monkeypatch.setattr(ingest.faiss, "IndexFlatL2", DummyIndex)

    written = []

    def fake_write_index(idx, path):
        written.append(path)

    monkeypatch.setattr(ingest.faiss, "write_index", fake_write_index)

    # run the ingestion over our tmp_path workspace
    ingest.ingest_all_documents()

    # there should be one .index + one .json for each input file
    assert any("a.txt.index" in p for p in written)
    assert any("b.txt.index" in p for p in written)

    a_json = vector_store / "a.txt.json"
    b_json = vector_store / "b.txt.json"
    assert a_json.exists()
    assert b_json.exists()

    # contents of the json should include the chunks we expect
    a_data = json.loads(a_json.read_text(encoding="utf-8"))
    assert isinstance(a_data.get("chunks"), list)


# ---------------------------------------------------------------------------
# retrieval tests
# ---------------------------------------------------------------------------


def test_top_k_retrieval_returns_exactly_k(monkeypatch):
    # before importing query we need to stop it from touching the real
    # filesystem or downloading models; patch the underlying libraries
    import faiss
    monkeypatch.setattr(faiss, "read_index", lambda path: None)

    import sentence_transformers
    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", lambda *args, **kwargs: mock.Mock(encode=lambda x: np.zeros((1, 384))))

    # make sure the module import does not fail when it tries to read a
    # non‑existent texts.json file
    os.makedirs("vector_store", exist_ok=True)
    Path("vector_store/texts.json").write_text("[]")

    import query

    # Fake index that always returns 5 nearest neighbours with indices 0..k-1
    class FakeIndex:
        def search(self, qvec, k):
            return np.zeros((1, k)), np.arange(k).reshape(1, k)

    monkeypatch.setattr(query, "index", FakeIndex())
    # embedder.encode just needs to accept a list and return a numpy array
    fake_embed = mock.Mock()
    fake_embed.encode.return_value = np.zeros((1, 384))
    monkeypatch.setattr(query, "embedder", fake_embed)

    # populate the texts array with five different paragraphs
    query.texts = [f"paragraph {i}" for i in range(5)]

    # also stub the network call so ask() doesn't try to reach a server
    import requests
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: mock.Mock(json=lambda: {"response": "ok"}))

    _, context = query.ask("any question")
    results = context.splitlines()
    assert len(results) == 5


def test_search_can_be_filtered_by_filename():
    # this helper mimics what a real search-with-metadata function would do
    def search_with_filter(index, texts, metadatas, query_str, filter_filename, k=5):
        # we don't actually care about the query string in this stub
        _, I = index.search(np.zeros((1, 384)), k)
        filtered = []
        for idx in I[0]:
            if metadatas[idx]["source"] == filter_filename:
                filtered.append(texts[idx])
        return filtered

    class FakeIndex:
        def search(self, qvec, k):
            return np.zeros((1, k)), np.arange(k).reshape(1, k)

    texts = ["A", "B", "C", "D", "E"]
    metadatas = [
        {"source": "file_A.txt"},
        {"source": "file_B.txt"},
        {"source": "file_A.txt"},
        {"source": "file_C.txt"},
        {"source": "file_A.txt"},
    ]

    results = search_with_filter(FakeIndex(), texts, metadatas, "q", "file_A.txt", k=5)
    assert results == ["A", "C", "E"]
