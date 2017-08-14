import importlib
import pkgutil

from . patch import SoftPatch, HardPatch, patcher

def apply_patches():
    import odooku_patches
    for importer, name, ispkg in pkgutil.iter_modules(odooku_patches.__path__):
        module = importlib.import_module('%s.%s' % (odooku_patches.__name__, name))