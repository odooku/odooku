import sys
import importlib
from importlib.machinery import PathFinder
from types import FunctionType, ModuleType


class SoftPatch(object):

    def __init__(self, module_name):
        self.module_name = module_name
        patcher._register(module_name, self)

    @staticmethod
    def apply_patch():
        return {}


class HardPatch(object):

    def __init__(self, module_name):
        self.module_name = module_name
        patcher._register(module_name, self)
    
    @staticmethod
    def apply_patch():
        return {}


# https://github.com/python/cpython/blob/3.6/Lib/importlib/_bootstrap_external.py
# look at this 

class SoftPatchLoader(object):
    
    patches = None

    def exec_module(self, module):
        super(SoftPatchLoader, self).exec_module(module)
        for patch in self.patches:
            apply_patch = FunctionType(patch.apply_patch.__code__, module.__dict__)
            module.__dict__.update(apply_patch())


class HardPatchLoader(object):
    
    patch = None

    def exec_module(self, module):
        apply_patch = FunctionType(self.patch.apply_patch.__code__, dict(globals(), **module.__dict__))
        module.__dict__.update(apply_patch())
    
    def create_module(self, spec):
        return ModuleType(self.patch.module_name)


class Patcher(object):

    def __init__(self):
        self._soft_patch_loaders = {}
        self._hard_patch_loaders = {}
        self._soft_patches = {}
        self._hard_patches = {}

    def _register(self, fullname, patch):
        if isinstance(patch, SoftPatch):
            if fullname not in self._soft_patches:
                self._soft_patches[fullname] = []
            self._soft_patches[fullname].append(patch)
        elif isinstance(patch, HardPatch):
            self._hard_patches[fullname] = patch
        else:
            raise TypeError(type(patch))

    def _wrap_soft_patches(self, loader, patches):
        loader_cls = type(loader)
        if loader_cls not in self._soft_patch_loaders:
            self._soft_patch_loaders[loader_cls] = type('Patch%s' % loader_cls.__name__, (SoftPatchLoader, loader_cls,), {})
        loader.__class__ = self._soft_patch_loaders[loader_cls]
        loader.patches = patches

    def _wrap_hard_patch(self, loader, patch):
        loader_cls = type(loader)
        if loader_cls not in self._hard_patch_loaders:
            self._hard_patch_loaders[loader_cls] = type('Patch%s' % loader_cls.__name__, (HardPatchLoader, loader_cls,), {})
        loader.__class__ = self._hard_patch_loaders[loader_cls]
        loader.patch = patch

    def find_spec(self, fullname, path, target=None):
        spec = None
        if fullname in self._soft_patches or fullname in self._hard_patches:
            spec = PathFinder.find_spec(fullname, path, target=target)
            if spec is None:
                raise Exception("Could not patch %s" % fullname)
            
            if fullname in self._soft_patches:
                self._wrap_soft_patches(spec.loader, self._soft_patches[fullname])
            elif fullname in self._hard_patches:
                self._wrap_hard_patch(spec.loader, self._hard_patches[fullname])
            
        return spec
            
patcher = Patcher()
sys.meta_path.insert(0, patcher)
