# -*- encoding: utf-8 -*-
{
  'name': 'Amazon S3',
  'description': 'Amazon S3 integration for Odooku',
  'version': '0.1',
  'category': 'Hidden',
  'author': 'Raymond Reggers',
  'depends': ['base'],
  'data': [],
  'auto_install': True,
  'post_init_hook': '_force_s3_storage',
}
