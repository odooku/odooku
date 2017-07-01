Odooku can integrate with New Relic make sure to modify your requirements.txt.

The following environment variables are available:

- NEW_RELIC_LICENSE_KEY (required)
- NEW_RELIC_CONFIG_FILE

### requirements.txt

```
newrelic
```

```
$ heroku config:set NEW_RELIC_LICENSE_KEY=<your_newrelic_license_key>
$ devoku env set NEW_RELIC_LICENSE_KEY=<your_newrelic_license_key>
```
