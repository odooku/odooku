### Preloading a database
When running against a new database, it's recommended to preload the database
usign the 'odooku preload' command. Database initialization using a web worker
is possible however.

```
$ heroku run odooku database preload [--demo-data]
```

### Backup and Restore

```
$ heroku run odooku database dump --s3-file dump.zip
$ heroku run odooku database restore --s3-file dump.zip
```

Backup and restore from within the Vagrant development machine:

```
$ devoku run odooku database dump > /vagrant/dump.zip
$ devoku run odooku database restore < /vagrant/dump.zip
```
