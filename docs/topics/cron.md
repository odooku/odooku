CRON jobs can be run in 3 differents ways:

### Along side the web process

This runs a somewhat slower polling cron worker. Ideal for most setups.

```
$ odooku wsgi --cron
```

### Dedicated worker process

This should be used for installations with long running cron jobs
(like mass mailing).

```
$ odooku cron
```

### Scheduled process

You can also make use of Heroku's scheduler, run Odooku as follows:

```
$ odooku cron --once
```
