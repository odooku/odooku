import click
import os


__all__ = [
    'cdn'
]


RESERVED = ['filestore', 'backup']


@click.command()
@click.pass_context
def collect(ctx):
    logger = (
        ctx.obj['logger']
    )

    from odoo.modules import get_modules, get_module_path
    from odoo.tools.osutil import listdir
    from odooku.backends import get_backend

    s3_backend = get_backend('s3')

    for module in get_modules():
        if module in RESERVED:
            logger.warning("Module name %s clashes with a reserved key", module)
            continue
        static_dir = os.path.join(get_module_path(module), 'static')
        if os.path.exists(static_dir):
            for filename in listdir(static_dir, True):
                path = os.path.join(static_dir, filename)
                url = os.path.join(module, 'static', filename)
                logger.info("Uploading %s", url)
                s3_backend.client.upload_file(path, s3_backend.bucket, url, ExtraArgs={
                    'ACL': 'public-read',
                    'CacheControl': ('max-age=%d, public' % (s3_backend.cache_time))
                })


@click.group()
@click.pass_context
def cdn(ctx):
    pass


cdn.add_command(collect)
