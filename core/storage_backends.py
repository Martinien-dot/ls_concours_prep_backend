import os
from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
    """
    Handles public media files like catalog thumbnails, PDF downloads, etc.
    """
    location = 'media/public'
    default_acl = None  # Critical for R2: disables S3 ACL headers
    file_overwrite = False
    custom_domain = os.getenv('R2_CUSTOM_DOMAIN')


class PrivateVideoStorage(S3Boto3Storage):
    """
    Handles private raw video uploads and HLS encoded playlists/segments.
    Generates pre-signed URLs for authenticated playback.
    """
    location = 'media/videos'
    default_acl = None  # Critical for R2: disables S3 ACL headers
    file_overwrite = True
    custom_domain = None  # Force R2 endpoint with pre-signed signatures
    querystring_auth = True
    querystring_expire = 3600  # Pre-signed URLs expire after 1 hour