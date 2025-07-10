"""
S3 management service for AWS Toolkit.
"""

import boto3
import os
from typing import List, Dict, Any, Optional, BinaryIO
from botocore.exceptions import ClientError
from ..core.config import Config
from ..utils.logger import get_logger


class S3Manager:
    """Manages S3 buckets and objects."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize S3 manager.

        Args:
            config: Configuration instance
        """
        self.config = config or Config()
        self.logger = get_logger(__name__, self.config.get("app.log_level"))

        try:
            self.s3_client = boto3.client("s3", **self.config.aws_config)
            self.s3_resource = boto3.resource("s3", **self.config.aws_config)
        except Exception as e:
            self.logger.error(f"Failed to initialize S3 client: {e}")
            raise

    def list_buckets(self) -> List[Dict[str, Any]]:
        """List all S3 buckets.

        Returns:
            List of bucket information
        """
        try:
            response = self.s3_client.list_buckets()
            buckets = []

            for bucket in response["Buckets"]:
                buckets.append(
                    {"Name": bucket["Name"], "CreationDate": bucket["CreationDate"]}
                )

            self.logger.info(f"Found {len(buckets)} buckets")
            return buckets

        except ClientError as e:
            self.logger.error(f"Failed to list buckets: {e}")
            raise

    def create_bucket(self, bucket_name: str, region: Optional[str] = None) -> bool:
        """Create a new S3 bucket.

        Args:
            bucket_name: Name of the bucket to create
            region: AWS region (uses default if not specified)

        Returns:
            True if successful
        """
        try:
            region = region or self.config.get("aws.region")

            # Create bucket configuration
            if region != "us-east-1":
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": region},
                )
            else:
                self.s3_client.create_bucket(Bucket=bucket_name)

            self.logger.info(f"Created bucket: {bucket_name}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to create bucket {bucket_name}: {e}")
            raise

    def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """Delete an S3 bucket.

        Args:
            bucket_name: Name of the bucket to delete
            force: If True, delete all objects first

        Returns:
            True if successful
        """
        try:
            if force:
                # Delete all objects first
                self.delete_all_objects(bucket_name)

            self.s3_client.delete_bucket(Bucket=bucket_name)
            self.logger.info(f"Deleted bucket: {bucket_name}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to delete bucket {bucket_name}: {e}")
            raise

    def upload_file(
        self,
        file_path: str,
        bucket_name: str,
        object_key: Optional[str] = None,
        extra_args: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Upload a file to S3.

        Args:
            file_path: Local file path
            bucket_name: Target bucket name
            object_key: S3 object key (uses filename if not specified)
            extra_args: Additional upload arguments

        Returns:
            True if successful
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            if object_key is None:
                object_key = os.path.basename(file_path)

            # Add encryption if configured
            if extra_args is None:
                extra_args = {}

            encryption = self.config.get("s3.encryption")
            if encryption and "ServerSideEncryption" not in extra_args:
                extra_args["ServerSideEncryption"] = encryption

            self.s3_client.upload_file(
                file_path, bucket_name, object_key, ExtraArgs=extra_args
            )
            self.logger.info(f"Uploaded {file_path} to s3://{bucket_name}/{object_key}")
            return True

        except (ClientError, FileNotFoundError) as e:
            self.logger.error(f"Failed to upload file: {e}")
            raise

    def download_file(self, bucket_name: str, object_key: str, file_path: str) -> bool:
        """Download a file from S3.

        Args:
            bucket_name: Source bucket name
            object_key: S3 object key
            file_path: Local file path to save

        Returns:
            True if successful
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            self.s3_client.download_file(bucket_name, object_key, file_path)
            self.logger.info(
                f"Downloaded s3://{bucket_name}/{object_key} to {file_path}"
            )
            return True

        except ClientError as e:
            self.logger.error(f"Failed to download file: {e}")
            raise

    def list_objects(
        self, bucket_name: str, prefix: Optional[str] = None, max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """List objects in an S3 bucket.

        Args:
            bucket_name: Bucket name
            prefix: Object key prefix filter
            max_keys: Maximum number of objects to return

        Returns:
            List of object information
        """
        try:
            params = {"Bucket": bucket_name, "MaxKeys": max_keys}

            if prefix:
                params["Prefix"] = prefix

            response = self.s3_client.list_objects_v2(**params)
            objects = []

            for obj in response.get("Contents", []):
                objects.append(
                    {
                        "Key": obj["Key"],
                        "Size": obj["Size"],
                        "LastModified": obj["LastModified"],
                        "ETag": obj["ETag"],
                        "StorageClass": obj.get("StorageClass", "STANDARD"),
                    }
                )

            self.logger.info(f"Found {len(objects)} objects in {bucket_name}")
            return objects

        except ClientError as e:
            self.logger.error(f"Failed to list objects: {e}")
            raise

    def delete_object(self, bucket_name: str, object_key: str) -> bool:
        """Delete an object from S3.

        Args:
            bucket_name: Bucket name
            object_key: Object key to delete

        Returns:
            True if successful
        """
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
            self.logger.info(f"Deleted s3://{bucket_name}/{object_key}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to delete object: {e}")
            raise

    def delete_all_objects(self, bucket_name: str, prefix: Optional[str] = None) -> int:
        """Delete all objects in a bucket.

        Args:
            bucket_name: Bucket name
            prefix: Object key prefix filter

        Returns:
            Number of objects deleted
        """
        try:
            objects = self.list_objects(bucket_name, prefix)

            if not objects:
                return 0

            # Prepare delete requests
            delete_keys = [{"Key": obj["Key"]} for obj in objects]

            # Delete in batches of 1000
            deleted_count = 0
            for i in range(0, len(delete_keys), 1000):
                batch = delete_keys[i : i + 1000]
                response = self.s3_client.delete_objects(
                    Bucket=bucket_name, Delete={"Objects": batch}
                )
                deleted_count += len(response.get("Deleted", []))

            self.logger.info(f"Deleted {deleted_count} objects from {bucket_name}")
            return deleted_count

        except ClientError as e:
            self.logger.error(f"Failed to delete objects: {e}")
            raise

    def copy_object(
        self, source_bucket: str, source_key: str, dest_bucket: str, dest_key: str
    ) -> bool:
        """Copy an object within S3.

        Args:
            source_bucket: Source bucket name
            source_key: Source object key
            dest_bucket: Destination bucket name
            dest_key: Destination object key

        Returns:
            True if successful
        """
        try:
            copy_source = {"Bucket": source_bucket, "Key": source_key}
            self.s3_client.copy_object(
                CopySource=copy_source, Bucket=dest_bucket, Key=dest_key
            )

            self.logger.info(
                f"Copied s3://{source_bucket}/{source_key} to s3://{dest_bucket}/{dest_key}"
            )
            return True

        except ClientError as e:
            self.logger.error(f"Failed to copy object: {e}")
            raise

    def get_object_metadata(self, bucket_name: str, object_key: str) -> Dict[str, Any]:
        """Get object metadata.

        Args:
            bucket_name: Bucket name
            object_key: Object key

        Returns:
            Object metadata
        """
        try:
            response = self.s3_client.head_object(Bucket=bucket_name, Key=object_key)

            return {
                "ContentLength": response["ContentLength"],
                "ContentType": response.get("ContentType"),
                "LastModified": response["LastModified"],
                "ETag": response["ETag"],
                "Metadata": response.get("Metadata", {}),
                "StorageClass": response.get("StorageClass", "STANDARD"),
            }

        except ClientError as e:
            self.logger.error(f"Failed to get object metadata: {e}")
            raise

    def generate_presigned_url(
        self,
        bucket_name: str,
        object_key: str,
        expiration: int = 3600,
        http_method: str = "GET",
    ) -> str:
        """Generate a presigned URL for an S3 object.

        Args:
            bucket_name: Bucket name
            object_key: Object key
            expiration: URL expiration time in seconds
            http_method: HTTP method (GET, PUT, etc.)

        Returns:
            Presigned URL
        """
        try:
            response = self.s3_client.generate_presigned_url(
                http_method.lower() + "_object",
                Params={"Bucket": bucket_name, "Key": object_key},
                ExpiresIn=expiration,
            )

            self.logger.info(
                f"Generated presigned URL for s3://{bucket_name}/{object_key}"
            )
            return response

        except ClientError as e:
            self.logger.error(f"Failed to generate presigned URL: {e}")
            raise

    def set_bucket_policy(self, bucket_name: str, policy: Dict[str, Any]) -> bool:
        """Set bucket policy.

        Args:
            bucket_name: Bucket name
            policy: Bucket policy as dictionary

        Returns:
            True if successful
        """
        try:
            import json

            policy_json = json.dumps(policy)

            self.s3_client.put_bucket_policy(Bucket=bucket_name, Policy=policy_json)

            self.logger.info(f"Set bucket policy for {bucket_name}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to set bucket policy: {e}")
            raise
