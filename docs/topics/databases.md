### Preloading a database
When running against a new database, it's recommended to preload the database
usign the 'odooku preload' command. Database initialization using a web worker
is possible however.

```
$ odooku database preload [--demo-data]
```

### Backup and Restore

```
$ odooku database dump --s3-file dump.zip
$ odooku database dump > file.zip
$ odooku database restore --s3-file dump.zip
$ dooku database restore < file.zip
```
