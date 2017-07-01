Clone the Odooku repository or create your own repository. Odooku is like
any other Python Heroku project, however the Odooku buildpack also requires
an `odooku.json` file.

## Project structure

### Procfile ###

Tell Heroku what to run:

```
web: odooku wsgi $PORT
```

### odooku.json ###

The Odooku buildpack needs to know from where to fetch Odoo. This needs
to a Github repository.
```
{
  "odoo": {
    "repo": "odoo/odoo",
    "branch": "10.0",
    "commit": null
  }
}

```

### requirements.txt ###

Requirements file for pip installation. This needs to include a reference
to the desired `odooku-core` package. Odoo's requirements are installed
by the buildpack. For manual installation, create a file named
`odoo_requirements.txt`.

```
git+https://github.com/adaptivdesign/odooku-core.git@10.0
```

### addons ###

Place your addons under `/addons`


## First deployment

```
$ heroku create --buildpack https://github.com/adaptivdesign/odooku-buildpack
$ heroku addons:create heroku-postgresql:hobby-basic
$ heroku addons:create heroku-redis:hobby-dev
$ heroku config:set AWS_ACCESS_KEY_ID=<your_aws_key>
$ heroku config:set AWS_SECRET_ACCESS_KEY=<your_aws_secret>
$ heroku config:set AWS_REGION=<your_aws_region>
$ heroku config:set S3_BUCKET=<your_s3_bucket_name>
$ git push heroku master
```
