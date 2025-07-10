"""
Core configuration management for AWS Toolkit.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration manager for AWS Toolkit."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_file: Path to configuration file (optional)
        """
        self._config = {}
        self._load_env_vars()

        if config_file:
            self._load_config_file(config_file)

    def _load_env_vars(self):
        """Load environment variables."""
        # Load .env file if it exists
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)

        # AWS Configuration
        self._config.update(
            {
                "aws": {
                    "access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
                    "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
                    "session_token": os.getenv("AWS_SESSION_TOKEN"),
                    "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
                    "profile": os.getenv("AWS_PROFILE"),
                },
                "app": {
                    "log_level": os.getenv("LOG_LEVEL", "INFO"),
                    "debug": os.getenv("DEBUG", "false").lower() == "true",
                },
                "s3": {
                    "bucket_prefix": os.getenv("S3_BUCKET_PREFIX", "aws-toolkit-"),
                    "encryption": os.getenv("S3_ENCRYPTION", "AES256"),
                },
                "ec2": {
                    "key_pair_name": os.getenv(
                        "EC2_KEY_PAIR_NAME", "aws-toolkit-keypair"
                    ),
                    "security_group": os.getenv("EC2_SECURITY_GROUP", "aws-toolkit-sg"),
                },
                "lambda": {
                    "timeout": int(os.getenv("LAMBDA_TIMEOUT", "30")),
                    "memory_size": int(os.getenv("LAMBDA_MEMORY_SIZE", "128")),
                },
            }
        )

    def _load_config_file(self, config_file: str):
        """Load configuration from YAML file.

        Args:
            config_file: Path to YAML configuration file
        """
        try:
            with open(config_file, "r") as f:
                file_config = yaml.safe_load(f)
                self._merge_config(self._config, file_config)
        except FileNotFoundError:
            pass  # Config file is optional
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")

    def _merge_config(self, base: Dict[str, Any], overlay: Dict[str, Any]):
        """Merge configuration dictionaries.

        Args:
            base: Base configuration dictionary
            overlay: Configuration to merge on top
        """
        for key, value in overlay.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key (dot notation supported)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value.

        Args:
            key: Configuration key (dot notation supported)
            value: Value to set
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary.

        Returns:
            Configuration dictionary
        """
        return self._config.copy()

    @property
    def aws_config(self) -> Dict[str, str]:
        """Get AWS configuration for boto3.

        Returns:
            AWS configuration dictionary
        """
        aws_config = {}

        if self.get("aws.access_key_id"):
            aws_config["aws_access_key_id"] = self.get("aws.access_key_id")

        if self.get("aws.secret_access_key"):
            aws_config["aws_secret_access_key"] = self.get("aws.secret_access_key")

        if self.get("aws.session_token"):
            aws_config["aws_session_token"] = self.get("aws.session_token")

        if self.get("aws.region"):
            aws_config["region_name"] = self.get("aws.region")

        return aws_config
