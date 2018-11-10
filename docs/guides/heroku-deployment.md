!!! note
    This guide assumes you have basic knowledge of the Heroku platform.

## Setup your project


#### requirements.txt
```
odooku-odoo-addons>=11.0.2,<12.0.0
odooku>=11.0.6,<12.0.0
```

#### Procfile
```
web: odooku --database-maxconn 20 --redis-maxconn 10 wsgi $PORT --cron --proxy-mode
```

!!! warning
    This procfile is optimized to work with Heroku's Postgres **hobby-basic** plan
    and the Redis **hobby-dev** plan. Choose your own plans and configure accordingly.

!!! tip
    When scaling to **N** dyno's, divide the maxconn values by factor **N**.

## Create the app

Deploying Odooku requires a custom buildpack. Create your Heroku app like so:

``` bash
heroku create --buildpack https://github.com/odooku/odooku-buildpack.git#11.0
```

## Setup backing services

!!! note
    If you are not familiar with S3 buckets, see:
    [Getting Started with Amazon Simple Storage Service]([http://docs.aws.amazon.com/AmazonS3/latest/gsg/GetStartedWithS3.html])

!!! warning
    To lower costs and increase performance ensure that your bucket is located in the same
    region as your Heroku application region.

### S3

``` bash
heroku config:set AWS_ACCESS_KEY_ID=<your_aws_key>
heroku config:set AWS_SECRET_ACCESS_KEY=<your_aws_secret>
heroku config:set AWS_REGION=<your_aws_region>
heroku config:set S3_BUCKET=<your_s3_bucket_name>
```

### Postgresql

``` bash
heroku addons:create heroku-postgresql:hobby-basic
```

### Redis

``` bash
heroku addons:create heroku-redis:hobby-dev
```


## Deploy

``` bash
git push heroku master
```
