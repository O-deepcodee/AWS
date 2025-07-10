"""
Tests for EC2Manager class.
"""

import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError
from aws_toolkit.services.ec2_manager import EC2Manager
from aws_toolkit.core.config import Config


class TestEC2Manager:
    """Test cases for EC2Manager class."""
    
    @pytest.fixture
    def ec2_manager(self, mock_boto3_client, mock_boto3_resource):
        """EC2Manager instance for testing."""
        config = Config()
        return EC2Manager(config)
    
    def test_init_success(self, mock_boto3_client, mock_boto3_resource):
        """Test successful initialization."""
        config = Config()
        manager = EC2Manager(config)
        assert manager is not None
        assert hasattr(manager, 'ec2_client')
        assert hasattr(manager, 'ec2_resource')
    
    def test_init_failure(self):
        """Test initialization failure."""
        with patch('boto3.client', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                EC2Manager()
    
    def test_list_instances_success(self, ec2_manager):
        """Test successful instance listing."""
        mock_response = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-1234567890abcdef0',
                            'InstanceType': 't2.micro',
                            'State': {'Name': 'running'},
                            'LaunchTime': '2023-01-01T00:00:00.000Z',
                            'PublicIpAddress': '1.2.3.4',
                            'PrivateIpAddress': '10.0.0.1',
                            'Tags': [
                                {'Key': 'Name', 'Value': 'Test Instance'}
                            ]
                        }
                    ]
                }
            ]
        }
        
        ec2_manager.ec2_client.describe_instances.return_value = mock_response
        
        instances = ec2_manager.list_instances()
        
        assert len(instances) == 1
        assert instances[0]['InstanceId'] == 'i-1234567890abcdef0'
        assert instances[0]['InstanceType'] == 't2.micro'
        assert instances[0]['State'] == 'running'
        assert instances[0]['Tags']['Name'] == 'Test Instance'
    
    def test_list_instances_with_filters(self, ec2_manager):
        """Test instance listing with filters."""
        filters = {'instance-state-name': 'running'}
        
        ec2_manager.ec2_client.describe_instances.return_value = {
            'Reservations': []
        }
        
        ec2_manager.list_instances(filters)
        
        ec2_manager.ec2_client.describe_instances.assert_called_once_with(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
    
    def test_list_instances_client_error(self, ec2_manager):
        """Test instance listing with client error."""
        ec2_manager.ec2_client.describe_instances.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'DescribeInstances'
        )
        
        with pytest.raises(ClientError):
            ec2_manager.list_instances()
    
    def test_create_instance_success(self, ec2_manager):
        """Test successful instance creation."""
        mock_response = {
            'Instances': [
                {
                    'InstanceId': 'i-1234567890abcdef0',
                    'InstanceType': 't2.micro',
                    'State': {'Name': 'pending'},
                    'ImageId': 'ami-12345678'
                }
            ]
        }
        
        ec2_manager.ec2_client.run_instances.return_value = mock_response
        
        instance = ec2_manager.create_instance('t2.micro', 'ami-12345678')
        
        assert instance['InstanceId'] == 'i-1234567890abcdef0'
        assert instance['InstanceType'] == 't2.micro'
        assert instance['State'] == 'pending'
        
        ec2_manager.ec2_client.run_instances.assert_called_once()
    
    def test_create_instance_with_tags(self, ec2_manager):
        """Test instance creation with tags."""
        mock_response = {
            'Instances': [
                {
                    'InstanceId': 'i-1234567890abcdef0',
                    'InstanceType': 't2.micro',
                    'State': {'Name': 'pending'},
                    'ImageId': 'ami-12345678'
                }
            ]
        }
        
        ec2_manager.ec2_client.run_instances.return_value = mock_response
        ec2_manager.ec2_client.create_tags.return_value = {}
        
        tags = {'Name': 'Test Instance', 'Environment': 'Test'}
        instance = ec2_manager.create_instance(
            't2.micro', 'ami-12345678', tags=tags
        )
        
        assert instance['InstanceId'] == 'i-1234567890abcdef0'
        ec2_manager.ec2_client.create_tags.assert_called_once()
    
    def test_terminate_instance_success(self, ec2_manager):
        """Test successful instance termination."""
        instance_id = 'i-1234567890abcdef0'
        
        ec2_manager.ec2_client.terminate_instances.return_value = {}
        
        result = ec2_manager.terminate_instance(instance_id)
        
        assert result is True
        ec2_manager.ec2_client.terminate_instances.assert_called_once_with(
            InstanceIds=[instance_id]
        )
    
    def test_start_instance_success(self, ec2_manager):
        """Test successful instance start."""
        instance_id = 'i-1234567890abcdef0'
        
        ec2_manager.ec2_client.start_instances.return_value = {}
        
        result = ec2_manager.start_instance(instance_id)
        
        assert result is True
        ec2_manager.ec2_client.start_instances.assert_called_once_with(
            InstanceIds=[instance_id]
        )
    
    def test_stop_instance_success(self, ec2_manager):
        """Test successful instance stop."""
        instance_id = 'i-1234567890abcdef0'
        
        ec2_manager.ec2_client.stop_instances.return_value = {}
        
        result = ec2_manager.stop_instance(instance_id)
        
        assert result is True
        ec2_manager.ec2_client.stop_instances.assert_called_once_with(
            InstanceIds=[instance_id]
        )
    
    def test_get_instance_status(self, ec2_manager):
        """Test getting instance status."""
        instance_id = 'i-1234567890abcdef0'
        
        mock_response = {
            'InstanceStatuses': [
                {
                    'InstanceId': instance_id,
                    'InstanceState': {'Name': 'running'},
                    'SystemStatus': {'Status': 'ok'},
                    'InstanceStatus': {'Status': 'ok'}
                }
            ]
        }
        
        ec2_manager.ec2_client.describe_instance_status.return_value = mock_response
        
        status = ec2_manager.get_instance_status(instance_id)
        
        assert status['InstanceId'] == instance_id
        assert status['InstanceState'] == 'running'
        assert status['SystemStatus'] == 'ok'
        assert status['InstanceStatus'] == 'ok'
    
    def test_add_tags_success(self, ec2_manager):
        """Test successful tag addition."""
        instance_id = 'i-1234567890abcdef0'
        tags = {'Name': 'Test Instance', 'Environment': 'Test'}
        
        ec2_manager.ec2_client.create_tags.return_value = {}
        
        result = ec2_manager.add_tags(instance_id, tags)
        
        assert result is True
        
        # Verify the call was made with correct parameters
        call_args = ec2_manager.ec2_client.create_tags.call_args
        assert call_args[1]['Resources'] == [instance_id]
        
        # Check that tags were converted correctly
        expected_tags = [
            {'Key': 'Name', 'Value': 'Test Instance'},
            {'Key': 'Environment', 'Value': 'Test'}
        ]
        actual_tags = call_args[1]['Tags']
        assert len(actual_tags) == 2
        assert all(tag in actual_tags for tag in expected_tags)
    
    def test_create_security_group_success(self, ec2_manager):
        """Test successful security group creation."""
        group_name = 'test-sg'
        description = 'Test security group'
        
        mock_response = {'GroupId': 'sg-12345678'}
        ec2_manager.ec2_client.create_security_group.return_value = mock_response
        
        group_id = ec2_manager.create_security_group(group_name, description)
        
        assert group_id == 'sg-12345678'
        ec2_manager.ec2_client.create_security_group.assert_called_once_with(
            GroupName=group_name,
            Description=description
        )
    
    def test_create_key_pair_success(self, ec2_manager):
        """Test successful key pair creation."""
        key_name = 'test-keypair'
        
        mock_response = {
            'KeyName': key_name,
            'KeyFingerprint': 'aa:bb:cc:dd:ee:ff',
            'KeyMaterial': '-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----'
        }
        
        ec2_manager.ec2_client.create_key_pair.return_value = mock_response
        
        key_info = ec2_manager.create_key_pair(key_name)
        
        assert key_info['KeyName'] == key_name
        assert 'KeyFingerprint' in key_info
        assert 'KeyMaterial' in key_info
        
        ec2_manager.ec2_client.create_key_pair.assert_called_once_with(
            KeyName=key_name
        )