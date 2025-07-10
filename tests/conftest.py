"""
Test configuration for AWS Toolkit.
"""

import pytest
import os
from unittest.mock import Mock, patch
from aws_toolkit.core.config import Config


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        'aws': {
            'access_key_id': 'test_access_key',
            'secret_access_key': 'test_secret_key',
            'region': 'us-east-1'
        },
        'app': {
            'log_level': 'INFO',
            'debug': False
        }
    }


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 client."""
    with patch('boto3.client') as mock_client:
        yield mock_client


@pytest.fixture
def mock_boto3_resource():
    """Mock boto3 resource."""
    with patch('boto3.resource') as mock_resource:
        yield mock_resource


@pytest.fixture
def config_instance():
    """Configuration instance for testing."""
    return Config()


@pytest.fixture
def temp_env_vars():
    """Temporary environment variables for testing."""
    original_env = {}
    test_vars = {
        'AWS_ACCESS_KEY_ID': 'test_key',
        'AWS_SECRET_ACCESS_KEY': 'test_secret',
        'AWS_DEFAULT_REGION': 'us-west-2'
    }
    
    # Save original values
    for key in test_vars:
        original_env[key] = os.environ.get(key)
        os.environ[key] = test_vars[key]
    
    yield test_vars
    
    # Restore original values
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value