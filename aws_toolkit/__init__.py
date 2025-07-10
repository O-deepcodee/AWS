"""
AWS Utility Toolkit

A comprehensive Python toolkit for managing AWS services.
"""

__version__ = "1.0.0"
__author__ = "O-deepcodee"
__email__ = "OzqrK@deepcode.com.tr"

from .core.config import Config
from .services.ec2_manager import EC2Manager
from .services.s3_manager import S3Manager
from .services.lambda_manager import LambdaManager
from .services.rds_manager import RDSManager
from .services.iam_manager import IAMManager
from .utils.logger import get_logger

__all__ = [
    "Config",
    "EC2Manager",
    "S3Manager",
    "LambdaManager",
    "RDSManager",
    "IAMManager",
    "get_logger",
]
