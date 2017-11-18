IGNORE_VARS = [
    '__doc__',
    '__module__',
    '__dict__',
    '__weakref__'
]

IGNORE_BASES = [
    object
]

def _safe_vars(obj):
    return { k: v for k, v in vars(obj).items() if k not in IGNORE_VARS}

def patch_class(cls):
    def decorated(patch):
        patched = _safe_vars(cls)
        for key, member in _safe_vars(patch).items():
            if key in patched:
                patched_key = '%s_' % key
                if hasattr(cls, patched_key):
                    raise Exception("Cannot patch %s, conflicting member %s" % (key, patched_key))
                patched[patched_key] = patched[key]

            patched[key] = member

        bases = [
            base for base in patch.__bases__
            if base not in IGNORE_BASES
        ]

        bases.extend(cls.__bases__)
        return type(cls.__name__, tuple(bases), patched)
    return decorated