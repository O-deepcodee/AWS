"""
Lambda management service for AWS Toolkit.
"""

import boto3
import json
import zipfile
import os
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError
from ..core.config import Config
from ..utils.logger import get_logger


class LambdaManager:
    """Manages AWS Lambda functions."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize Lambda manager.

        Args:
            config: Configuration instance
        """
        self.config = config or Config()
        self.logger = get_logger(__name__, self.config.get("app.log_level"))

        try:
            self.lambda_client = boto3.client("lambda", **self.config.aws_config)
        except Exception as e:
            self.logger.error(f"Failed to initialize Lambda client: {e}")
            raise

    def list_functions(self) -> List[Dict[str, Any]]:
        """List all Lambda functions.

        Returns:
            List of function information
        """
        try:
            response = self.lambda_client.list_functions()
            functions = []

            for func in response["Functions"]:
                functions.append(
                    {
                        "FunctionName": func["FunctionName"],
                        "Runtime": func["Runtime"],
                        "Handler": func["Handler"],
                        "CodeSize": func["CodeSize"],
                        "Description": func.get("Description", ""),
                        "Timeout": func["Timeout"],
                        "MemorySize": func["MemorySize"],
                        "LastModified": func["LastModified"],
                        "State": func.get("State", "Active"),
                    }
                )

            self.logger.info(f"Found {len(functions)} Lambda functions")
            return functions

        except ClientError as e:
            self.logger.error(f"Failed to list functions: {e}")
            raise

    def create_function(
        self,
        function_name: str,
        runtime: str,
        role_arn: str,
        handler: str,
        code_path: str,
        description: Optional[str] = None,
        timeout: Optional[int] = None,
        memory_size: Optional[int] = None,
        environment_vars: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a new Lambda function.

        Args:
            function_name: Name of the function
            runtime: Runtime environment (e.g., 'python3.9')
            role_arn: IAM role ARN for the function
            handler: Function handler (e.g., 'lambda_function.lambda_handler')
            code_path: Path to code zip file or directory
            description: Function description
            timeout: Function timeout in seconds
            memory_size: Memory allocation in MB
            environment_vars: Environment variables

        Returns:
            Function information
        """
        try:
            # Prepare code
            if os.path.isdir(code_path):
                # Create zip from directory
                zip_path = f"/tmp/{function_name}.zip"
                self._create_zip_from_directory(code_path, zip_path)
                code_path = zip_path

            with open(code_path, "rb") as f:
                zip_content = f.read()

            # Set defaults from config
            timeout = timeout or self.config.get("lambda.timeout", 30)
            memory_size = memory_size or self.config.get("lambda.memory_size", 128)

            params = {
                "FunctionName": function_name,
                "Runtime": runtime,
                "Role": role_arn,
                "Handler": handler,
                "Code": {"ZipFile": zip_content},
                "Timeout": timeout,
                "MemorySize": memory_size,
            }

            if description:
                params["Description"] = description

            if environment_vars:
                params["Environment"] = {"Variables": environment_vars}

            response = self.lambda_client.create_function(**params)

            self.logger.info(f"Created Lambda function: {function_name}")
            return {
                "FunctionName": response["FunctionName"],
                "FunctionArn": response["FunctionArn"],
                "Runtime": response["Runtime"],
                "Handler": response["Handler"],
                "State": response.get("State", "Active"),
            }

        except ClientError as e:
            self.logger.error(f"Failed to create function {function_name}: {e}")
            raise

    def update_function_code(self, function_name: str, code_path: str) -> bool:
        """Update Lambda function code.

        Args:
            function_name: Name of the function
            code_path: Path to new code zip file or directory

        Returns:
            True if successful
        """
        try:
            # Prepare code
            if os.path.isdir(code_path):
                zip_path = f"/tmp/{function_name}_update.zip"
                self._create_zip_from_directory(code_path, zip_path)
                code_path = zip_path

            with open(code_path, "rb") as f:
                zip_content = f.read()

            self.lambda_client.update_function_code(
                FunctionName=function_name, ZipFile=zip_content
            )

            self.logger.info(f"Updated code for function: {function_name}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to update function code: {e}")
            raise

    def invoke_function(
        self,
        function_name: str,
        payload: Optional[Dict[str, Any]] = None,
        invocation_type: str = "RequestResponse",
    ) -> Dict[str, Any]:
        """Invoke a Lambda function.

        Args:
            function_name: Name of the function
            payload: Function payload
            invocation_type: 'RequestResponse', 'Event', or 'DryRun'

        Returns:
            Invocation response
        """
        try:
            params = {"FunctionName": function_name, "InvocationType": invocation_type}

            if payload:
                params["Payload"] = json.dumps(payload)

            response = self.lambda_client.invoke(**params)

            result = {
                "StatusCode": response["StatusCode"],
                "ExecutedVersion": response.get("ExecutedVersion"),
            }

            if "Payload" in response:
                result["Payload"] = response["Payload"].read().decode("utf-8")
                if invocation_type == "RequestResponse":
                    try:
                        result["Payload"] = json.loads(result["Payload"])
                    except json.JSONDecodeError:
                        pass  # Keep as string if not valid JSON

            self.logger.info(f"Invoked function: {function_name}")
            return result

        except ClientError as e:
            self.logger.error(f"Failed to invoke function {function_name}: {e}")
            raise

    def delete_function(self, function_name: str) -> bool:
        """Delete a Lambda function.

        Args:
            function_name: Name of the function to delete

        Returns:
            True if successful
        """
        try:
            self.lambda_client.delete_function(FunctionName=function_name)
            self.logger.info(f"Deleted function: {function_name}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to delete function {function_name}: {e}")
            raise

    def get_function(self, function_name: str) -> Dict[str, Any]:
        """Get Lambda function information.

        Args:
            function_name: Name of the function

        Returns:
            Function information
        """
        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            config = response["Configuration"]

            return {
                "FunctionName": config["FunctionName"],
                "FunctionArn": config["FunctionArn"],
                "Runtime": config["Runtime"],
                "Handler": config["Handler"],
                "CodeSize": config["CodeSize"],
                "Description": config.get("Description", ""),
                "Timeout": config["Timeout"],
                "MemorySize": config["MemorySize"],
                "LastModified": config["LastModified"],
                "State": config.get("State", "Active"),
                "Environment": config.get("Environment", {}).get("Variables", {}),
                "CodeSha256": config["CodeSha256"],
            }

        except ClientError as e:
            self.logger.error(f"Failed to get function {function_name}: {e}")
            raise

    def create_event_source_mapping(
        self,
        function_name: str,
        event_source_arn: str,
        starting_position: str = "LATEST",
    ) -> Dict[str, Any]:
        """Create an event source mapping for the function.

        Args:
            function_name: Name of the function
            event_source_arn: ARN of the event source (e.g., Kinesis stream)
            starting_position: Starting position for stream ('LATEST' or 'TRIM_HORIZON')

        Returns:
            Event source mapping information
        """
        try:
            response = self.lambda_client.create_event_source_mapping(
                EventSourceArn=event_source_arn,
                FunctionName=function_name,
                StartingPosition=starting_position,
            )

            self.logger.info(f"Created event source mapping for {function_name}")
            return {
                "UUID": response["UUID"],
                "EventSourceArn": response["EventSourceArn"],
                "FunctionArn": response["FunctionArn"],
                "State": response["State"],
            }

        except ClientError as e:
            self.logger.error(f"Failed to create event source mapping: {e}")
            raise

    def add_permission(
        self,
        function_name: str,
        statement_id: str,
        action: str,
        principal: str,
        source_arn: Optional[str] = None,
    ) -> bool:
        """Add permission to Lambda function.

        Args:
            function_name: Name of the function
            statement_id: Unique statement identifier
            action: Action to allow (e.g., 'lambda:InvokeFunction')
            principal: Principal that is getting permission
            source_arn: Source ARN (optional)

        Returns:
            True if successful
        """
        try:
            params = {
                "FunctionName": function_name,
                "StatementId": statement_id,
                "Action": action,
                "Principal": principal,
            }

            if source_arn:
                params["SourceArn"] = source_arn

            self.lambda_client.add_permission(**params)
            self.logger.info(f"Added permission to function: {function_name}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to add permission: {e}")
            raise

    def _create_zip_from_directory(self, directory: str, zip_path: str):
        """Create a zip file from a directory.

        Args:
            directory: Directory to zip
            zip_path: Output zip file path
        """
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, directory)
                    zipf.write(file_path, arcname)

    def get_function_logs(
        self,
        function_name: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
    ) -> List[str]:
        """Get CloudWatch logs for a Lambda function.

        Args:
            function_name: Name of the function
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            limit: Maximum number of log entries

        Returns:
            List of log messages
        """
        try:
            # This would require CloudWatch Logs client
            # For now, return a placeholder
            self.logger.info(f"Getting logs for function: {function_name}")
            return [f"Log retrieval for {function_name} - feature to be implemented"]

        except Exception as e:
            self.logger.error(f"Failed to get function logs: {e}")
            raise
