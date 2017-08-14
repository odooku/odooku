## About this guide

This guide is intended for setting up a local development
environment for Odoo. It consists out of 4 parts:

- Python installation
- LESSC & WKHTMLTOPDF
- Running docker services
- Environment configuration
- Running

## Python installation

Follow [Manual installation](/guides/manual-installation) guide.

## LESSC & WKHTMLTOPDF

Todo

## Running docker services

``` bash
docker run --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=odoo -e POSTGRES_USER=odoo -d postgres:9.5
docker run --name redis -p 6379:6379 -d redis:latest
docker run --name s3 -p 4569:4569 -d lphoward/fake-s3:latest -r /fakes3_root -p 4569 -H localhost
```

## Environment configuration


``` bash
export DATABASE_URL=postgres://odoo:odoo@localhost:5432
export REDIS_URL=redis://localhost:6379
export S3_BUCKET=odooku
export S3_ENDPOINT_URL=http://localhost:4569
export S3_CUSTOM_DOMAIN=http://odooku.localhost:4569
export AWS_ACCESS_KEY_ID=foobar
export AWS_SECRET_ACCESS_KEY=foobar
export ODOOKU_ADMIN_PASSWORD=foobar
```

!!! tip
    Put this in an .env file and source it.

### OSX 

This should only be required on OSX.

``` bash
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

## Running

``` bash
odooku <your command>
```

### Run development server

``` bash
odooku wsgi 8000 --dev
```