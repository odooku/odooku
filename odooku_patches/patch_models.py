from odooku.patch import SoftPatch


class patch_ensure_xml_id(SoftPatch):

    @staticmethod
    def apply_patch():

        def ensure_xml_id(self, skip=False):
            """ Create missing external ids for records in ``self``, and return an
                iterator of pairs ``(record, xmlid)`` for the records in ``self``.

            :rtype: Iterable[Model, str | None]
            """
            if skip:
                return ((record, None) for record in self)

            if not self:
                return iter([])

            if not self._is_an_ordinary_table():
                raise Exception(
                    "You can not export the column ID of model %s, because the "
                    "table %s is not an ordinary table."
                    % (self._name, self._table))

            modname = '__export__'

            cr = self.env.cr
            cr.execute("""
                SELECT res_id, module, name
                FROM ir_model_data
                WHERE model = %s AND res_id in %s
            """, (self._name, tuple(self.ids)))
            xids = {
                res_id: (module, name)
                for res_id, module, name in cr.fetchall()
            }
            def to_xid(record_id):
                (module, name) = xids[record_id]
                return ('%s.%s' % (module, name)) if module else name

            # create missing xml ids
            missing = self.filtered(lambda r: r.id not in xids)
            if not missing:
                return (
                    (record, to_xid(record.id))
                    for record in self
                )

            xids.update(
                (r.id, (modname, '%s_%s_%s' % (
                    r._table,
                    r.id,
                    uuid.uuid4().hex[:8],
                )))
                for r in missing
            )

            # Do not use cr.copy_from here
            # since it won't work with async
            for record in missing:
                self.env['ir.model.data'].sudo().create({
                    'module': modname,
                    'model': record._name,
                    'name': xids[record.id][1],
                    'res_id': record.id
                })


            return (
                (record, to_xid(record.id))
                for record in self
            )

        assert(hasattr(BaseModel, '_BaseModel__ensure_xml_id'))
        BaseModel._BaseModel__ensure_xml_id = ensure_xml_id
        return {}


patch_ensure_xml_id('odoo.models')