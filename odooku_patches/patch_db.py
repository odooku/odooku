from odooku.patch import SoftPatch


class patch_check_super(SoftPatch):

    @staticmethod
    def apply_patch():

        def check_super(passwd):
            if odoo.tools.config['admin_passwd'] is not None:
                if passwd and passwd == odoo.tools.config['admin_passwd']:
                    return True
            raise odoo.exceptions.AccessDenied()

        return dict(check_super=check_super)


class patch_dump_db(SoftPatch):

    @staticmethod
    def apply_patch():

        from odoo import api, models, SUPERUSER_ID

        def dump_db(db_name, stream=None, backup_format='zip'):
            """Dump database `db` into file-like object `stream` if stream is None
            return a file object with the dump """

            _logger.info('DUMP DB: %s format %s', db_name, backup_format)

            cmd = ['pg_dump', '--no-owner']
            cmd.append(db_name)

            if backup_format == 'zip':
                with odoo.tools.osutil.tempdir() as dump_dir:
                    # PATCH !!
                    # Instead of copying the filestore directory, read
                    # all attachments from filestore/s3-bucket
                    registry = odoo.modules.registry.Registry.new(db_name)
                    # We need all attachments, bypass regular search
                    with registry.cursor() as cr:
                        env = api.Environment(cr, SUPERUSER_ID, {})
                        IrAttachment = env['ir.attachment']
                        ids = models.Model._search(IrAttachment, [])
                        for attachment in IrAttachment.browse(ids):
                            if attachment.store_fname:
                                full_path = os.path.join(dump_dir, 'filestore', attachment.store_fname)
                                bin_value = attachment.datas
                                if bin_value is False:
                                    continue
                                if not os.path.exists(os.path.dirname(full_path)):
                                    os.makedirs(os.path.dirname(full_path))
                                with open(full_path, 'wb') as fp:
                                    fp.write(bin_value)

                    with open(os.path.join(dump_dir, 'manifest.json'), 'w') as fh:
                        db = odoo.sql_db.db_connect(db_name)
                        with db.cursor() as cr:
                            json.dump(dump_db_manifest(cr), fh, indent=4)
                    cmd.insert(-1, '--file=' + os.path.join(dump_dir, 'dump.sql'))
                    odoo.tools.exec_pg_command(*cmd)
                    if stream:
                        odoo.tools.osutil.zip_dir(dump_dir, stream, include_dir=False, fnct_sort=lambda file_name: file_name != 'dump.sql')
                    else:
                        t=tempfile.TemporaryFile()
                        odoo.tools.osutil.zip_dir(dump_dir, t, include_dir=False, fnct_sort=lambda file_name: file_name != 'dump.sql')
                        t.seek(0)
                        return t
            else:
                cmd.insert(-1, '--format=c')
                stdin, stdout = odoo.tools.exec_pg_command_pipe(*cmd)
                if stream:
                    shutil.copyfileobj(stdout, stream)
                else:
                    return stdout

        return dict(dump_db=dump_db)


class patch_restore_db(SoftPatch):

    @staticmethod
    def apply_patch():

        from odoo import api, models, SUPERUSER_ID

        def restore_db(db_name, dump_file, copy=False):
            assert isinstance(db_name, str)
            if exp_db_exist(db_name):
                _logger.info('RESTORE DB: %s already exists', db_name)
                raise Exception("Database already exists")

            _create_empty_database(db_name)

            filestore_path = None
            with odoo.tools.osutil.tempdir() as dump_dir:
                if zipfile.is_zipfile(dump_file):
                    # v8 format
                    with zipfile.ZipFile(dump_file, 'r') as z:
                        # only extract known members!
                        filestore = [m for m in z.namelist() if m.startswith('filestore/')]
                        z.extractall(dump_dir, ['dump.sql'] + filestore)

                        if filestore:
                            filestore_path = os.path.join(dump_dir, 'filestore')

                    pg_cmd = 'psql'
                    pg_args = ['-q', '-f', os.path.join(dump_dir, 'dump.sql')]

                else:
                    # <= 7.0 format (raw pg_dump output)
                    pg_cmd = 'pg_restore'
                    pg_args = ['--no-owner', dump_file]

                args = []
                args.append('--dbname=' + db_name)
                pg_args = args + pg_args

                if odoo.tools.exec_pg_command(pg_cmd, *pg_args):
                    raise Exception("Couldn't restore database")

                registry = odoo.modules.registry.Registry.new(db_name)
                with registry.cursor() as cr:
                    env = odoo.api.Environment(cr, SUPERUSER_ID, {})
                    if copy:
                        # if it's a copy of a database, force generation of a new dbuuid
                        env['ir.config_parameter'].init(force=True)
                    if filestore_path:
                        # PATCH !!
                        # Instead of copying the filestore directory, read
                        # all attachments from filestore/s3-bucket.
                        attachment = env['ir.attachment']
                        # For some reason we can't search installed attachments...
                        cr.execute("SELECT id FROM ir_attachment")
                        for id in [rec['id'] for rec in cr.dictfetchall()]:
                            rec = attachment.browse([id])[0]
                            if rec.store_fname:
                                full_path = os.path.join(dump_dir, 'filestore', rec.store_fname)
                                if os.path.exists(full_path):
                                    value = open(full_path,'rb').read()
                                    rec.write({'datas': value, 'mimetype': rec.mimetype})

                    if odoo.tools.config['unaccent']:
                        try:
                            with cr.savepoint():
                                cr.execute("CREATE EXTENSION unaccent")
                        except psycopg2.Error:
                            pass

            _logger.info('RESTORE DB: %s', db_name)

        return dict(restore_db=restore_db)


class patch_exp_change_admin_password(SoftPatch):

    @staticmethod
    def apply_patch():

        def exp_change_admin_password(new_password):
            # Won't have any effect
            return False

        return dict(exp_change_admin_password=exp_change_admin_password)


class patch_list_dbs(SoftPatch):

    @staticmethod
    def apply_patch():

        from odooku.params import params

        original_list_dbs = list_dbs
        def patched_list_dbs(force=False):
            if params.no_db:
                return []
            
            if odoo.tools.config['db_name']:
                return odoo.tools.config['db_name'].split(',')
            return original_list_dbs(force)

        return dict(list_dbs=patched_list_dbs)


patch_check_super('odoo.service.db')
patch_dump_db('odoo.service.db')
patch_restore_db('odoo.service.db')
patch_list_dbs('odoo.service.db')
patch_exp_change_admin_password('odoo.service.db')