A vagrant machine is provivded for development purposes. It fully emulates
the Heroku environment.

```
$ vagrant up
$ vagrant ssh
$ devoku service postgres up
$ devoku service redis up
$ devoku service s3 up
$ cd /vagrant
$ devoku env new
$ devoku build
$ devoku pg createdb
$ devoku web
```

### Create new database and S3 bucket

```
$ devoku env new
$ devoku pg createdb
$ devoku run odooku database preload
$ devoku web
```

## Database
Odooku can be run in single database mode, or Odoo's regular behaviour. If a
database is specified in DATABASE_URL, single database mode is enabled.
