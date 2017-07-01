from odooku.patch import HardPatch


class patch_lru(HardPatch):

    @staticmethod
    def apply_patch():
        from odooku.tools.lru import LRU
        return dict({
            'LRU': LRU
        })


patch_lru('odoo.tools.lru')
