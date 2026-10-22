import pytest

from enterprise_rag.data import DocumentRecord, allowed_roles_for, read_manifest, write_manifest


def _rec(doc_id, source):
    return DocumentRecord(doc_id, source, f"{doc_id}.md", "t", None, "x", ("c_level",), "l", "h")


def test_department_docs_visible_to_owner_and_superuser_only(cfg):
    assert allowed_roles_for("legal", cfg) == ("c_level", "legal")


def test_general_docs_visible_to_every_role(cfg):
    assert set(allowed_roles_for(None, cfg)) == set(cfg.roles)


def test_write_manifest_replaces_only_requested_source(tmp_path):
    path = tmp_path / "manifest.jsonl"
    write_manifest(path, [_rec("a", "handbook"), _rec("b", "sec")], {"handbook", "sec"})
    write_manifest(path, [_rec("c", "sec")], {"sec"})
    assert [r.doc_id for r in read_manifest(path)] == ["a", "c"]


def test_write_manifest_rejects_duplicate_ids(tmp_path):
    with pytest.raises(ValueError):
        write_manifest(tmp_path / "m.jsonl", [_rec("a", "sec"), _rec("a", "sec")], {"sec"})
