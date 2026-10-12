import argparse
import gzip
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from conftest import load

task = load('disposable_task_tests', '.claude/skills/disposable-tasks/scripts/task.py')


def args(path, **kw):
    values=dict(kind='logs',question='Find the failure',criteria='',files=[str(path)],root=None,
                pattern='',base='HEAD',image=[],model='test',timeout=30,refresh=False)
    values.update(kw)
    return argparse.Namespace(**values)


def test_logs_bound_context_preserve_locations(tmp_path):
    path=tmp_path/'run.log'
    path.write_text('routine output\n'*2000+'FATAL missing dependency\n'+'tail\n'*30)
    prepared,coverage=task.prepare('logs',[path],limit=1000)
    assert '2001: FATAL missing dependency' in prepared
    assert coverage[0]['partial'] and len(prepared)<1200


def test_csv_profile_numeric_missing_and_malformed(tmp_path):
    path=tmp_path/'data.csv';path.write_text('value,name\n1,A\n3,B\n,\n5\n')
    data,note=task.profile_data(path);data=json.loads(data)
    assert data['rows_profiled']==4 and data['malformed_rows']==1
    assert data['columns'][0]['mean']==3 and data['columns'][0]['missing']==1
    assert data['columns'][1]['missing']==2


def test_capture_failure_gzip_and_no_overwrite(tmp_path,capsys):
    path=tmp_path/'run.log'
    a=argparse.Namespace(command=[sys.executable,'-c','print("x"*100000); raise SystemExit(3)'],output=str(path),compress=True,timeout=None)
    assert task.capture(a)==3
    report=json.loads(capsys.readouterr().out)
    assert report['stored_bytes']<report['original_bytes']//10
    assert gzip.open(report['log'],'rt').read().startswith('x'*10)
    import pytest
    with pytest.raises(ValueError):task.capture(a)


def test_cached_worker_has_no_tools_and_receives_prompt_on_stdin(tmp_path,monkeypatch):
    monkeypatch.setattr(task,'STATE',tmp_path/'state')
    path=tmp_path/'input.log';path.write_text('ERROR failed\n')
    calls=[]
    def run(cmd,**kw):
        calls.append(cmd)
        assert cmd[-1]=='-' and 'ERROR' in kw['input']
        assert '--ephemeral' in cmd and 'skip_host_skill_discovery' in cmd
        assert 'web_search="disabled"' in cmd and 'shell_tool' in cmd
        answer=Path(cmd[cmd.index('--output-last-message')+1]);answer.write_text('Evidence: input.log:1 failed.')
        return subprocess.CompletedProcess(cmd,0)
    with patch.object(task.subprocess,'run',side_effect=run):
        first=task.analyze(args(path));second=task.analyze(args(path))
        assert not first['cache_hit'] and second['cache_hit'] and len(calls)==1
        path.write_text('ERROR different failure\n');task.analyze(args(path));assert len(calls)==2


def test_docx_extracts_body_without_images(tmp_path):
    import zipfile
    path=tmp_path/'document.docx'
    with zipfile.ZipFile(path,'w') as z:z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:t>Requirement A</w:t></w:r></w:p></w:document>')
    text,note=task.extract_document(path)
    assert 'Requirement A' in text and 'headers' in note


def test_rejects_embedded_image_report():
    import pytest
    with pytest.raises(ValueError):task.check_report('data:image/png;base64,AAAA')


def test_web_is_never_served_from_cache(tmp_path,monkeypatch):
    monkeypatch.setattr(task,'STATE',tmp_path/'cache')
    calls=[]
    def run(cmd,**kw):
        calls.append(cmd);assert 'web_search="live"' in cmd
        Path(cmd[cmd.index('--output-last-message')+1]).write_text('Finding with https://example.org/source')
        return subprocess.CompletedProcess(cmd,0)
    with patch.object(task.subprocess,'run',side_effect=run):
        for _ in range(2):task.analyze(args(None,kind='web',files=[]))
    assert len(calls)==2
