import pandas as pd

from enterprise_rag.data import (
    DocumentRecord,
    load_doc_pages,
    load_fixture_pages,
    load_fixture_roles,
)


def rec(path: str) -> DocumentRecord:
    return DocumentRecord("d", "x", path, "t", None, "x", ("c_level",), "CC", "h")


def test_load_doc_pages_markdown_strips_front_matter(tmp_path):
    (tmp_path / "p.md").write_text("---\ntitle: Hi\n---\n\n## Body\n\nSome text.\n")
    pages = load_doc_pages(rec("p.md"), tmp_path)
    assert len(pages) == 1
    assert pages[0].page is None
    assert "title:" not in pages[0].text and "Some text." in pages[0].text


def test_load_doc_pages_xlsx_one_page_per_sheet(tmp_path):
    with pd.ExcelWriter(tmp_path / "w.xlsx") as xw:
        pd.DataFrame({"Dept": ["Sales"], "Cost": [100]}).to_excel(xw, sheet_name="A", index=False)
        pd.DataFrame({"Dept": ["Legal"], "Cost": [200]}).to_excel(xw, sheet_name="B", index=False)
    pages = load_doc_pages(rec("w.xlsx"), tmp_path)
    assert [p.page for p in pages] == [1, 2]
    assert "Sales,100" in pages[0].text and "Legal,200" in pages[1].text


def test_load_fixture_pages_ids_and_body(tmp_path):
    (tmp_path / "vendor-faq.md").write_text("---\nallowed_roles: [legal]\n---\nVendor body.\n")
    pages = load_fixture_pages(tmp_path)
    assert list(pages) == ["fixture:vendor-faq"]
    assert pages["fixture:vendor-faq"][0].text.strip() == "Vendor body."


def test_load_fixture_roles_from_front_matter(tmp_path):
    (tmp_path / "vendor-faq.md").write_text("---\nallowed_roles: [legal, c_level]\n---\nBody\n")
    assert load_fixture_roles(tmp_path) == {"fixture:vendor-faq": ("legal", "c_level")}
