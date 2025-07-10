"""
IAM management service for AWS Toolkit.
"""

import boto3
import json
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError
from ..core.config import Config
from ..utils.logger import get_logger


class IAMManager:
    """Manages IAM users, roles, and policies."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize IAM manager.

        Args:
            config: Configuration instance
        """
        self.config = config or Config()
        self.logger = get_logger(__name__, self.config.get("app.log_level"))

        try:
            self.iam_client = boto3.client("iam", **self.config.aws_config)
        except Exception as e:
            self.logger.error(f"Failed to initialize IAM client: {e}")
            raise

    def list_users(self) -> List[Dict[str, Any]]:
        """List all IAM users.

        Returns:
            List of user information
        """
        try:
            response = self.iam_client.list_users()
            users = []

            for user in response["Users"]:
                users.append(
                    {
                        "UserName": user["UserName"],
                        "UserId": user["UserId"],
                        "Arn": user["Arn"],
                        "CreateDate": user["CreateDate"],
                        "Path": user["Path"],
                    }
                )

            self.logger.info(f"Found {len(users)} IAM users")
            return users

        except ClientError as e:
            self.logger.error(f"Failed to list users: {e}")
            raise

    def create_user(self, username: str, path: str = "/") -> Dict[str, Any]:
        """Create a new IAM user.

        Args:
            username: Username for the new user
            path: Path for the user (default: '/')

        Returns:
            User information
        """
        try:
            response = self.iam_client.create_user(UserName=username, Path=path)
            user = response["User"]

            self.logger.info(f"Created IAM user: {username}")
            return {
                "UserName": user["UserName"],
                "UserId": user["UserId"],
                "Arn": user["Arn"],
                "CreateDate": user["CreateDate"],
                "Path": user["Path"],
            }

        except ClientError as e:
            self.logger.error(f"Failed to create user {username}: {e}")
            raise

    def delete_user(self, username: str) -> bool:
        """Delete an IAM user.

        Args:
            username: Username to delete

        Returns:
            True if successful
        """
        try:
            # Remove user from all groups
            groups = self.get_user_groups(username)
            for group in groups:
                self.remove_user_from_group(username, group["GroupName"])

            # Detach all policies
            policies = self.list_user_policies(username)
            for policy in policies:
                self.detach_user_policy(username, policy["PolicyArn"])

            # Delete access keys
            access_keys = self.list_access_keys(username)
            for key in access_keys:
                self.delete_access_key(username, key["AccessKeyId"])

            # Delete user
            self.iam_client.delete_user(UserName=username)
            self.logger.info(f"Deleted IAM user: {username}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to delete user {username}: {e}")
            raise

    def create_role(
        self,
        role_name: str,
        assume_role_policy: Dict[str, Any],
        description: Optional[str] = None,
        path: str = "/",
    ) -> Dict[str, Any]:
        """Create a new IAM role.

        Args:
            role_name: Name for the role
            assume_role_policy: Trust policy document
            description: Role description
            path: Path for the role

        Returns:
            Role information
        """
        try:
            params = {
                "RoleName": role_name,
                "AssumeRolePolicyDocument": json.dumps(assume_role_policy),
                "Path": path,
            }

            if description:
                params["Description"] = description

            response = self.iam_client.create_role(**params)
            role = response["Role"]

            self.logger.info(f"Created IAM role: {role_name}")
            return {
                "RoleName": role["RoleName"],
                "RoleId": role["RoleId"],
                "Arn": role["Arn"],
                "CreateDate": role["CreateDate"],
                "Path": role["Path"],
            }

        except ClientError as e:
            self.logger.error(f"Failed to create role {role_name}: {e}")
            raise

    def delete_role(self, role_name: str) -> bool:
        """Delete an IAM role.

        Args:
            role_name: Name of the role to delete

        Returns:
            True if successful
        """
        try:
            # Detach all policies
            policies = self.list_role_policies(role_name)
            for policy in policies:
                self.detach_role_policy(role_name, policy["PolicyArn"])

            # Delete role
            self.iam_client.delete_role(RoleName=role_name)
            self.logger.info(f"Deleted IAM role: {role_name}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to delete role {role_name}: {e}")
            raise

    def attach_user_policy(self, username: str, policy_arn: str) -> bool:
        """Attach a policy to a user.

        Args:
            username: Username
            policy_arn: Policy ARN to attach

        Returns:
            True if successful
        """
        try:
            self.iam_client.attach_user_policy(UserName=username, PolicyArn=policy_arn)
            self.logger.info(f"Attached policy {policy_arn} to user {username}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to attach policy to user: {e}")
            raise

    def detach_user_policy(self, username: str, policy_arn: str) -> bool:
        """Detach a policy from a user.

        Args:
            username: Username
            policy_arn: Policy ARN to detach

        Returns:
            True if successful
        """
        try:
            self.iam_client.detach_user_policy(UserName=username, PolicyArn=policy_arn)
            self.logger.info(f"Detached policy {policy_arn} from user {username}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to detach policy from user: {e}")
            raise

    def attach_role_policy(self, role_name: str, policy_arn: str) -> bool:
        """Attach a policy to a role.

        Args:
            role_name: Role name
            policy_arn: Policy ARN to attach

        Returns:
            True if successful
        """
        try:
            self.iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
            self.logger.info(f"Attached policy {policy_arn} to role {role_name}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to attach policy to role: {e}")
            raise

    def detach_role_policy(self, role_name: str, policy_arn: str) -> bool:
        """Detach a policy from a role.

        Args:
            role_name: Role name
            policy_arn: Policy ARN to detach

        Returns:
            True if successful
        """
        try:
            self.iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
            self.logger.info(f"Detached policy {policy_arn} from role {role_name}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to detach policy from role: {e}")
            raise

    def create_access_key(self, username: str) -> Dict[str, str]:
        """Create access key for a user.

        Args:
            username: Username

        Returns:
            Access key information
        """
        try:
            response = self.iam_client.create_access_key(UserName=username)
            access_key = response["AccessKey"]

            self.logger.info(f"Created access key for user {username}")
            return {
                "AccessKeyId": access_key["AccessKeyId"],
                "SecretAccessKey": access_key["SecretAccessKey"],
                "Status": access_key["Status"],
            }

        except ClientError as e:
            self.logger.error(f"Failed to create access key: {e}")
            raise

    def delete_access_key(self, username: str, access_key_id: str) -> bool:
        """Delete an access key.

        Args:
            username: Username
            access_key_id: Access key ID to delete

        Returns:
            True if successful
        """
        try:
            self.iam_client.delete_access_key(
                UserName=username, AccessKeyId=access_key_id
            )
            self.logger.info(f"Deleted access key {access_key_id} for user {username}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to delete access key: {e}")
            raise

    def list_access_keys(self, username: str) -> List[Dict[str, Any]]:
        """List access keys for a user.

        Args:
            username: Username

        Returns:
            List of access key information
        """
        try:
            response = self.iam_client.list_access_keys(UserName=username)
            return [
                {
                    "AccessKeyId": key["AccessKeyId"],
                    "Status": key["Status"],
                    "CreateDate": key["CreateDate"],
                }
                for key in response["AccessKeyMetadata"]
            ]

        except ClientError as e:
            self.logger.error(f"Failed to list access keys: {e}")
            raise

    def list_user_policies(self, username: str) -> List[Dict[str, Any]]:
        """List policies attached to a user.

        Args:
            username: Username

        Returns:
            List of attached policies
        """
        try:
            response = self.iam_client.list_attached_user_policies(UserName=username)
            return [
                {"PolicyName": policy["PolicyName"], "PolicyArn": policy["PolicyArn"]}
                for policy in response["AttachedPolicies"]
            ]

        except ClientError as e:
            self.logger.error(f"Failed to list user policies: {e}")
            raise

    def list_role_policies(self, role_name: str) -> List[Dict[str, Any]]:
        """List policies attached to a role.

        Args:
            role_name: Role name

        Returns:
            List of attached policies
        """
        try:
            response = self.iam_client.list_attached_role_policies(RoleName=role_name)
            return [
                {"PolicyName": policy["PolicyName"], "PolicyArn": policy["PolicyArn"]}
                for policy in response["AttachedPolicies"]
            ]

        except ClientError as e:
            self.logger.error(f"Failed to list role policies: {e}")
            raise

    def get_user_groups(self, username: str) -> List[Dict[str, Any]]:
        """Get groups for a user.

        Args:
            username: Username

        Returns:
            List of groups the user belongs to
        """
        try:
            response = self.iam_client.get_groups_for_user(UserName=username)
            return [
                {
                    "GroupName": group["GroupName"],
                    "GroupId": group["GroupId"],
                    "Arn": group["Arn"],
                }
                for group in response["Groups"]
            ]

        except ClientError as e:
            self.logger.error(f"Failed to get user groups: {e}")
            raise

    def remove_user_from_group(self, username: str, group_name: str) -> bool:
        """Remove user from a group.

        Args:
            username: Username
            group_name: Group name

        Returns:
            True if successful
        """
        try:
            self.iam_client.remove_user_from_group(
                UserName=username, GroupName=group_name
            )
            self.logger.info(f"Removed user {username} from group {group_name}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to remove user from group: {e}")
            raise
