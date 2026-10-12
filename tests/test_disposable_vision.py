"""Collect the bundled offline worker tests without an authenticated model call."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parents[1] / '.claude/skills/disposable-vision/tests/test_image_workers.py'
_spec = importlib.util.spec_from_file_location('disposable_vision_tests', _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
ImageWorkersTest = _module.ImageWorkersTest


def test_portable_install_is_idempotent_and_preserves_existing_files(tmp_path):
    from conftest import load
    installer = load('vision_skill_installer_test', 'scripts/agents/install-vision-skill.py')
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'SKILL.md').write_text('test skill')
    targets = [tmp_path / name / 'skill' for name in ('claude', 'codex', 'hermes')]
    installer.install(source, targets, dry_run=True)
    assert not any(p.exists() for p in targets)
    installer.install(source, targets)
    installer.install(source, targets)
    assert all((p / 'SKILL.md').read_text() == 'test skill' for p in targets)
    (targets[1] / 'SKILL.md').write_text('user changes')
    import pytest
    with pytest.raises(ValueError, match='refusing to overwrite'):
        installer.install(source, targets)
    assert (targets[1] / 'SKILL.md').read_text() == 'user changes'


def test_environment_check_reports_missing_codex_without_model_calls(monkeypatch):
    from conftest import load
    checker = load('vision_environment_test', '.claude/skills/disposable-vision/scripts/check_environment.py')
    monkeypatch.setattr(checker.shutil, 'which', lambda _: None)
    monkeypatch.setattr(checker.subprocess, 'run', lambda *a, **k: (_ for _ in ()).throw(AssertionError('unexpected process')))
    assert checker.check()['ready'] is False
