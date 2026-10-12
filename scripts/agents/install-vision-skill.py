#!/usr/bin/env python3
"""Install the bundled image-worker skill into user skill directories.

No credentials or global instructions are changed. Existing differing copies are
never overwritten. Use --dry-run to inspect destinations without writing.
"""
import argparse
import os
from pathlib import Path
import shutil

SOURCE = Path(__file__).resolve().parents[2] / '.claude/skills/disposable-vision'


def files(root):
    return {p.relative_to(root): p.read_bytes() for p in root.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}


def install(source, destinations, dry_run=False):
    expected = files(source)
    if Path('SKILL.md') not in expected:
        raise ValueError('Source is not a skill bundle')
    for dest in destinations:
        if dest.exists() and (not dest.is_dir() or files(dest) != expected):
            raise ValueError(f'Existing skill differs; refusing to overwrite: {dest}')
    for dest in destinations:
        if dest.exists():
            print(f'Already installed: {dest}')
        elif dry_run:
            print(f'Would install: {dest}')
        else:
            shutil.copytree(source, dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            print(f'Installed: {dest}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill', choices=['disposable-vision','disposable-tasks','all'], default='disposable-vision')
    parser.add_argument('--agent', choices=['claude', 'codex', 'hermes', 'all'], default='all')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    home = Path.home()
    roots = {'claude': home / '.claude/skills',
             'codex': Path(os.environ.get('CODEX_HOME', str(home / '.codex'))) / 'skills',
             'hermes': Path(os.environ.get('HERMES_HOME', str(home / '.hermes'))) / 'skills/creative'}
    names = roots if args.agent == 'all' else [args.agent]
    try:
        skills = ['disposable-vision','disposable-tasks'] if args.skill == 'all' else [args.skill]
        for skill in skills:
            install(SOURCE.parent / skill, [roots[name] / skill for name in names], args.dry_run)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'{exc}\n')


if __name__ == '__main__':
    main()
