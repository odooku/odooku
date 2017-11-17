import posixpath
from urllib.parse import urlparse, urljoin

import logging
import boto3
import botocore.session
from botocore.client import Config
from botocore.exceptions import ClientError
from werkzeug.local import Local

from odooku.backends.base import BaseBackend


_logger = logging.getLogger(__name__)



class S3Backend(BaseBackend):

    cache_time = 3600*24*30

    def __init__(self, bucket, aws_access_key_id=None,
            aws_region=None, aws_secret_access_key=None,
            addressing_style=None, signature_version=None,
            custom_domain=None, endpoint_url=None):
        self._local = Local()
        self._bucket = bucket
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._aws_region = aws_region
        self._endpoint_url = endpoint_url
        self._addressing_style = addressing_style
        self._signature_version = signature_version
        self._custom_domain = custom_domain

    def test_backend(self):
        # Wont work for fake-s3
        '''
        try:
            _logger.info("S3 (%s) head", self.bucket)
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            _logger.warning("S3 (%s) head", self.bucket, exc_info=True)
            return False
        '''
        return NotImplemented

    def get_url(self, *parts):
        if self._custom_domain:
            return urljoin(self._custom_domain, posixpath.join(*parts))
        return urljoin(self.client.meta.endpoint_url, posixpath.join(self.bucket, *parts))

    @property
    def bucket(self):
        return self._bucket

    @property
    def client(self):
        if not hasattr(self._local, 'client'):
            _logger.info("Creating new S3 Client")
            self._local.client = boto3.client(
                's3',
                region_name=self._aws_region,
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
                endpoint_url=self._endpoint_url,
                config=Config(
                    s3={'addressing_style': self._addressing_style},
                    signature_version=self._signature_version
                )
            )

        return self._local.client
