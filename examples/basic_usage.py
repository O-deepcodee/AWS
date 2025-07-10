#!/usr/bin/env python3
"""
Example script showing basic AWS Toolkit usage.
"""

from aws_toolkit import EC2Manager, S3Manager, LambdaManager, Config, get_logger


def main():
    """Main example function."""
    # Initialize configuration and logging
    config = Config()
    logger = get_logger(__name__)
    
    logger.info("AWS Toolkit Basic Example")
    
    try:
        # EC2 Example
        logger.info("=== EC2 Examples ===")
        ec2 = EC2Manager(config)
        
        # List instances
        instances = ec2.list_instances()
        logger.info(f"Found {len(instances)} EC2 instances")
        
        for instance in instances[:3]:  # Show first 3
            logger.info(f"Instance: {instance['InstanceId']} ({instance['State']})")
        
        # S3 Example
        logger.info("=== S3 Examples ===")
        s3 = S3Manager(config)
        
        # List buckets
        buckets = s3.list_buckets()
        logger.info(f"Found {len(buckets)} S3 buckets")
        
        for bucket in buckets[:3]:  # Show first 3
            logger.info(f"Bucket: {bucket['Name']}")
        
        # Lambda Example
        logger.info("=== Lambda Examples ===")
        lambda_mgr = LambdaManager(config)
        
        # List functions
        functions = lambda_mgr.list_functions()
        logger.info(f"Found {len(functions)} Lambda functions")
        
        for function in functions[:3]:  # Show first 3
            logger.info(f"Function: {function['FunctionName']} ({function['Runtime']})")
        
        logger.info("Example completed successfully!")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        logger.info("Make sure your AWS credentials are configured properly")
        logger.info("You can configure them using:")
        logger.info("  - AWS CLI: aws configure")
        logger.info("  - Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        logger.info("  - .env file in the project root")


if __name__ == "__main__":
    main()