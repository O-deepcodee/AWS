"""
Tests for Config class.
"""

import os
import tempfile
import yaml
import pytest
from aws_toolkit.core.config import Config


class TestConfig:
    """Test cases for Config class."""
    
    def test_init_without_config_file(self):
        """Test initialization without config file."""
        config = Config()
        assert config is not None
        assert config.get('aws.region') == 'us-east-1'  # default
    
    def test_init_with_env_vars(self, temp_env_vars):
        """Test initialization with environment variables."""
        config = Config()
        assert config.get('aws.access_key_id') == 'test_key'
        assert config.get('aws.secret_access_key') == 'test_secret'
        assert config.get('aws.region') == 'us-west-2'
    
    def test_init_with_config_file(self):
        """Test initialization with config file."""
        test_config = {
            'aws': {
                'region': 'eu-west-1'
            },
            'app': {
                'log_level': 'DEBUG'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            config_file = f.name
        
        try:
            config = Config(config_file)
            assert config.get('aws.region') == 'eu-west-1'
            assert config.get('app.log_level') == 'DEBUG'
        finally:
            os.unlink(config_file)
    
    def test_get_method(self):
        """Test get method with dot notation."""
        config = Config()
        
        # Test existing key
        assert config.get('aws.region') is not None
        
        # Test non-existing key with default
        assert config.get('non.existing.key', 'default') == 'default'
        
        # Test non-existing key without default
        assert config.get('non.existing.key') is None
    
    def test_set_method(self):
        """Test set method with dot notation."""
        config = Config()
        
        config.set('test.nested.value', 'test_value')
        assert config.get('test.nested.value') == 'test_value'
    
    def test_to_dict(self):
        """Test to_dict method."""
        config = Config()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'aws' in config_dict
        assert 'app' in config_dict
    
    def test_aws_config_property(self, temp_env_vars):
        """Test aws_config property."""
        config = Config()
        aws_config = config.aws_config
        
        assert 'aws_access_key_id' in aws_config
        assert 'aws_secret_access_key' in aws_config
        assert 'region_name' in aws_config
        assert aws_config['aws_access_key_id'] == 'test_key'
        assert aws_config['region_name'] == 'us-west-2'
    
    def test_invalid_yaml_config_file(self):
        """Test handling of invalid YAML config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_file = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                Config(config_file)
        finally:
            os.unlink(config_file)
    
    def test_merge_config(self):
        """Test configuration merging."""
        base_config = {
            'aws': {
                'region': 'us-east-1',
                'access_key_id': 'base_key'
            },
            'app': {
                'log_level': 'INFO'
            }
        }
        
        overlay_config = {
            'aws': {
                'region': 'eu-west-1'  # Override region
            },
            'new_section': {
                'new_value': 'test'
            }
        }
        
        config = Config()
        config._config = base_config.copy()
        config._merge_config(config._config, overlay_config)
        
        # Check override
        assert config._config['aws']['region'] == 'eu-west-1'
        # Check preserved value
        assert config._config['aws']['access_key_id'] == 'base_key'
        # Check new section
        assert config._config['new_section']['new_value'] == 'test'