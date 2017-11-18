from odooku.patch import SoftPatch


class patch_registry_concurrency(SoftPatch):

    @staticmethod
    def apply_patch():

        from odooku.patch.helpers import patch_class
        from gevent.lock import RLock
        
        @patch_class(globals()['Registry'])
        class Registry(object):
            """ Model registry for a particular database.

            The registry is essentially a mapping between model names and model classes.
            There is one registry instance per database.

            """

            # Clear set lock
            _lock = None

            def __new__(cls, db_name):
                """ Return the registry for the given database name."""
                if db_name in cls.registries:
                    registry = cls.registries[db_name]
                    registry._lock.acquire()
                    registry._lock.release()
                    registry = cls.registries[db_name]
                else:
                    registry = cls.new(db_name)

                # set db tracker - cleaned up at the WSGI dispatching phase in
                # odoo.service.wsgi_server.application
                threading.current_thread().dbname = db_name
                return registry

            @classmethod
            def new(cls, db_name, force_demo=False, status=None, update_module=False):
                """ Create and return a new registry for the given database name. """
                with odoo.api.Environment.manage():
                    cls.delete(db_name)
                    registry = object.__new__(cls)
                    cls.registries[db_name] = registry

                    # Counter to Odoo's class based locking mechanism, we will
                    # only use locks at instance level.
                    registry._lock = RLock()

                    # Lock point
                    with registry._lock:
                        registry.init(db_name)

                        try:
                            registry.setup_signaling()
                            # This should be a method on Registry
                            odoo.modules.load_modules(registry._db, force_demo, status, update_module)
                        except Exception as ex:
                            _logger.exception('Failed to load registry')
                            _logger.exception(ex, exc_info=True)
                            del cls.registries[db_name]
                            raise

                        # load_modules() above can replace the registry by calling
                        # indirectly new() again (when modules have to be uninstalled).
                        # Yeah, crazy.
                        init_parent = registry._init_parent
                        registry = cls.registries[db_name]
                        registry._init_parent.update(init_parent)

                        with closing(registry.cursor()) as cr:
                            registry.do_parent_store(cr)
                            cr.commit()

                registry.ready = True
                registry.registry_invalidated = bool(update_module)
                return registry

            @classmethod
            def delete(cls, db_name):
                """ Delete the registry linked to a given database. """
                if db_name in cls.registries:
                    registry = cls.registries[db_name]
                    # Lock point
                    with registry._lock:
                        registry.clear_caches()
                    del cls.registries[db_name]

            @classmethod
            def delete_all(cls):
                """ Delete all the registries. """
                for db_name in cls.registries.keys():
                    cls.delete(db_name)

            def enter_test_mode(self):
                """ Enter the 'test' mode, where one cursor serves several requests. """
                assert self.test_cr is None
                self.test_cr = self._db.test_cursor()
                assert self._saved_lock is None
                self._saved_lock = self._lock
                self._lock = DummyRLock()

            def leave_test_mode(self):
                """ Leave the test mode. """
                assert self.test_cr is not None
                self.clear_caches()
                self.test_cr.force_close()
                self.test_cr = None
                assert self._saved_lock is not None
                self._lock = self._saved_lock
                self._saved_lock = None
        
        return locals()


patch_registry_concurrency('odoo.modules.registry')