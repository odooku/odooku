import sys
import importlib
from types import FunctionType, ModuleType


class SoftPatch(object):

    def __init__(self, module_name):
        self.module_name = module_name
        patcher._register(module_name, self)

    def _apply_patch(self, module):
        apply_patch = FunctionType(self.apply_patch.func_code, module.__dict__)
        module.__dict__.update(apply_patch())

    @staticmethod
    def apply_patch():
        return {}


class HardPatch(object):

    def __init__(self, module_name):
        self.module_name = module_name
        patcher._register(module_name, self)

    def _create_module(self):
        module = ModuleType(self.module_name)
        apply_patch = FunctionType(self.apply_patch.func_code, dict(globals(), **module.__dict__))
        module.__dict__.update(apply_patch())
        return module

    @staticmethod
    def apply_patch():
        return {}


class Patcher(object):

    def __init__(self):
        self._patch = {}
        self._soft_patches = {}
        self._hard_patches = {}
        self._loaded = {}
        self._loading = {}

    def _register(self, module_name, patch):
        if isinstance(patch, SoftPatch):
            if module_name not in self._soft_patches:
                self._soft_patches[module_name] = []
            self._soft_patches[module_name].append(patch)
        elif isinstance(patch, HardPatch):
            self._hard_patches[module_name] = patch
        else:
            raise TypeError(type(patch))

        self._patch[module_name] = True

    def find_module(self, module_name, path=None):
        if self._patch.get(module_name, False):
            return self

    def load_module(self, module_name):
        if module_name not in self._loaded:
            hard_patch = self._hard_patches.get(module_name, None)
            if hard_patch:
                module = hard_patch._create_module()
                sys.modules[module_name] = module
            else:
                # Before actually importing, we have to bypass our
                # find_module function.
                self._patch[module_name] = False
                module = importlib.import_module(module_name)
                self._patch[module_name] = True

            # Apply soft patches the module
            for patch in self._soft_patches.get(module_name, []):
                patch._apply_patch(module)

            self._loaded[module_name] = module

        return self._loaded[module_name]


patcher = Patcher()
sys.meta_path.append(patcher)
