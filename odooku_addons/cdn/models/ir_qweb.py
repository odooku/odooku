# -*- coding: utf-8 -*-

import ast

import odoo
from odoo import models, tools, SUPERUSER_ID
from odoo.http import request
from odoo.addons.base.ir.ir_qweb.assetsbundle import AssetsBundle

from odooku.backends import get_backend
from odooku.params import params

CDN_ENABLED = getattr(params, 'CDN_ENABLED', False)
s3_backend = get_backend('s3')


class IrQWeb(models.AbstractModel):

    _inherit = 'ir.qweb'

    CDN_TRIGGERS = {
        'link':    'href',
        'script':  'src',
        'img':     'src',
    }

    def _cdn_url(self, url):
        parts = url.split('/')
        cr, env = request.cr, request.env
        if url.startswith('/web/content/'):
            IrAttachment = env['ir.attachment']
            attachments = IrAttachment.search([('url', '=like', url)])
            if attachments:
                # /filestore/<dbname/<attachment>
                url = s3_backend.get_url('filestore', cr.dbname, attachments[0].store_fname)
        elif len(parts) > 3 and parts[2] == 'static':
            # /<module>/static
            url = s3_backend.get_url(url[1:])

        return url

    def _cdn_build_attribute(self, tagName, name, value, options, values):
        return self._cdn_url(value)

    def _wrap_cdn_build_attributes(self, el, items, options):
        if (options.get('rendering_bundle')
                or not CDN_ENABLED
                or not s3_backend
                or el.tag not in self.CDN_TRIGGERS):
            # Shortcircuit
            return items

        cdn_att = self.CDN_TRIGGERS.get(el.tag)
        def process(item):
            if isinstance(item, tuple) and item[0] == cdn_att:
                return (item[0], ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id='self', ctx=ast.Load()),
                        attr='_cdn_build_attribute',
                        ctx=ast.Load()
                    ),
                    args=[
                        ast.Str(el.tag),
                        ast.Str(item[0]),
                        item[1],
                        ast.Name(id='options', ctx=ast.Load()),
                        ast.Name(id='values', ctx=ast.Load()),
                    ], keywords=[],
                    starargs=None, kwargs=None
                ))
            else:
                return item

        return list(map(process, items))

    def _compile_static_attributes(self, el, options):
        items = super(IrQWeb, self)._compile_static_attributes(el, options)
        return self._wrap_cdn_build_attributes(el, items, options)

    def _compile_dynamic_attributes(self, el, options):
        items = super(IrQWeb, self)._compile_dynamic_attributes(el, options)
        return self._wrap_cdn_build_attributes(el, items, options)

    def _get_dynamic_att(self, tagName, atts, options, values):
        atts = super(IrQWeb, self)._get_dynamic_att(tagName, atts, options, values)
        if (options.get('rendering_bundle')
                or not CDN_ENABLED
                or not s3_backend
                or tagName not in self.CDN_TRIGGERS):
            # Shortcircuit
            return atts

        for name, value in atts.items():
            atts[name] = self._cdn_build_attribute(tagName, name, value, options, values)
        return atts

    def _is_static_node(self, el):
        cdn_att = self.CDN_TRIGGERS.get(el.tag, False)
        return super(IrQWeb, self)._is_static_node(el) and \
                (not cdn_att or not el.get(cdn_att))

    def _get_asset(self, xmlid, options, css=True, js=True, debug=False, async=False, values=None):
        # Commit_assetsbundle is assigned when rendering a pdf.
        # We use it to distinguish between web and pdf report asset url's.
        # hackish !!
        if CDN_ENABLED and s3_backend and not options.get('commit_assetsbundle'):
            values = dict(values or {}, url_for=self._cdn_url)
        html = super(IrQWeb, self)._get_asset(xmlid, options, css, js, debug, async, values)
        # This fixes web editor widgets using cssRules
        # TODO Make this configurable
        html = html.replace('<link', '<link crossorigin="anonymous"')
        return html
