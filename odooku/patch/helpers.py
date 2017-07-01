IGNORE_MEMBERS = [
    '__doc__',
    '__module__',
    '__dict__',
    '__weakref__'
]

IGNORE_BASES = [
    object
]

def patch_class(cls, only=None, keep=None):
    def decorated(patch):
        patched = dict(cls.__dict__)

        for key, member in dict(patch.__dict__).iteritems():
            if (key in IGNORE_MEMBERS
                    or only and key not in only
                    or keep and key in keep):
                continue

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
