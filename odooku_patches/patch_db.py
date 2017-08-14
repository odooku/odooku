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
                    registry = odoo.modules.registry.RegistryManager.new(db_name)
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
            assert isinstance(db_name, basestring)
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


class patch_base_sql(SoftPatch):

    @staticmethod
    def apply_patch():

        import os


        BASE_SQL = '''
        CREATE TABLE ir_actions (
        id serial,
        primary key(id)
        );
        CREATE TABLE ir_act_window (primary key(id)) INHERITS (ir_actions);
        CREATE TABLE ir_act_report_xml (primary key(id)) INHERITS (ir_actions);
        CREATE TABLE ir_act_url (primary key(id)) INHERITS (ir_actions);
        CREATE TABLE ir_act_server (primary key(id)) INHERITS (ir_actions);
        CREATE TABLE ir_act_client (primary key(id)) INHERITS (ir_actions);


        CREATE TABLE ir_model (
        id serial,
        model varchar NOT NULL,
        name varchar,
        state varchar,
        info text,
        transient boolean,
        primary key(id)
        );

        CREATE TABLE ir_model_fields (
        id serial,
        model varchar NOT NULL,
        model_id integer references ir_model on delete cascade,
        name varchar NOT NULL,
        state varchar default 'base',
        field_description varchar,
        help varchar,
        ttype varchar,
        relation varchar,
        relation_field varchar,
        index boolean,
        copy boolean,
        related varchar,
        readonly boolean default False,
        required boolean default False,
        selectable boolean default False,
        translate boolean default False,
        serialization_field_id integer references ir_model_fields on delete cascade,
        relation_table varchar,
        column1 varchar,
        column2 varchar,
        store boolean,
        primary key(id)
        );

        CREATE TABLE res_lang (
            id serial,
            name VARCHAR(64) NOT NULL UNIQUE,
            code VARCHAR(16) NOT NULL UNIQUE,
            primary key(id)
        );

        CREATE TABLE res_users (
            id serial NOT NULL,
            active boolean default True,
            login varchar(64) NOT NULL UNIQUE,
            password varchar(64) default null,
            -- No FK references below, will be added later by ORM
            -- (when the destination rows exist)
            company_id integer, -- references res_company,
            partner_id integer, -- references res_partner,
            primary key(id)
        );

        create table wkf (
            id serial,
            name varchar(64),
            osv varchar(64),
            on_create bool default false,
            primary key(id)
        );

        CREATE TABLE ir_module_category (
            id serial NOT NULL,
            create_uid integer, -- references res_users on delete set null,
            create_date timestamp without time zone,
            write_date timestamp without time zone,
            write_uid integer, -- references res_users on delete set null,
            parent_id integer REFERENCES ir_module_category ON DELETE SET NULL,
            name character varying(128) NOT NULL,
            primary key(id)
        );

        CREATE TABLE ir_module_module (
            id serial NOT NULL,
            create_uid integer, -- references res_users on delete set null,
            create_date timestamp without time zone,
            write_date timestamp without time zone,
            write_uid integer, -- references res_users on delete set null,
            website character varying(256),
            summary character varying(256),
            name character varying(128) NOT NULL,
            author character varying(128),
            icon varchar,
            state character varying(16),
            latest_version character varying(64),
            shortdesc character varying(256),
            category_id integer REFERENCES ir_module_category ON DELETE SET NULL,
            description text,
            application boolean default False,
            demo boolean default False,
            web boolean DEFAULT FALSE,
            license character varying(32),
            sequence integer DEFAULT 100,
            auto_install boolean default False,
            primary key(id)
        );
        ALTER TABLE ir_module_module add constraint name_uniq unique (name);

        CREATE TABLE ir_module_module_dependency (
            id serial NOT NULL,
            create_uid integer, -- references res_users on delete set null,
            create_date timestamp without time zone,
            write_date timestamp without time zone,
            write_uid integer, -- references res_users on delete set null,
            name character varying(128),
            module_id integer REFERENCES ir_module_module ON DELETE cascade,
            primary key(id)
        );

        CREATE TABLE ir_model_data (
            id serial NOT NULL,
            create_uid integer,
            create_date timestamp without time zone,
            write_date timestamp without time zone,
            write_uid integer,
            noupdate boolean,
            name varchar NOT NULL,
            date_init timestamp without time zone,
            date_update timestamp without time zone,
            module varchar NOT NULL,
            model varchar NOT NULL,
            res_id integer,
            primary key(id)
        );

        -- Records foreign keys and constraints installed by a module (so they can be
        -- removed when the module is uninstalled):
        --   - for a foreign key: type is 'f',
        --   - for a constraint: type is 'u' (this is the convention PostgreSQL uses).
        CREATE TABLE ir_model_constraint (
            id serial NOT NULL,
            date_init timestamp without time zone,
            date_update timestamp without time zone,
            module integer NOT NULL references ir_module_module on delete restrict,
            model integer NOT NULL references ir_model on delete restrict,
            type character varying(1) NOT NULL,
            definition varchar,
            name varchar NOT NULL,
            primary key(id)
        );

        -- Records relation tables (i.e. implementing many2many) installed by a module
        -- (so they can be removed when the module is uninstalled).
        CREATE TABLE ir_model_relation (
            id serial NOT NULL,
            date_init timestamp without time zone,
            date_update timestamp without time zone,
            module integer NOT NULL references ir_module_module on delete restrict,
            model integer NOT NULL references ir_model on delete restrict,
            name varchar NOT NULL,
            primary key(id)
        );

        CREATE TABLE res_currency (
            id serial,
            name varchar NOT NULL,
            symbol varchar NOT NULL,
            primary key(id)
        );

        CREATE TABLE res_company (
            id serial,
            name varchar NOT NULL,
            sequence integer, -- PATCH
            partner_id integer,
            currency_id integer,
            primary key(id)
        );

        CREATE TABLE res_partner (
            id serial,
            name varchar,
            company_id integer,
            primary key(id)
        );


        ---------------------------------
        -- Default data
        ---------------------------------
        insert into res_currency (id, name, symbol) VALUES (1, 'EUR', '\u20ac35');
        insert into ir_model_data (name, module, model, noupdate, res_id) VALUES ('EUR', 'base', 'res.currency', true, 1);
        select setval('res_currency_id_seq', 2);

        insert into res_company (id, name, sequence, partner_id, currency_id) VALUES (1, 'My Company', 10, 1, 1);
        insert into ir_model_data (name, module, model, noupdate, res_id) VALUES ('main_company', 'base', 'res.company', true, 1);
        select setval('res_company_id_seq', 2);

        insert into res_partner (id, name, company_id) VALUES (1, 'My Company', 1);
        insert into ir_model_data (name, module, model, noupdate, res_id) VALUES ('main_partner', 'base', 'res.partner', true, 1);
        select setval('res_partner_id_seq', 2);

        insert into res_users (id, login, password, active, partner_id, company_id) VALUES (1, 'admin', 'admin', true, 1, 1);
        insert into ir_model_data (name, module, model, noupdate, res_id) VALUES ('user_root', 'base', 'res.users', true, 1);
        select setval('res_users_id_seq', 2);
        '''


        def initialize(cr):
            """ Initialize a database with for the ORM.
            This executes base/base.sql, creates the ir_module_categories (taken
            from each module descriptor file), and creates the ir_module_module
            and ir_model_data entries.
            """
            cr.execute(BASE_SQL)
            cr.commit()

            for i in odoo.modules.get_modules():
                mod_path = odoo.modules.get_module_path(i)
                if not mod_path:
                    continue

                # This will raise an exception if no/unreadable descriptor file.
                info = odoo.modules.load_information_from_description_file(i)

                if not info:
                    continue
                categories = info['category'].split('/')
                category_id = create_categories(cr, categories)

                if info['installable']:
                    state = 'uninstalled'
                else:
                    state = 'uninstallable'

                cr.execute('INSERT INTO ir_module_module \
                        (author, website, name, shortdesc, description, \
                            category_id, auto_install, state, web, license, application, icon, sequence, summary) \
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id', (
                    info['author'],
                    info['website'], i, info['name'],
                    info['description'], category_id,
                    info['auto_install'], state,
                    info['web'],
                    info['license'],
                    info['application'], info['icon'],
                    info['sequence'], info['summary']))
                id = cr.fetchone()[0]
                cr.execute('INSERT INTO ir_model_data \
                    (name,model,module, res_id, noupdate) VALUES (%s,%s,%s,%s,%s)', (
                        'module_'+i, 'ir.module.module', 'base', id, True))
                dependencies = info['depends']
                for d in dependencies:
                    cr.execute('INSERT INTO ir_module_module_dependency \
                            (module_id,name) VALUES (%s, %s)', (id, d))

            # Install recursively all auto-installing modules
            while True:
                cr.execute("""SELECT m.name FROM ir_module_module m WHERE m.auto_install AND state != 'to install'
                              AND NOT EXISTS (
                                  SELECT 1 FROM ir_module_module_dependency d JOIN ir_module_module mdep ON (d.name = mdep.name)
                                           WHERE d.module_id = m.id AND mdep.state != 'to install'
                              )""")
                to_auto_install = [x[0] for x in cr.fetchall()]
                if not to_auto_install: break
                cr.execute("""UPDATE ir_module_module SET state='to install' WHERE name in %s""", (tuple(to_auto_install),))

            cr.commit()

        return dict(initialize=initialize)


patch_check_super('odoo.service.db')
patch_dump_db('odoo.service.db')
patch_restore_db('odoo.service.db')
patch_exp_change_admin_password('odoo.service.db')
patch_list_dbs('odoo.service.db')
patch_base_sql('odoo.modules.db')
