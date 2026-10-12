#!/usr/bin/env python3
"""Check local prerequisites without uploading images or making a model request."""
import importlib.util
import json
import shutil
import subprocess
import sys

REQUIRED_FEATURES = {'hooks', 'plugins', 'view_image', 'shell_tool', 'image_generation', 'skip_host_skill_discovery'}
REQUIRED_OPTIONS = {'--ephemeral', '--ignore-user-config', '--output-last-message', '--image'}


def check():
    result = {'python_compatible': sys.version_info >= (3, 11),
              'pillow_available': importlib.util.find_spec('PIL') is not None,
              'codex_available': shutil.which('codex') is not None}
    if result['codex_available']:
        try:
            features = subprocess.run(['codex', 'features', 'list'], capture_output=True, text=True, timeout=10)
            names = {line.split()[0] for line in features.stdout.splitlines() if line.split()}
            help_text = subprocess.run(['codex', 'exec', '--help'], capture_output=True, text=True, timeout=10)
            result['missing_features'] = sorted(REQUIRED_FEATURES - names)
            result['missing_options'] = sorted(option for option in REQUIRED_OPTIONS if option not in help_text.stdout)
            result['cli_compatible'] = features.returncode == help_text.returncode == 0 and not result['missing_features'] and not result['missing_options']
            login = subprocess.run(['codex', 'login', 'status'], capture_output=True, timeout=10)
            result['codex_authenticated'] = login.returncode == 0
        except (OSError, subprocess.SubprocessError):
            result['cli_compatible'] = False
    result['ready'] = all(result.get(key, False) for key in
                          ('python_compatible', 'pillow_available', 'codex_available', 'cli_compatible', 'codex_authenticated'))
    return result


if __name__ == '__main__':
    result = check()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['ready'] else 1)
