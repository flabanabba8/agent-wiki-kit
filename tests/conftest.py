import importlib.util, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name, relpath):
    """Import a script that isn't a package module (e.g. scripts/hooks/*.py)."""
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, relpath))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
