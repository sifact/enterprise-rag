from enterprise_rag.evaluation import (
    Evidence,
    chunk_is_relevant,
    normalize_text,
    quote_in_text,
    quote_match_score,
)

QUOTE = " ".join(f"word{i}" for i in range(40))


def test_exact_quote_scores_one():
    text = "Some intro. " + QUOTE + " Some outro."
    assert quote_match_score(QUOTE, text) == 1.0


def test_match_ignores_markdown_and_pdf_artifacts():
    text = "The **Total** revenue was $955 mil-\nlion, per [the report](http://x)."
    quote = "The Total revenue was $955 million, per the report."
    assert quote_match_score(quote, text) >= 0.95


def test_normalize_maps_smart_quotes_and_nbsp():
    assert normalize_text("It’s “fine”") == normalize_text("It's \"fine\"")


def test_partial_chunk_covering_most_of_quote_matches():
    words = QUOTE.split()
    chunk = " ".join(words[:34])  # 85% of the quote; the chunk boundary cut the rest
    assert quote_in_text(QUOTE, chunk, threshold=0.80)
    assert not quote_in_text(QUOTE, chunk, threshold=0.90)


def test_tiny_chunk_inside_quote_is_not_relevant():
    chunk = " ".join(QUOTE.split()[:6])
    assert not quote_in_text(QUOTE, chunk, threshold=0.80)


def test_wrong_doc_never_relevant():
    gold = [Evidence("handbook:eng", QUOTE)]
    assert chunk_is_relevant("handbook:eng", QUOTE, gold, 0.8)
    assert not chunk_is_relevant("handbook:legal", QUOTE, gold, 0.8)
