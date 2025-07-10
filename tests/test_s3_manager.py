"""
Tests for S3Manager class.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from botocore.exceptions import ClientError
from aws_toolkit.services.s3_manager import S3Manager
from aws_toolkit.core.config import Config


class TestS3Manager:
    """Test cases for S3Manager class."""
    
    @pytest.fixture
    def s3_manager(self, mock_boto3_client, mock_boto3_resource):
        """S3Manager instance for testing."""
        config = Config()
        return S3Manager(config)
    
    def test_init_success(self, mock_boto3_client, mock_boto3_resource):
        """Test successful initialization."""
        config = Config()
        manager = S3Manager(config)
        assert manager is not None
        assert hasattr(manager, 's3_client')
        assert hasattr(manager, 's3_resource')
    
    def test_list_buckets_success(self, s3_manager):
        """Test successful bucket listing."""
        mock_response = {
            'Buckets': [
                {
                    'Name': 'test-bucket-1',
                    'CreationDate': '2023-01-01T00:00:00.000Z'
                },
                {
                    'Name': 'test-bucket-2', 
                    'CreationDate': '2023-01-02T00:00:00.000Z'
                }
            ]
        }
        
        s3_manager.s3_client.list_buckets.return_value = mock_response
        
        buckets = s3_manager.list_buckets()
        
        assert len(buckets) == 2
        assert buckets[0]['Name'] == 'test-bucket-1'
        assert buckets[1]['Name'] == 'test-bucket-2'
    
    def test_create_bucket_success_us_east_1(self, s3_manager):
        """Test successful bucket creation in us-east-1."""
        bucket_name = 'test-bucket'
        
        s3_manager.config.set('aws.region', 'us-east-1')
        s3_manager.s3_client.create_bucket.return_value = {}
        
        result = s3_manager.create_bucket(bucket_name)
        
        assert result is True
        s3_manager.s3_client.create_bucket.assert_called_once_with(
            Bucket=bucket_name
        )
    
    def test_create_bucket_success_other_region(self, s3_manager):
        """Test successful bucket creation in other regions."""
        bucket_name = 'test-bucket'
        region = 'eu-west-1'
        
        s3_manager.s3_client.create_bucket.return_value = {}
        
        result = s3_manager.create_bucket(bucket_name, region)
        
        assert result is True
        s3_manager.s3_client.create_bucket.assert_called_once_with(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': region}
        )
    
    def test_delete_bucket_success(self, s3_manager):
        """Test successful bucket deletion."""
        bucket_name = 'test-bucket'
        
        s3_manager.s3_client.delete_bucket.return_value = {}
        
        result = s3_manager.delete_bucket(bucket_name)
        
        assert result is True
        s3_manager.s3_client.delete_bucket.assert_called_once_with(
            Bucket=bucket_name
        )
    
    def test_upload_file_success(self, s3_manager):
        """Test successful file upload."""
        file_path = '/tmp/test.txt'
        bucket_name = 'test-bucket'
        object_key = 'test-object.txt'
        
        # Mock file existence
        with patch('os.path.exists', return_value=True):
            s3_manager.s3_client.upload_file.return_value = None
            
            result = s3_manager.upload_file(file_path, bucket_name, object_key)
            
            assert result is True
            s3_manager.s3_client.upload_file.assert_called_once()
    
    def test_upload_file_not_found(self, s3_manager):
        """Test file upload with non-existent file."""
        file_path = '/tmp/nonexistent.txt'
        bucket_name = 'test-bucket'
        
        with pytest.raises(FileNotFoundError):
            s3_manager.upload_file(file_path, bucket_name)
    
    def test_download_file_success(self, s3_manager):
        """Test successful file download."""
        bucket_name = 'test-bucket'
        object_key = 'test-object.txt'
        file_path = '/tmp/downloaded.txt'
        
        with patch('os.makedirs') as mock_makedirs:
            s3_manager.s3_client.download_file.return_value = None
            
            result = s3_manager.download_file(bucket_name, object_key, file_path)
            
            assert result is True
            s3_manager.s3_client.download_file.assert_called_once_with(
                bucket_name, object_key, file_path
            )
    
    def test_list_objects_success(self, s3_manager):
        """Test successful object listing."""
        bucket_name = 'test-bucket'
        
        mock_response = {
            'Contents': [
                {
                    'Key': 'object1.txt',
                    'Size': 1024,
                    'LastModified': '2023-01-01T00:00:00.000Z',
                    'ETag': '"abc123"',
                    'StorageClass': 'STANDARD'
                },
                {
                    'Key': 'object2.txt',
                    'Size': 2048,
                    'LastModified': '2023-01-02T00:00:00.000Z',
                    'ETag': '"def456"'
                }
            ]
        }
        
        s3_manager.s3_client.list_objects_v2.return_value = mock_response
        
        objects = s3_manager.list_objects(bucket_name)
        
        assert len(objects) == 2
        assert objects[0]['Key'] == 'object1.txt'
        assert objects[0]['Size'] == 1024
        assert objects[1]['StorageClass'] == 'STANDARD'  # Default value
    
    def test_list_objects_with_prefix(self, s3_manager):
        """Test object listing with prefix."""
        bucket_name = 'test-bucket'
        prefix = 'documents/'
        
        s3_manager.s3_client.list_objects_v2.return_value = {'Contents': []}
        
        s3_manager.list_objects(bucket_name, prefix)
        
        s3_manager.s3_client.list_objects_v2.assert_called_once_with(
            Bucket=bucket_name,
            MaxKeys=1000,
            Prefix=prefix
        )
    
    def test_delete_object_success(self, s3_manager):
        """Test successful object deletion."""
        bucket_name = 'test-bucket'
        object_key = 'test-object.txt'
        
        s3_manager.s3_client.delete_object.return_value = {}
        
        result = s3_manager.delete_object(bucket_name, object_key)
        
        assert result is True
        s3_manager.s3_client.delete_object.assert_called_once_with(
            Bucket=bucket_name,
            Key=object_key
        )
    
    def test_copy_object_success(self, s3_manager):
        """Test successful object copy."""
        source_bucket = 'source-bucket'
        source_key = 'source-object.txt'
        dest_bucket = 'dest-bucket'
        dest_key = 'dest-object.txt'
        
        s3_manager.s3_client.copy_object.return_value = {}
        
        result = s3_manager.copy_object(
            source_bucket, source_key, dest_bucket, dest_key
        )
        
        assert result is True
        
        # Verify copy_object was called with correct parameters
        call_args = s3_manager.s3_client.copy_object.call_args
        assert call_args[1]['Bucket'] == dest_bucket
        assert call_args[1]['Key'] == dest_key
        assert call_args[1]['CopySource']['Bucket'] == source_bucket
        assert call_args[1]['CopySource']['Key'] == source_key
    
    def test_get_object_metadata_success(self, s3_manager):
        """Test successful object metadata retrieval."""
        bucket_name = 'test-bucket'
        object_key = 'test-object.txt'
        
        mock_response = {
            'ContentLength': 1024,
            'ContentType': 'text/plain',
            'LastModified': '2023-01-01T00:00:00.000Z',
            'ETag': '"abc123"',
            'Metadata': {'custom-key': 'custom-value'},
            'StorageClass': 'STANDARD'
        }
        
        s3_manager.s3_client.head_object.return_value = mock_response
        
        metadata = s3_manager.get_object_metadata(bucket_name, object_key)
        
        assert metadata['ContentLength'] == 1024
        assert metadata['ContentType'] == 'text/plain'
        assert metadata['Metadata']['custom-key'] == 'custom-value'
        assert metadata['StorageClass'] == 'STANDARD'
    
    def test_generate_presigned_url_success(self, s3_manager):
        """Test successful presigned URL generation."""
        bucket_name = 'test-bucket'
        object_key = 'test-object.txt'
        
        expected_url = 'https://test-bucket.s3.amazonaws.com/test-object.txt?...'
        s3_manager.s3_client.generate_presigned_url.return_value = expected_url
        
        url = s3_manager.generate_presigned_url(bucket_name, object_key)
        
        assert url == expected_url
        s3_manager.s3_client.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=3600
        )
    
    def test_set_bucket_policy_success(self, s3_manager):
        """Test successful bucket policy setting."""
        bucket_name = 'test-bucket'
        policy = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Principal': '*',
                    'Action': 's3:GetObject',
                    'Resource': f'arn:aws:s3:::{bucket_name}/*'
                }
            ]
        }
        
        s3_manager.s3_client.put_bucket_policy.return_value = {}
        
        result = s3_manager.set_bucket_policy(bucket_name, policy)
        
        assert result is True
        
        # Verify the policy was JSON-encoded correctly
        call_args = s3_manager.s3_client.put_bucket_policy.call_args
        assert call_args[1]['Bucket'] == bucket_name
        
        import json
        policy_json = call_args[1]['Policy']
        parsed_policy = json.loads(policy_json)
        assert parsed_policy == policy
    
    def test_delete_all_objects_success(self, s3_manager):
        """Test successful deletion of all objects."""
        bucket_name = 'test-bucket'
        
        # Mock list_objects to return some objects
        mock_objects = [
            {'Key': 'object1.txt', 'Size': 1024},
            {'Key': 'object2.txt', 'Size': 2048}
        ]
        
        with patch.object(s3_manager, 'list_objects', return_value=mock_objects):
            mock_delete_response = {
                'Deleted': [
                    {'Key': 'object1.txt'},
                    {'Key': 'object2.txt'}
                ]
            }
            s3_manager.s3_client.delete_objects.return_value = mock_delete_response
            
            deleted_count = s3_manager.delete_all_objects(bucket_name)
            
            assert deleted_count == 2
            s3_manager.s3_client.delete_objects.assert_called_once()
    
    def test_client_error_handling(self, s3_manager):
        """Test client error handling."""
        s3_manager.s3_client.list_buckets.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'ListBuckets'
        )
        
        with pytest.raises(ClientError):
            s3_manager.list_buckets()