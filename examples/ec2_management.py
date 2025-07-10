#!/usr/bin/env python3
"""
Example script for EC2 instance management.
"""

import time
from aws_toolkit import EC2Manager, Config, get_logger


def create_and_manage_instance():
    """Example of creating and managing an EC2 instance."""
    config = Config()
    logger = get_logger(__name__)
    ec2 = EC2Manager(config)
    
    logger.info("EC2 Instance Management Example")
    
    try:
        # Create a new instance (using Amazon Linux 2 AMI)
        # Note: You'll need to replace this AMI ID with a valid one for your region
        ami_id = "ami-0c02fb55956c7d316"  # Amazon Linux 2 (us-east-1)
        instance_type = "t2.micro"
        
        logger.info(f"Creating new instance: {instance_type}")
        
        tags = {
            "Name": "AWS-Toolkit-Example",
            "Environment": "Demo",
            "Project": "AWS-Toolkit"
        }
        
        instance = ec2.create_instance(
            instance_type=instance_type,
            image_id=ami_id,
            tags=tags
        )
        
        instance_id = instance['InstanceId']
        logger.info(f"Created instance: {instance_id}")
        
        # Wait for instance to be running
        logger.info("Waiting for instance to be running...")
        max_attempts = 30
        for attempt in range(max_attempts):
            status = ec2.get_instance_status(instance_id)
            state = status.get('InstanceState', 'unknown')
            logger.info(f"Instance state: {state}")
            
            if state == 'running':
                logger.info("Instance is now running!")
                break
            elif state in ['terminated', 'stopping', 'stopped']:
                logger.error(f"Instance is in unexpected state: {state}")
                break
            
            time.sleep(10)
        else:
            logger.warning("Instance did not reach running state within timeout")
        
        # Get final status
        final_status = ec2.get_instance_status(instance_id)
        logger.info(f"Final instance status: {final_status}")
        
        # Add additional tags
        additional_tags = {
            "Status": "Active",
            "LastModified": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        ec2.add_tags(instance_id, additional_tags)
        logger.info("Added additional tags")
        
        # Stop the instance
        logger.info("Stopping instance...")
        ec2.stop_instance(instance_id)
        
        # Wait a bit
        time.sleep(5)
        
        # Get updated status
        status = ec2.get_instance_status(instance_id)
        logger.info(f"Instance status after stop: {status}")
        
        # Start it again
        logger.info("Starting instance...")
        ec2.start_instance(instance_id)
        
        logger.info("Example completed! Remember to terminate the instance when done.")
        logger.info(f"To terminate: aws-toolkit ec2 terminate {instance_id}")
        
        return instance_id
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        return None


def list_and_filter_instances():
    """Example of listing and filtering instances."""
    config = Config()
    logger = get_logger(__name__)
    ec2 = EC2Manager(config)
    
    logger.info("=== Listing All Instances ===")
    all_instances = ec2.list_instances()
    
    for instance in all_instances:
        logger.info(f"ID: {instance['InstanceId']}")
        logger.info(f"  Type: {instance['InstanceType']}")
        logger.info(f"  State: {instance['State']}")
        logger.info(f"  Tags: {instance['Tags']}")
        logger.info("  ---")
    
    logger.info("=== Filtering Running Instances ===")
    running_instances = ec2.list_instances({"instance-state-name": "running"})
    logger.info(f"Found {len(running_instances)} running instances")
    
    logger.info("=== Filtering by Tag ===")
    tagged_instances = ec2.list_instances({"tag:Environment": "Demo"})
    logger.info(f"Found {len(tagged_instances)} instances with Environment=Demo tag")


def main():
    """Main function."""
    logger = get_logger(__name__)
    
    # First, list existing instances
    list_and_filter_instances()
    
    # Ask user if they want to create a new instance
    print("\nDo you want to create a new demo instance? (y/N): ", end="")
    response = input().strip().lower()
    
    if response in ['y', 'yes']:
        instance_id = create_and_manage_instance()
        if instance_id:
            print(f"\nCreated instance: {instance_id}")
            print(f"To terminate it later, run: aws-toolkit ec2 terminate {instance_id}")
    else:
        logger.info("Skipping instance creation")


if __name__ == "__main__":
    main()