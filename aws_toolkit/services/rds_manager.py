"""
RDS management service for AWS Toolkit.
"""

import boto3
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError
from ..core.config import Config
from ..utils.logger import get_logger


class RDSManager:
    """Manages RDS database instances and clusters."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize RDS manager.

        Args:
            config: Configuration instance
        """
        self.config = config or Config()
        self.logger = get_logger(__name__, self.config.get("app.log_level"))

        try:
            self.rds_client = boto3.client("rds", **self.config.aws_config)
        except Exception as e:
            self.logger.error(f"Failed to initialize RDS client: {e}")
            raise

    def list_instances(self) -> List[Dict[str, Any]]:
        """List all RDS instances.

        Returns:
            List of instance information
        """
        try:
            response = self.rds_client.describe_db_instances()
            instances = []

            for instance in response["DBInstances"]:
                instances.append(
                    {
                        "DBInstanceIdentifier": instance["DBInstanceIdentifier"],
                        "DBInstanceClass": instance["DBInstanceClass"],
                        "Engine": instance["Engine"],
                        "EngineVersion": instance["EngineVersion"],
                        "DBInstanceStatus": instance["DBInstanceStatus"],
                        "AllocatedStorage": instance["AllocatedStorage"],
                        "StorageType": instance.get("StorageType"),
                        "Endpoint": instance.get("Endpoint", {}).get("Address"),
                        "Port": instance.get("Endpoint", {}).get("Port"),
                        "MultiAZ": instance.get("MultiAZ", False),
                        "BackupRetentionPeriod": instance.get(
                            "BackupRetentionPeriod", 0
                        ),
                    }
                )

            self.logger.info(f"Found {len(instances)} RDS instances")
            return instances

        except ClientError as e:
            self.logger.error(f"Failed to list RDS instances: {e}")
            raise

    def create_instance(
        self,
        db_instance_identifier: str,
        db_instance_class: str,
        engine: str,
        master_username: str,
        master_password: str,
        allocated_storage: int = 20,
        db_name: Optional[str] = None,
        vpc_security_group_ids: Optional[List[str]] = None,
        subnet_group_name: Optional[str] = None,
        storage_type: str = "gp2",
        multi_az: bool = False,
        backup_retention_period: int = 7,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a new RDS instance.

        Args:
            db_instance_identifier: DB instance identifier
            db_instance_class: DB instance class (e.g., 'db.t3.micro')
            engine: Database engine (e.g., 'mysql', 'postgres')
            master_username: Master username
            master_password: Master password
            allocated_storage: Allocated storage in GB
            db_name: Initial database name
            vpc_security_group_ids: VPC security group IDs
            subnet_group_name: DB subnet group name
            storage_type: Storage type ('gp2', 'io1', etc.)
            multi_az: Enable Multi-AZ deployment
            backup_retention_period: Backup retention period in days
            tags: Instance tags

        Returns:
            Instance information
        """
        try:
            params = {
                "DBInstanceIdentifier": db_instance_identifier,
                "DBInstanceClass": db_instance_class,
                "Engine": engine,
                "MasterUsername": master_username,
                "MasterUserPassword": master_password,
                "AllocatedStorage": allocated_storage,
                "StorageType": storage_type,
                "MultiAZ": multi_az,
                "BackupRetentionPeriod": backup_retention_period,
            }

            if db_name:
                params["DBName"] = db_name

            if vpc_security_group_ids:
                params["VpcSecurityGroupIds"] = vpc_security_group_ids

            if subnet_group_name:
                params["DBSubnetGroupName"] = subnet_group_name

            if tags:
                tag_list = [{"Key": k, "Value": v} for k, v in tags.items()]
                params["Tags"] = tag_list

            response = self.rds_client.create_db_instance(**params)
            instance = response["DBInstance"]

            self.logger.info(f"Created RDS instance: {db_instance_identifier}")
            return {
                "DBInstanceIdentifier": instance["DBInstanceIdentifier"],
                "DBInstanceClass": instance["DBInstanceClass"],
                "Engine": instance["Engine"],
                "DBInstanceStatus": instance["DBInstanceStatus"],
                "AllocatedStorage": instance["AllocatedStorage"],
            }

        except ClientError as e:
            self.logger.error(f"Failed to create RDS instance: {e}")
            raise

    def delete_instance(
        self,
        db_instance_identifier: str,
        skip_final_snapshot: bool = True,
        final_snapshot_identifier: Optional[str] = None,
    ) -> bool:
        """Delete an RDS instance.

        Args:
            db_instance_identifier: DB instance identifier
            skip_final_snapshot: Skip final snapshot
            final_snapshot_identifier: Final snapshot identifier

        Returns:
            True if successful
        """
        try:
            params = {
                "DBInstanceIdentifier": db_instance_identifier,
                "SkipFinalSnapshot": skip_final_snapshot,
            }

            if not skip_final_snapshot and final_snapshot_identifier:
                params["FinalDBSnapshotIdentifier"] = final_snapshot_identifier

            self.rds_client.delete_db_instance(**params)
            self.logger.info(f"Deleted RDS instance: {db_instance_identifier}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to delete RDS instance: {e}")
            raise

    def start_instance(self, db_instance_identifier: str) -> bool:
        """Start a stopped RDS instance.

        Args:
            db_instance_identifier: DB instance identifier

        Returns:
            True if successful
        """
        try:
            self.rds_client.start_db_instance(
                DBInstanceIdentifier=db_instance_identifier
            )
            self.logger.info(f"Started RDS instance: {db_instance_identifier}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to start RDS instance: {e}")
            raise

    def stop_instance(self, db_instance_identifier: str) -> bool:
        """Stop a running RDS instance.

        Args:
            db_instance_identifier: DB instance identifier

        Returns:
            True if successful
        """
        try:
            self.rds_client.stop_db_instance(
                DBInstanceIdentifier=db_instance_identifier
            )
            self.logger.info(f"Stopped RDS instance: {db_instance_identifier}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to stop RDS instance: {e}")
            raise

    def create_snapshot(
        self, db_instance_identifier: str, snapshot_identifier: str
    ) -> Dict[str, Any]:
        """Create a manual snapshot of an RDS instance.

        Args:
            db_instance_identifier: Source DB instance identifier
            snapshot_identifier: Snapshot identifier

        Returns:
            Snapshot information
        """
        try:
            response = self.rds_client.create_db_snapshot(
                DBSnapshotIdentifier=snapshot_identifier,
                DBInstanceIdentifier=db_instance_identifier,
            )

            snapshot = response["DBSnapshot"]
            self.logger.info(f"Created snapshot: {snapshot_identifier}")

            return {
                "DBSnapshotIdentifier": snapshot["DBSnapshotIdentifier"],
                "DBInstanceIdentifier": snapshot["DBInstanceIdentifier"],
                "Status": snapshot["Status"],
                "AllocatedStorage": snapshot["AllocatedStorage"],
            }

        except ClientError as e:
            self.logger.error(f"Failed to create snapshot: {e}")
            raise

    def restore_from_snapshot(
        self,
        db_instance_identifier: str,
        snapshot_identifier: str,
        db_instance_class: str,
    ) -> Dict[str, Any]:
        """Restore RDS instance from snapshot.

        Args:
            db_instance_identifier: New DB instance identifier
            snapshot_identifier: Source snapshot identifier
            db_instance_class: DB instance class for restored instance

        Returns:
            Restored instance information
        """
        try:
            response = self.rds_client.restore_db_instance_from_db_snapshot(
                DBInstanceIdentifier=db_instance_identifier,
                DBSnapshotIdentifier=snapshot_identifier,
                DBInstanceClass=db_instance_class,
            )

            instance = response["DBInstance"]
            self.logger.info(
                f"Restored instance from snapshot: {db_instance_identifier}"
            )

            return {
                "DBInstanceIdentifier": instance["DBInstanceIdentifier"],
                "DBInstanceClass": instance["DBInstanceClass"],
                "Engine": instance["Engine"],
                "DBInstanceStatus": instance["DBInstanceStatus"],
            }

        except ClientError as e:
            self.logger.error(f"Failed to restore from snapshot: {e}")
            raise

    def list_snapshots(
        self, db_instance_identifier: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List RDS snapshots.

        Args:
            db_instance_identifier: Filter by DB instance (optional)

        Returns:
            List of snapshot information
        """
        try:
            params = {}
            if db_instance_identifier:
                params["DBInstanceIdentifier"] = db_instance_identifier

            response = self.rds_client.describe_db_snapshots(**params)
            snapshots = []

            for snapshot in response["DBSnapshots"]:
                snapshots.append(
                    {
                        "DBSnapshotIdentifier": snapshot["DBSnapshotIdentifier"],
                        "DBInstanceIdentifier": snapshot["DBInstanceIdentifier"],
                        "Status": snapshot["Status"],
                        "SnapshotCreateTime": snapshot.get("SnapshotCreateTime"),
                        "AllocatedStorage": snapshot["AllocatedStorage"],
                        "SnapshotType": snapshot["SnapshotType"],
                    }
                )

            self.logger.info(f"Found {len(snapshots)} snapshots")
            return snapshots

        except ClientError as e:
            self.logger.error(f"Failed to list snapshots: {e}")
            raise

    def modify_instance(
        self,
        db_instance_identifier: str,
        db_instance_class: Optional[str] = None,
        allocated_storage: Optional[int] = None,
        apply_immediately: bool = False,
    ) -> bool:
        """Modify an RDS instance.

        Args:
            db_instance_identifier: DB instance identifier
            db_instance_class: New DB instance class
            allocated_storage: New allocated storage
            apply_immediately: Apply changes immediately

        Returns:
            True if successful
        """
        try:
            params = {
                "DBInstanceIdentifier": db_instance_identifier,
                "ApplyImmediately": apply_immediately,
            }

            if db_instance_class:
                params["DBInstanceClass"] = db_instance_class

            if allocated_storage:
                params["AllocatedStorage"] = allocated_storage

            self.rds_client.modify_db_instance(**params)
            self.logger.info(f"Modified RDS instance: {db_instance_identifier}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to modify RDS instance: {e}")
            raise

    def get_instance_status(self, db_instance_identifier: str) -> Dict[str, Any]:
        """Get RDS instance status.

        Args:
            db_instance_identifier: DB instance identifier

        Returns:
            Instance status information
        """
        try:
            response = self.rds_client.describe_db_instances(
                DBInstanceIdentifier=db_instance_identifier
            )

            if response["DBInstances"]:
                instance = response["DBInstances"][0]
                return {
                    "DBInstanceIdentifier": instance["DBInstanceIdentifier"],
                    "DBInstanceStatus": instance["DBInstanceStatus"],
                    "Engine": instance["Engine"],
                    "Endpoint": instance.get("Endpoint", {}).get("Address"),
                    "Port": instance.get("Endpoint", {}).get("Port"),
                }
            else:
                return {
                    "DBInstanceIdentifier": db_instance_identifier,
                    "Status": "Not Found",
                }

        except ClientError as e:
            self.logger.error(f"Failed to get instance status: {e}")
            raise
