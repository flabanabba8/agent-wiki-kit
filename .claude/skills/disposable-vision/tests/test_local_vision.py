"""Offline checks for stateless local requests, cache isolation and fail-closed behavior."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import local_vision
import vision_inspect


class LocalVisionTest(unittest.TestCase):
    def setUp(self):
        self.config_patch = patch('local_vision.local_config', return_value={})
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)

    def test_router_key_stays_private_and_is_not_sent_to_another_endpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            key = Path(directory)/'router.key';key.write_text('test-router-key');key.chmod(0o600)
            config={'endpoint':'http://127.0.0.1:20128','api_key_file':str(key)}
            with patch('local_vision.local_config',return_value=config):
                self.assertEqual(local_vision.auth_headers(config['endpoint']),{'Authorization':'Bearer test-router-key'})
                self.assertEqual(local_vision.auth_headers('http://127.0.0.1:8081'),{})
                key.chmod(0o644)
                with self.assertRaises(ValueError):local_vision.auth_headers(config['endpoint'])

    def test_configured_model_is_selected_without_picking_a_cloud_model(self):
        config={'endpoint':'http://127.0.0.1:20128','model':'example/local-test'}
        with patch('local_vision.local_config',return_value=config),patch('local_vision.request_json',return_value={'data':[{'id':'cloud-model'},{'id':'example/local-test'}]}):
            self.assertEqual(local_vision.resolve_local()[1],'example/local-test')

    def test_default_inspection_does_not_start_an_agent(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'source.png';Image.new('RGB',(16,16)).save(source)
            with patch('local_vision.resolve_local',side_effect=RuntimeError('Local selected')), patch('vision_inspect.codex_command') as codex:
                with self.assertRaisesRegex(RuntimeError,'Local selected'):
                    vision_inspect.inspect_images([source],'Provider routing')
                codex.assert_not_called()

    def test_request_is_stateless_bounded_and_caches_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.png'
            Image.new('RGB', (160, 100), 'blue').save(source)
            requests = []

            def respond(endpoint, route, payload=None, timeout=120):
                if route == '/v1/models':
                    return {'data': [{'id': 'local-test'}]}
                self.assertEqual(route, '/v1/chat/completions')
                requests.append(payload)
                self.assertEqual([m['role'] for m in payload['messages']], ['system', 'user'])
                self.assertNotIn('tools', payload)
                self.assertNotIn('previous_response_id', payload)
                self.assertEqual(payload['max_tokens'], 512)
                self.assertFalse(payload['chat_template_kwargs']['enable_thinking'])
                self.assertLess(len(payload['messages'][0]['content']), 400)
                return {'choices': [{'message': {'content': 'VERDICT: PASS\nBlue image.'},
                                     'finish_reason': 'stop'}],
                        'usage': {'prompt_tokens': 600, 'completion_tokens': 12,
                                  'total_tokens': 612, 'prompt_tokens_details': {'cached_tokens': 20}}}

            with patch('local_vision.request_json', side_effect=respond), \
                 patch('vision_inspect.STATE', root / 'state'), \
                 patch('vision_metrics.STATE', root / 'state'), \
                 patch('vision_inspect.codex_command') as codex:
                first = vision_inspect.inspect_images([source], 'What color?', backend='local')
                second = vision_inspect.inspect_images([source], 'What color?', backend='local')
                self.assertEqual(first, second)
                self.assertEqual(len(requests), 1)
                codex.assert_not_called()
            rows = [json.loads(s) for s in (root / 'state/metrics.jsonl').read_text().splitlines()]
            self.assertEqual(rows[0]['prompt_tokens'], 600)
            self.assertEqual(rows[0]['cached_input_tokens'], 20)
            self.assertLessEqual(rows[0]['attachment_bytes'], 50000)
            self.assertTrue(rows[1]['cache_hit'])
            self.assertEqual(rows[1]['attachment_bytes'], 0)

    def test_failure_never_starts_codex(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.png'
            Image.new('RGB', (16, 16)).save(source)
            with patch('local_vision.request_json', side_effect=RuntimeError('Unavailable')), \
                 patch('vision_inspect.codex_command') as codex:
                with self.assertRaises(RuntimeError):
                    vision_inspect.inspect_images([source], 'Check', backend='local')
                codex.assert_not_called()

    def test_rejects_remote_endpoint_and_truncated_pass(self):
        for endpoint in ['https://example.com', 'http://user:secret@localhost:8081',
                         'http://127.0.0.1:8081/?key=secret']:
            with self.assertRaises(ValueError):
                local_vision.endpoint_url(endpoint)
        response = {'choices': [{'message': {'content': 'VERDICT: PASS'}, 'finish_reason': 'length'}]}
        with patch('local_vision.request_json', return_value=response):
            with self.assertRaises(ValueError):
                local_vision.inspect([], '', 'Check', '', endpoint='http://127.0.0.1:8081', model='local-test')

    def test_codex_usage_extraction_does_not_keep_payloads(self):
        events = '\n'.join([json.dumps({'type': 'item.completed', 'payload': 'irrelevant'}),
                            json.dumps({'type': 'turn.completed', 'usage': {
                                'input_tokens': 5000, 'cached_input_tokens': 3000, 'output_tokens': 80}})])
        self.assertEqual(vision_inspect.codex_usage(events), {
            'input_tokens': 5000, 'cached_input_tokens': 3000, 'output_tokens': 80})


if __name__ == '__main__':
    unittest.main()
