from odooku.patch import SoftPatch


class patch_http_request(SoftPatch):

    @staticmethod
    def apply_patch():

        from odooku.patch.helpers import patch_class
        from odooku.request import WebRequestMixin

        @patch_class(globals()['HttpRequest'])
        class HttpRequest(WebRequestMixin):
            pass

        return locals()


class patch_json_request(SoftPatch):

    @staticmethod
    def apply_patch():

        from odooku.patch.helpers import patch_class
        from odooku.request import WebRequestMixin

        @patch_class(globals()['JsonRequest'])
        class JsonRequest(WebRequestMixin):
            pass

        return locals()


class patch_root(SoftPatch):

    @staticmethod
    def apply_patch():

        from odooku.patch.helpers import patch_class
        from odooku.backends import get_backend
        from odooku.backends.redis import RedisSessionStore

        @patch_class(globals()['Root'])
        class Root(object):

            @lazy_property
            def session_store(self):
                redis = get_backend('redis')
                if redis:
                    _logger.info("HTTP Sessions stored in redis")
                    return RedisSessionStore(redis, session_class=OpenERPSession)
                else:
                    path = odoo.tools.config.session_dir
                    _logger.info("HTTP sessions stored locally in: %s", path)
                    return werkzeug.contrib.sessions.FilesystemSessionStore(path, session_class=OpenERPSession)

            def setup_session(self, httprequest):
                if isinstance(self.session_store, RedisSessionStore):
                    sid = httprequest.args.get('session_id')
                    explicit_session = True
                    if not sid:
                        sid =  httprequest.headers.get("X-Openerp-Session-Id")
                    if not sid:
                        sid = httprequest.cookies.get('session_id')
                        explicit_session = False
                    if sid is None:
                        httprequest.session = self.session_store.new()
                    else:
                        httprequest.session = self.session_store.get(sid)
                    return explicit_session
                else:
                    return self.setup_session_(httprequest)

            def preload(self):
                self._loaded = True
                self.load_addons()

        root = Root()
        return locals()


class patch_session(SoftPatch):

    @staticmethod
    def apply_patch():

        from odooku.patch.helpers import patch_class
        from odooku.backends.redis import RedisSessionStore

        @patch_class(globals()['OpenERPSession'])
        class OpenERPSession(object):

            def save_request_data(self):
                if isinstance(root.session_store, RedisSessionStore):
                    req = request.httprequest
                    if req.files:
                        raise NotImplementedError("Cannot save request data with files")

                    self['serialized_request_data'] = {
                        'form': req.form
                    }
                else:
                    self.save_request_data_()

            @contextlib.contextmanager
            def load_request_data(self):
                if isinstance(root.session_store, RedisSessionStore):
                    data = self.pop('serialized_request_data', None)
                    if data:
                        yield werkzeug.datastructures.CombinedMultiDict([data['form']])
                    else:
                        yield None
                else:
                    with self.load_request_data_() as data:
                        yield data
        
        return locals()


class patch_db_filter(SoftPatch):
    
    @staticmethod
    def apply_patch():

        def db_filter(dbs, httprequest=None):
            httprequest = httprequest or request.httprequest
            h = httprequest.environ.get('HTTP_HOST', '').split(':')[0]
            d, _, r = h.partition('.')
            if d == "www" and r:
                d = r.partition('.')[0]
            if odoo.tools.config['dbfilter']:
                h = h.replace('.', '_')
                d, h = re.escape(d), re.escape(h)
                r = odoo.tools.config['dbfilter'].replace('%h', h).replace('%d', d)
                dbs = [i for i in dbs if re.match(r, i)]
            elif odoo.tools.config['db_name']:
                # In case --db-filter is not provided and --database is passed, Odoo will
                # use the value of --database as a comma seperated list of exposed databases.
                exposed_dbs = set(db.strip() for db in odoo.tools.config['db_name'].split(','))
                dbs = sorted(exposed_dbs.intersection(dbs))
            return dbs

        return locals()


patch_root('odoo.http')
patch_http_request('odoo.http')
patch_json_request('odoo.http')
patch_session('odoo.http')
patch_db_filter('odoo.http')