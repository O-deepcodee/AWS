#!/usr/bin/env python3
"""
Command-line interface for AWS Toolkit.
"""

import click
import json
import sys
from typing import Optional
from aws_toolkit.core.config import Config
from aws_toolkit.services import (
    EC2Manager,
    S3Manager,
    LambdaManager,
    IAMManager,
    RDSManager,
)
from aws_toolkit.utils.logger import get_logger, setup_logging


@click.group()
@click.option("--config", "-c", help="Configuration file path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, config, verbose):
    """AWS Utility Toolkit - Comprehensive AWS management tool."""
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)

    # Initialize configuration
    ctx.ensure_object(dict)
    ctx.obj["config"] = Config(config)
    ctx.obj["logger"] = get_logger(__name__, log_level)


@cli.group()
@click.pass_context
def ec2(ctx):
    """EC2 instance management commands."""
    ctx.obj["ec2"] = EC2Manager(ctx.obj["config"])


@ec2.command("list")
@click.option("--state", help="Filter by instance state")
@click.pass_context
def ec2_list(ctx, state):
    """List EC2 instances."""
    try:
        filters = {}
        if state:
            filters["instance-state-name"] = state

        instances = ctx.obj["ec2"].list_instances(filters if filters else None)

        if instances:
            click.echo(f"Found {len(instances)} instances:")
            for instance in instances:
                click.echo(f"  ID: {instance['InstanceId']}")
                click.echo(f"  Type: {instance['InstanceType']}")
                click.echo(f"  State: {instance['State']}")
                click.echo(f"  Public IP: {instance.get('PublicIpAddress', 'N/A')}")
                click.echo("  ---")
        else:
            click.echo("No instances found.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@ec2.command("create")
@click.argument("instance_type")
@click.argument("image_id")
@click.option("--key-name", help="SSH key pair name")
@click.option("--tags", help="Instance tags (JSON format)")
@click.pass_context
def ec2_create(ctx, instance_type, image_id, key_name, tags):
    """Create a new EC2 instance."""
    try:
        instance_tags = None
        if tags:
            instance_tags = json.loads(tags)

        instance = ctx.obj["ec2"].create_instance(
            instance_type=instance_type,
            image_id=image_id,
            key_name=key_name,
            tags=instance_tags,
        )

        click.echo(f"Created instance: {instance['InstanceId']}")
        click.echo(f"Type: {instance['InstanceType']}")
        click.echo(f"State: {instance['State']}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@ec2.command("terminate")
@click.argument("instance_id")
@click.confirmation_option(prompt="Are you sure you want to terminate this instance?")
@click.pass_context
def ec2_terminate(ctx, instance_id):
    """Terminate an EC2 instance."""
    try:
        ctx.obj["ec2"].terminate_instance(instance_id)
        click.echo(f"Terminated instance: {instance_id}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
@click.pass_context
def s3(ctx):
    """S3 bucket and object management commands."""
    ctx.obj["s3"] = S3Manager(ctx.obj["config"])


@s3.command("list-buckets")
@click.pass_context
def s3_list_buckets(ctx):
    """List S3 buckets."""
    try:
        buckets = ctx.obj["s3"].list_buckets()

        if buckets:
            click.echo(f"Found {len(buckets)} buckets:")
            for bucket in buckets:
                click.echo(f"  {bucket['Name']} (created: {bucket['CreationDate']})")
        else:
            click.echo("No buckets found.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@s3.command("create-bucket")
@click.argument("bucket_name")
@click.option("--region", help="AWS region")
@click.pass_context
def s3_create_bucket(ctx, bucket_name, region):
    """Create an S3 bucket."""
    try:
        ctx.obj["s3"].create_bucket(bucket_name, region)
        click.echo(f"Created bucket: {bucket_name}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@s3.command("upload")
@click.argument("file_path")
@click.argument("bucket_name")
@click.option("--key", help="S3 object key (default: filename)")
@click.pass_context
def s3_upload(ctx, file_path, bucket_name, key):
    """Upload a file to S3."""
    try:
        ctx.obj["s3"].upload_file(file_path, bucket_name, key)
        object_key = key or file_path.split("/")[-1]
        click.echo(f"Uploaded {file_path} to s3://{bucket_name}/{object_key}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@s3.command("list-objects")
@click.argument("bucket_name")
@click.option("--prefix", help="Object key prefix filter")
@click.pass_context
def s3_list_objects(ctx, bucket_name, prefix):
    """List objects in an S3 bucket."""
    try:
        objects = ctx.obj["s3"].list_objects(bucket_name, prefix)

        if objects:
            click.echo(f"Found {len(objects)} objects in {bucket_name}:")
            for obj in objects:
                click.echo(f"  {obj['Key']} ({obj['Size']} bytes)")
        else:
            click.echo(f"No objects found in {bucket_name}.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
@click.pass_context
def lambda_func(ctx):
    """Lambda function management commands."""
    ctx.obj["lambda"] = LambdaManager(ctx.obj["config"])


@lambda_func.command("list")
@click.pass_context
def lambda_list(ctx):
    """List Lambda functions."""
    try:
        functions = ctx.obj["lambda"].list_functions()

        if functions:
            click.echo(f"Found {len(functions)} Lambda functions:")
            for func in functions:
                click.echo(f"  Name: {func['FunctionName']}")
                click.echo(f"  Runtime: {func['Runtime']}")
                click.echo(f"  Handler: {func['Handler']}")
                click.echo(f"  State: {func['State']}")
                click.echo("  ---")
        else:
            click.echo("No Lambda functions found.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@lambda_func.command("invoke")
@click.argument("function_name")
@click.option("--payload", help="Function payload (JSON format)")
@click.pass_context
def lambda_invoke(ctx, function_name, payload):
    """Invoke a Lambda function."""
    try:
        function_payload = None
        if payload:
            function_payload = json.loads(payload)

        result = ctx.obj["lambda"].invoke_function(function_name, function_payload)

        click.echo(f"Function invocation result:")
        click.echo(f"Status Code: {result['StatusCode']}")
        if "Payload" in result:
            click.echo(f"Response: {result['Payload']}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
@click.pass_context
def rds(ctx):
    """RDS database management commands."""
    ctx.obj["rds"] = RDSManager(ctx.obj["config"])


@rds.command("list")
@click.pass_context
def rds_list(ctx):
    """List RDS instances."""
    try:
        instances = ctx.obj["rds"].list_instances()

        if instances:
            click.echo(f"Found {len(instances)} RDS instances:")
            for instance in instances:
                click.echo(f"  ID: {instance['DBInstanceIdentifier']}")
                click.echo(f"  Engine: {instance['Engine']}")
                click.echo(f"  Class: {instance['DBInstanceClass']}")
                click.echo(f"  Status: {instance['DBInstanceStatus']}")
                click.echo(f"  Endpoint: {instance.get('Endpoint', 'N/A')}")
                click.echo("  ---")
        else:
            click.echo("No RDS instances found.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("version")
def version():
    """Show version information."""
    from aws_toolkit import __version__

    click.echo(f"AWS Toolkit version {__version__}")


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
