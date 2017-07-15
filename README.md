## Development instructions


### Run against local services

```
$ docker run --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=odoo -e POSTGRES_USER=odoo -d postgres:9.5
$ docker run --name redis -p 6379:6379 -d redis:latest
$ docker run --name s3 -p 4569:4569 -d lphoward/fake-s3:latest -r /fakes3_root -p 4569 -H localhost
```

### Install LESSC

```
$ npm install -g less
```

### Environment variables

Put these in an .env file

```
export DATABASE_URL=postgres://odoo:odoo@localhost:5432
export REDIS_URL=redis://localhost:6379
export S3_BUCKET=odooku
export S3_ENDPOINT_URL=http://localhost:4569
export S3_CUSTOM_DOMAIN=http://odooku.localhost:4569
export AWS_ACCESS_KEY_ID=foobar
export AWS_SECRET_ACCESS_KEY=foobar
export ODOOKU_ADMIN_PASSWORD=foobar
```

#### OSX

```
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

#### Visual Studio Code debugging

```
export ODOOKU_PTVSD_URL=ptvsd://:keyboardcat@localhost:3000
```


## Test instructions


### Install phantomjs

```
npm install -g phantomjs-prebuilt
```

### Run the tests

```
odooku runtests --db-name test
```