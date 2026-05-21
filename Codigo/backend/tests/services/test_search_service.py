from unittest.mock import patch

import pytest

from app.services.search_service import _escape_lucene, _make_snippet, search


# ── _escape_lucene ────────────────────────────────────────────────────────


def test_escape_lucene_passes_through_safe_chars():
    assert _escape_lucene("redes neurais") == "redes neurais"


def test_escape_lucene_escapes_special_chars():
    raw = 'f(x) + "y" || z*'
    escaped = _escape_lucene(raw)
    assert escaped == 'f\\(x\\) \\+ \\"y\\" \\|\\| z\\*'


def test_escape_lucene_handles_empty_string():
    assert _escape_lucene("") == ""


# ── _make_snippet ─────────────────────────────────────────────────────────


def test_make_snippet_marks_term_with_bold():
    text = "As redes neurais convolucionais são amplamente usadas."
    snippet = _make_snippet(text, "redes neurais")
    assert "**redes**" in snippet or "**Redes**" in snippet


def test_make_snippet_centers_window_around_term():
    text = "a" * 200 + " ALVO " + "b" * 200
    snippet = _make_snippet(text, "ALVO", max_len=150)
    assert "**ALVO**" in snippet
    assert len(snippet) <= 150 + len("****") + 6  # marcadores + reticências


def test_make_snippet_prefixes_ellipsis_when_truncated_left():
    text = "x" * 100 + " termo " + "y" * 100
    snippet = _make_snippet(text, "termo", max_len=50)
    assert snippet.startswith("...")


def test_make_snippet_suffixes_ellipsis_when_truncated_right():
    text = "termo " + "y" * 200
    snippet = _make_snippet(text, "termo", max_len=50)
    assert snippet.endswith("...")


def test_make_snippet_returns_prefix_when_term_not_found():
    text = "qualquer texto sem o que buscamos aqui dentro"
    snippet = _make_snippet(text, "ausente", max_len=20)
    assert len(snippet) <= 23
    assert "**" not in snippet


def test_make_snippet_preserves_original_case_in_marker():
    text = "Redes Neurais são legais"
    snippet = _make_snippet(text, "redes")
    assert "**Redes**" in snippet


def test_make_snippet_handles_term_at_start():
    text = "Redes neurais convolucionais"
    snippet = _make_snippet(text, "redes", max_len=50)
    assert not snippet.startswith("...")
    assert "**Redes**" in snippet


def test_make_snippet_handles_term_at_end():
    text = "Aprendizado profundo com redes"
    snippet = _make_snippet(text, "redes", max_len=50)
    assert not snippet.endswith("...")
    assert "**redes**" in snippet


# ── search() ──────────────────────────────────────────────────────────────


def test_search_rejects_short_query():
    with pytest.raises(ValueError):
        search(user_uid="u1", query=" a ")


def test_search_rejects_empty_query():
    with pytest.raises(ValueError):
        search(user_uid="u1", query="")


def test_search_groups_pages_under_their_document():
    project = {"uid": "p1", "name": "Tese"}
    doc = {"uid": "d1", "title": "goodfellow.pdf", "status": "INDEXED"}
    page1 = {"uid": "pg1", "page_number": 234, "text": "redes neurais convolucionais ali"}
    page2 = {"uid": "pg2", "page_number": 412, "text": "outra menção a redes neurais aqui"}

    doc_rows = [
        (project, doc, page1, 4.2, ["DocumentPage"]),
        (project, doc, page2, 3.1, ["DocumentPage"]),
    ]

    with patch("app.services.search_service._run_doc_query", return_value=doc_rows), \
         patch("app.services.search_service._run_annotation_query", return_value=[]):
        resp = search(user_uid="u1", query="redes neurais")

    assert resp.total == 2
    assert len(resp.results_by_project) == 1
    pg = resp.results_by_project[0]
    assert pg.project.uid == "p1"
    assert len(pg.documents) == 1
    assert pg.documents[0].document.uid == "d1"
    assert len(pg.documents[0].page_hits) == 2
    page_numbers = {h.page_number for h in pg.documents[0].page_hits}
    assert page_numbers == {234, 412}


def test_search_document_title_match_goes_to_title_match_not_page_hits():
    project = {"uid": "p1", "name": "Tese"}
    doc = {"uid": "d1", "title": "redes neurais.pdf", "status": "INDEXED"}
    doc_rows = [(project, doc, doc, 5.0, ["Document"])]

    with patch("app.services.search_service._run_doc_query", return_value=doc_rows), \
         patch("app.services.search_service._run_annotation_query", return_value=[]):
        resp = search(user_uid="u1", query="redes")

    g = resp.results_by_project[0].documents[0]
    assert g.title_match is not None
    assert "**redes**" in g.title_match.snippet
    assert g.page_hits == []


def test_search_includes_annotation_extracted_text_hit():
    project = {"uid": "p1", "name": "Tese"}
    ann = {
        "uid": "a1", "title": "Resumo CNN",
        "extracted_text": "convolução com kernel 3x3 em redes neurais",
        "content": "", "status": "INDEXED",
    }
    ann_rows = [(project, None, ann, 3.0)]

    with patch("app.services.search_service._run_doc_query", return_value=[]), \
         patch("app.services.search_service._run_annotation_query", return_value=ann_rows):
        resp = search(user_uid="u1", query="redes neurais")

    pg = resp.results_by_project[0]
    assert len(pg.annotations) == 1
    assert pg.annotations[0].annotation.uid == "a1"
    assert "redes" in pg.annotations[0].snippet.lower()


def test_search_orders_by_score_globally_top_50():
    project = {"uid": "p1", "name": "Tese"}
    doc = {"uid": "d1", "title": "x.pdf", "status": "INDEXED"}
    doc_rows = [
        (project, doc, {"uid": f"pg{i}", "page_number": i, "text": f"hit {i}"}, 100 - i, ["DocumentPage"])
        for i in range(60)
    ]

    with patch("app.services.search_service._run_doc_query", return_value=doc_rows), \
         patch("app.services.search_service._run_annotation_query", return_value=[]):
        resp = search(user_uid="u1", query="hit", limit=50)

    assert resp.total == 50
    pages = resp.results_by_project[0].documents[0].page_hits
    assert len(pages) == 50
    assert pages[0].score >= pages[-1].score


def test_search_sanitizes_lucene_special_chars_in_query():
    captured = {}

    def fake_doc_query(escaped_query, user_uid):
        captured["q"] = escaped_query
        return []

    with patch("app.services.search_service._run_doc_query", side_effect=fake_doc_query), \
         patch("app.services.search_service._run_annotation_query", return_value=[]):
        search(user_uid="u1", query='f(x):"y"')

    # caracteres especiais devem aparecer escapados
    assert "\\(" in captured["q"]
    assert "\\)" in captured["q"]
    assert '\\"' in captured["q"]
    assert "\\:" in captured["q"]
