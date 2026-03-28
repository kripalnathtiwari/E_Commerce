from storages.backends.s3boto3 import S3Boto3Storage

class S3DesignStorage(S3Boto3Storage):
    file_overwrite = False
    default_acl = None
