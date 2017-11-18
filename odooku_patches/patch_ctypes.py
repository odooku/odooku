import os
import os.path
import re
from odooku.patch import SoftPatch


# Ctypes won't find libraries inside a snap
# This will make sure pyusb (and any other ctypes) package works.

class patch_find_library(SoftPatch):

    @staticmethod
    def apply_patch():

        original_find_library = find_library
        def patched_find_library(name):
            regex = r'lib{name}\.[^\s]+'.format(name=re.escape(name))
            lib_root = os.path.join(os.environ.get('SNAP'), 'lib')
            for root, directories, files in os.walk(lib_root):
                for filename in files:
                    match = re.search(regex, filename)
                    if match:
                        return match.group(0)

            return original_find_library(name)

        return dict(find_library=patched_find_library)


if os.environ.get('SNAP'):
    patch_find_library('ctypes.util')