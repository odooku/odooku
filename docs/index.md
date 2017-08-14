Odooku provides a great way to run Odoo as a service,
deploy your codebase, migrate your data and more.

## Guides

- [Heroku deployment](/guides/heroku-deployment)
- [Manual installation](/guides/manual-installation)
- [Local development](/guides/local-development)


## Python packages

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

[View Github](https://github.com/odooku/odooku)

### odooku-odoo

Pypi packaged Odoo providing an easy and reliable install method for Odoo.

[View Github](https://github.com/odooku/odooku-odoo)

### odooku-data

Data serialization and deserialization library for migrations (docs comming soon).

[View Github](https://github.com/odooku/odooku-data)

## Heroku deployment

### odooku-heroku-buildpack

Heroku buildpack for Odooku.

[View Github](https://github.com/odooku/odooku-heroku-buildpack)

### odooku-heroku-starter

Template project for Heroku.

[View Github](https://github.com/odooku/odooku-heroku-starter)

## Snap deployment

### odooku-snap

[View Github](https://github.com/odooku/odooku-snap)