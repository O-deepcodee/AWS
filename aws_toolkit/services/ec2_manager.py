"""
EC2 management service for AWS Toolkit.
"""

import boto3
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError, BotoCoreError
from ..core.config import Config
from ..utils.logger import get_logger


class EC2Manager:
    """Manages EC2 instances and related resources."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize EC2 manager.

        Args:
            config: Configuration instance
        """
        self.config = config or Config()
        self.logger = get_logger(__name__, self.config.get("app.log_level"))

        try:
            self.ec2_client = boto3.client("ec2", **self.config.aws_config)
            self.ec2_resource = boto3.resource("ec2", **self.config.aws_config)
        except Exception as e:
            self.logger.error(f"Failed to initialize EC2 client: {e}")
            raise

    def list_instances(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """List EC2 instances.

        Args:
            filters: Optional filters for instances

        Returns:
            List of instance information
        """
        try:
            params = {}
            if filters:
                params["Filters"] = [
                    {"Name": k, "Values": v if isinstance(v, list) else [v]}
                    for k, v in filters.items()
                ]

            response = self.ec2_client.describe_instances(**params)
            instances = []

            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    instances.append(
                        {
                            "InstanceId": instance["InstanceId"],
                            "InstanceType": instance["InstanceType"],
                            "State": instance["State"]["Name"],
                            "LaunchTime": instance.get("LaunchTime"),
                            "PublicIpAddress": instance.get("PublicIpAddress"),
                            "PrivateIpAddress": instance.get("PrivateIpAddress"),
                            "Tags": {
                                tag["Key"]: tag["Value"]
                                for tag in instance.get("Tags", [])
                            },
                        }
                    )

            self.logger.info(f"Found {len(instances)} instances")
            return instances

        except ClientError as e:
            self.logger.error(f"Failed to list instances: {e}")
            raise

    def create_instance(
        self,
        instance_type: str,
        image_id: str,
        key_name: Optional[str] = None,
        security_groups: Optional[List[str]] = None,
        subnet_id: Optional[str] = None,
        user_data: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a new EC2 instance.

        Args:
            instance_type: EC2 instance type (e.g., 't2.micro')
            image_id: AMI ID to launch
            key_name: SSH key pair name
            security_groups: List of security group IDs
            subnet_id: Subnet ID for VPC instances
            user_data: User data script
            tags: Instance tags

        Returns:
            Instance information
        """
        try:
            params = {
                "ImageId": image_id,
                "MinCount": 1,
                "MaxCount": 1,
                "InstanceType": instance_type,
            }

            if key_name:
                params["KeyName"] = key_name
            elif self.config.get("ec2.key_pair_name"):
                params["KeyName"] = self.config.get("ec2.key_pair_name")

            if security_groups:
                if subnet_id:  # VPC instance
                    params["SecurityGroupIds"] = security_groups
                else:  # EC2-Classic instance
                    params["SecurityGroups"] = security_groups

            if subnet_id:
                params["SubnetId"] = subnet_id

            if user_data:
                params["UserData"] = user_data

            response = self.ec2_client.run_instances(**params)
            instance = response["Instances"][0]

            instance_id = instance["InstanceId"]
            self.logger.info(f"Created instance: {instance_id}")

            # Add tags if provided
            if tags:
                self.add_tags(instance_id, tags)

            return {
                "InstanceId": instance_id,
                "InstanceType": instance["InstanceType"],
                "State": instance["State"]["Name"],
                "ImageId": instance["ImageId"],
            }

        except ClientError as e:
            self.logger.error(f"Failed to create instance: {e}")
            raise

    def terminate_instance(self, instance_id: str) -> bool:
        """Terminate an EC2 instance.

        Args:
            instance_id: Instance ID to terminate

        Returns:
            True if successful
        """
        try:
            self.ec2_client.terminate_instances(InstanceIds=[instance_id])
            self.logger.info(f"Terminated instance: {instance_id}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to terminate instance {instance_id}: {e}")
            raise

    def start_instance(self, instance_id: str) -> bool:
        """Start a stopped EC2 instance.

        Args:
            instance_id: Instance ID to start

        Returns:
            True if successful
        """
        try:
            self.ec2_client.start_instances(InstanceIds=[instance_id])
            self.logger.info(f"Started instance: {instance_id}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to start instance {instance_id}: {e}")
            raise

    def stop_instance(self, instance_id: str) -> bool:
        """Stop a running EC2 instance.

        Args:
            instance_id: Instance ID to stop

        Returns:
            True if successful
        """
        try:
            self.ec2_client.stop_instances(InstanceIds=[instance_id])
            self.logger.info(f"Stopped instance: {instance_id}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to stop instance {instance_id}: {e}")
            raise

    def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """Get instance status information.

        Args:
            instance_id: Instance ID

        Returns:
            Instance status information
        """
        try:
            response = self.ec2_client.describe_instance_status(
                InstanceIds=[instance_id], IncludeAllInstances=True
            )

            if response["InstanceStatuses"]:
                status = response["InstanceStatuses"][0]
                return {
                    "InstanceId": status["InstanceId"],
                    "InstanceState": status["InstanceState"]["Name"],
                    "SystemStatus": status.get("SystemStatus", {}).get("Status"),
                    "InstanceStatus": status.get("InstanceStatus", {}).get("Status"),
                }
            else:
                return {"InstanceId": instance_id, "Status": "Not Found"}

        except ClientError as e:
            self.logger.error(f"Failed to get instance status {instance_id}: {e}")
            raise

    def add_tags(self, instance_id: str, tags: Dict[str, str]) -> bool:
        """Add tags to an EC2 instance.

        Args:
            instance_id: Instance ID
            tags: Dictionary of tags to add

        Returns:
            True if successful
        """
        try:
            tag_list = [{"Key": k, "Value": v} for k, v in tags.items()]
            self.ec2_client.create_tags(Resources=[instance_id], Tags=tag_list)
            self.logger.info(f"Added tags to instance {instance_id}: {tags}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to add tags to instance {instance_id}: {e}")
            raise

    def create_security_group(
        self, group_name: str, description: str, vpc_id: Optional[str] = None
    ) -> str:
        """Create a new security group.

        Args:
            group_name: Security group name
            description: Security group description
            vpc_id: VPC ID (optional, for VPC security groups)

        Returns:
            Security group ID
        """
        try:
            params = {"GroupName": group_name, "Description": description}

            if vpc_id:
                params["VpcId"] = vpc_id

            response = self.ec2_client.create_security_group(**params)
            group_id = response["GroupId"]

            self.logger.info(f"Created security group: {group_id}")
            return group_id

        except ClientError as e:
            self.logger.error(f"Failed to create security group: {e}")
            raise

    def create_key_pair(
        self, key_name: str, save_path: Optional[str] = None
    ) -> Dict[str, str]:
        """Create a new EC2 key pair.

        Args:
            key_name: Key pair name
            save_path: Optional path to save private key

        Returns:
            Key pair information
        """
        try:
            response = self.ec2_client.create_key_pair(KeyName=key_name)

            key_info = {
                "KeyName": response["KeyName"],
                "KeyFingerprint": response["KeyFingerprint"],
                "KeyMaterial": response["KeyMaterial"],
            }

            # Save private key if path provided
            if save_path:
                with open(save_path, "w") as f:
                    f.write(response["KeyMaterial"])
                # Set proper permissions
                import os

                os.chmod(save_path, 0o600)
                self.logger.info(f"Saved private key to: {save_path}")

            self.logger.info(f"Created key pair: {key_name}")
            return key_info

        except ClientError as e:
            self.logger.error(f"Failed to create key pair: {e}")
            raise
