from enterprise_rag.config import load_config


def test_handbook_sample_within_brief_range():
    total = sum(s.pages for s in load_config().handbook.sections)
    assert 150 <= total <= 300


def test_every_department_section_maps_to_a_declared_role():
    cfg = load_config()
    for s in cfg.handbook.sections:
        assert s.role is None or s.role in cfg.roles
    assert [s.name for s in cfg.handbook.sections if s.role is None] == ["general"]


def test_handbook_folders_do_not_overlap_between_sections():
    folders = [f for s in load_config().handbook.sections for f in s.folders]
    assert len(folders) == len(set(folders))
