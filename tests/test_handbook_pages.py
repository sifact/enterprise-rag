import pytest

from enterprise_rag.data.handbook_pages import (
    eligible_pages,
    page_url,
    parse_page,
    prose_word_count,
    sample_pages,
)


def _write(root, rel, body, title="T"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\ntitle: {title}\n---\n{body}")
    return p


def test_word_count_ignores_shortcodes_html_and_link_targets():
    body = "Hello world {{< youtube abc def >}} <div class='x'>two</div> [link](https://a.b/c/d)"
    assert prose_word_count(body) == 4  # Hello, world, two, link


def test_parse_page_reads_title_from_front_matter(tmp_path):
    page = parse_page(_write(tmp_path, "eng/a.md", "one two three", title="Alpha"), tmp_path)
    assert (page.rel_path, page.title, page.word_count) == ("eng/a.md", "Alpha", 3)


@pytest.mark.parametrize("rel,url", [
    ("engineering/foo.md", "https://handbook.gitlab.com/handbook/engineering/foo/"),
    ("engineering/_index.md", "https://handbook.gitlab.com/handbook/engineering/"),
    ("engineering/reindex.md", "https://handbook.gitlab.com/handbook/engineering/reindex/"),
])
def test_page_url(rel, url):
    assert page_url(rel) == url


def test_eligible_pages_filters_stubs(tmp_path):
    _write(tmp_path, "eng/long.md", "word " * 50)
    _write(tmp_path, "eng/stub.md", "word " * 5)
    assert [p.rel_path for p in eligible_pages(tmp_path, ("eng",), 10)] == ["eng/long.md"]


def test_sampling_is_deterministic_and_seed_dependent(tmp_path):
    for i in range(30):
        _write(tmp_path, f"eng/p{i:02d}.md", "word " * 20)
    pool = eligible_pages(tmp_path, ("eng",), 10)
    a = sample_pages(pool, 10, seed=42, section="eng")
    assert a == sample_pages(pool, 10, seed=42, section="eng")
    assert a != sample_pages(pool, 10, seed=7, section="eng")


def test_sampling_fails_when_section_too_small(tmp_path):
    _write(tmp_path, "eng/a.md", "word " * 20)
    with pytest.raises(ValueError, match="eligible"):
        sample_pages(eligible_pages(tmp_path, ("eng",), 10), 5, seed=1, section="eng")
