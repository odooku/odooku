Odooku provides a great way to run Odoo as a service, deploy your codebase, migrate your data and more.

### odooku

Wrapper package around Odoo that patches and extends Odoo to work in a service oriented environment.

- Strips out threading in favor of Gevent
- Single process wsgi server and/or cron runner
- S3 based filestore
- Redis sessions for multi server deployments
- Websockets for persistent connections and awesome performance
- Comprehensive suite of management commands
- CDN support, serve all static files directly through S3
- Packaged addons

### odooku-odoo

Pypi packaged Odoo for easy install.

### odooku-data

Data serialization and deserialization library for migrations (docs comming soon).

## Heroku

### odooku-heroku-buildpack

Heroku buildpack for Odooku.

### odooku-heroku-starter

Template project for Heroku.

## Snap

### odooku-snap
