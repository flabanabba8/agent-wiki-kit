"""Offline checks for the image/context boundary. Run: python3 -m unittest discover -s this_directory -p test_image_workers.py"""
import subprocess
import sys
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from PIL import Image
import vision_inspect
import image_reference_generate
REAL_RUN = subprocess.run

class ImageWorkersTest(unittest.TestCase):

    def setUp(self):
        self.backend_patch = patch.dict(os.environ, {'VISION_BACKEND': 'codex'})
        self.backend_patch.start()
        self.addCleanup(self.backend_patch.stop)
        self.state = tempfile.TemporaryDirectory()
        self.addCleanup(self.state.cleanup)
        self.state_patch = patch('vision_inspect.STATE', Path(self.state.name))
        self.state_patch.start()
        self.addCleanup(self.state_patch.stop)
        self.metrics_patch = patch('vision_metrics.STATE', Path(self.state.name))
        self.metrics_patch.start()
        self.addCleanup(self.metrics_patch.stop)

    @patch.dict(os.environ, {'VISION_WORKER_DROP_ENV_PREFIXES': 'HOSTAPP_', 'HOSTAPP_SESSION': 'abc'})
    def test_inspection_compresses_and_returns_only_text(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.png'
            Image.effect_noise((800, 600), 50).save(source)
            original = source.read_bytes()
            workdirs = []

            def fake_run(command, **kwargs):
                if command[0] != 'codex':
                    return REAL_RUN(command, **kwargs)
                for flag in ('--ephemeral', '--ignore-user-config', '--sandbox'):
                    self.assertIn(flag, command)
                self.assertEqual(command[command.index('--sandbox') + 1], 'read-only')
                self.assertEqual(command[-2], '--')
                self.assertEqual(kwargs['stdout'], subprocess.PIPE)
                self.assertNotIn('HOSTAPP_SESSION', kwargs['env'])
                self.assertIn('HOME', kwargs['env'])
                work = Path(command[command.index('--cd') + 1])
                workdirs.append(work)
                previews = list(work.glob('image-*.jpg'))
                self.assertEqual(len(previews), 2)
                self.assertTrue(all((p.stat().st_size <= 50000 for p in previews)))
                Path(command[command.index('--output-last-message') + 1]).write_text('Two images: edges look correct.')
                return subprocess.CompletedProcess(command, 0)
            with patch('subprocess.run', side_effect=fake_run):
                report = vision_inspect.inspect_images([source, source], 'Check edges', model='test-model', backend='codex')
            self.assertEqual(report, 'Two images: edges look correct.')
            self.assertEqual(source.read_bytes(), original)
            self.assertFalse(workdirs[0].exists())
            with self.assertRaises(ValueError):
                vision_inspect.inspect_images([source] * 5, 'Check', backend='codex')

    def test_generation_preserves_references_and_returns_only_path(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'reference.png'
            output = Path(directory) / 'output.png'
            Image.new('RGBA', (16, 16), (0, 255, 0, 100)).save(source)
            original = source.read_bytes()
            workdirs = []

            def fake_run(command, **kwargs):
                self.assertIn('--ephemeral', command)
                self.assertEqual(command[command.index('--sandbox') + 1], 'workspace-write')
                self.assertEqual(kwargs['stdout'], subprocess.PIPE)
                work = Path(command[command.index('--cd') + 1])
                workdirs.append(work)
                self.assertEqual((work / 'reference-1.png').read_bytes(), original)
                Image.new('RGBA', (32, 32), (255, 0, 0, 255)).save(work / 'generated.png')
                return subprocess.CompletedProcess(command, 0)
            with patch('subprocess.run', side_effect=fake_run), patch('image_reference_generate.inspect_images', return_value='VERDICT: PASS\nMatches the reference.') as reviewer:
                result = image_reference_generate.generate(output, 'Use the reference', [source], model='test-model')
            self.assertEqual(result['image'], str(output))
            self.assertEqual(result['verdict'], 'PASS')
            self.assertTrue(reviewer.call_args.kwargs['refresh'])
            self.assertEqual(reviewer.call_args.kwargs['backend'], 'codex')
            self.assertEqual(reviewer.call_args.kwargs['model'], 'test-model')
            self.assertEqual(json.loads(Path(result['review']).read_text())['verdict'], 'PASS')
            self.assertTrue(output.exists())
            self.assertFalse(workdirs[0].exists())
            with self.assertRaises(ValueError):
                image_reference_generate.generate(output, 'Do not overwrite', [source])

    def test_cache_hits_and_invalidates(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.png'
            Image.new('RGB', (8, 8), 'red').save(source)
            calls = []

            def fake_run(command, **kwargs):
                if command[0] != 'codex':
                    return REAL_RUN(command, **kwargs)
                calls.append(command)
                Path(command[command.index('--output-last-message') + 1]).write_text('Visible red square.')
                return subprocess.CompletedProcess(command, 0)
            with patch('subprocess.run', side_effect=fake_run):
                for _ in range(2):
                    vision_inspect.inspect_images([source], 'Check', model='test', backend='codex')
                self.assertEqual(len(calls), 1)
                Image.new('RGB', (8, 8), 'blue').save(source)
                vision_inspect.inspect_images([source], 'Check', model='test', backend='codex')
                vision_inspect.inspect_images([source], 'Another question', model='test', backend='codex')
                vision_inspect.inspect_images([source], 'Another question', model='test', criteria='Blue', backend='codex')
                vision_inspect.inspect_images([source], 'Another question', model='other', criteria='Blue', backend='codex')
                vision_inspect.inspect_images([source], 'Another question', model='other', criteria='Blue', refresh=True, backend='codex')
                self.assertEqual(len(calls), 6)

    def test_failed_review_never_accepts_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'output.png'

            def fake_run(command, **kwargs):
                work = Path(command[command.index('--cd') + 1])
                Image.new('RGB', (8, 8), 'red').save(work / 'generated.png')
                return subprocess.CompletedProcess(command, 0)
            with patch('subprocess.run', side_effect=fake_run), patch('image_reference_generate.inspect_images', side_effect=ValueError('bad report')):
                result = image_reference_generate.generate(output, 'Test', model='test')
            self.assertEqual(result['verdict'], 'UNCERTAIN')
            self.assertTrue(output.exists())
            self.assertIn('error', json.loads(Path(result['review']).read_text()))

    def test_worker_isolated_generation_enabled(self):
        command = vision_inspect.codex_command('/tmp/test', '/tmp/test/answer', model='test', generation=True)
        self.assertIn('--ephemeral', command)
        self.assertIn('skip_host_skill_discovery', command)
        self.assertIn(['--enable', 'image_generation'], [command[i:i + 2] for i in range(len(command) - 1)])

    def test_inspection_rejects_embedded_images_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.png'
            Image.new('RGB', (8, 8)).save(source)
            workdirs = []

            def fake_run(command, **kwargs):
                if command[0] != 'codex':
                    return REAL_RUN(command, **kwargs)
                workdirs.append(Path(command[command.index('--cd') + 1]))
                Path(command[command.index('--output-last-message') + 1]).write_text('data:image/png;base64,bad')
                return subprocess.CompletedProcess(command, 0)
            with patch('subprocess.run', side_effect=fake_run), self.assertRaises(ValueError):
                vision_inspect.inspect_images([source], 'Check', model='test-model', backend='codex')
            self.assertFalse(workdirs[0].exists())
if __name__ == '__main__':
    unittest.main()
