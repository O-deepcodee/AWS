#!/usr/bin/env python3
"""
Example script for S3 bucket and object management.
"""

import os
import tempfile
import time
from aws_toolkit import S3Manager, Config, get_logger


def create_and_manage_bucket():
    """Example of creating and managing an S3 bucket."""
    config = Config()
    logger = get_logger(__name__)
    s3 = S3Manager(config)
    
    # Create unique bucket name
    timestamp = int(time.time())
    bucket_name = f"aws-toolkit-demo-{timestamp}"
    
    logger.info(f"S3 Bucket Management Example")
    logger.info(f"Bucket name: {bucket_name}")
    
    try:
        # Create bucket
        logger.info("Creating bucket...")
        s3.create_bucket(bucket_name)
        logger.info(f"Created bucket: {bucket_name}")
        
        # Create a sample file
        sample_content = f"""# AWS Toolkit Demo File
        
This file was created by the AWS Toolkit demo script.
Created at: {time.strftime('%Y-%m-%d %H:%M:%S')}
Bucket: {bucket_name}

## Features Demonstrated:
- Bucket creation
- File upload
- File download  
- Object listing
- Object metadata
- Presigned URLs
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(sample_content)
            temp_file = f.name
        
        try:
            # Upload file
            object_key = "demo/readme.md"
            logger.info(f"Uploading file to {object_key}...")
            
            extra_args = {
                'ContentType': 'text/markdown',
                'Metadata': {
                    'author': 'aws-toolkit',
                    'version': '1.0'
                }
            }
            
            s3.upload_file(temp_file, bucket_name, object_key, extra_args)
            logger.info("File uploaded successfully")
            
            # List objects
            logger.info("Listing objects in bucket...")
            objects = s3.list_objects(bucket_name)
            
            for obj in objects:
                logger.info(f"  Object: {obj['Key']}")
                logger.info(f"    Size: {obj['Size']} bytes")
                logger.info(f"    Last Modified: {obj['LastModified']}")
            
            # Get object metadata
            logger.info("Getting object metadata...")
            metadata = s3.get_object_metadata(bucket_name, object_key)
            logger.info(f"  Content Type: {metadata['ContentType']}")
            logger.info(f"  Custom Metadata: {metadata['Metadata']}")
            
            # Generate presigned URL
            logger.info("Generating presigned URL...")
            url = s3.generate_presigned_url(bucket_name, object_key, expiration=3600)
            logger.info(f"  Presigned URL: {url}")
            
            # Download file
            download_path = tempfile.mktemp(suffix='_downloaded.md')
            logger.info(f"Downloading file to {download_path}...")
            s3.download_file(bucket_name, object_key, download_path)
            
            # Verify download
            with open(download_path, 'r') as f:
                downloaded_content = f.read()
            
            if sample_content == downloaded_content:
                logger.info("Download verification successful!")
            else:
                logger.warning("Download verification failed!")
            
            # Copy object
            copy_key = "demo/readme_copy.md"
            logger.info(f"Copying object to {copy_key}...")
            s3.copy_object(bucket_name, object_key, bucket_name, copy_key)
            
            # List objects again
            objects = s3.list_objects(bucket_name)
            logger.info(f"Bucket now contains {len(objects)} objects")
            
            # Clean up downloaded file
            os.unlink(download_path)
            
            logger.info("Example completed successfully!")
            logger.info(f"Bucket '{bucket_name}' and its contents are still available.")
            logger.info("You can clean it up with: aws-toolkit s3 delete-bucket --force")
            
            return bucket_name
            
        finally:
            # Clean up temp file
            os.unlink(temp_file)
            
    except Exception as e:
        logger.error(f"Example failed: {e}")
        return None


def list_and_explore_buckets():
    """Example of listing and exploring existing buckets."""
    config = Config()
    logger = get_logger(__name__)
    s3 = S3Manager(config)
    
    logger.info("=== Listing All Buckets ===")
    buckets = s3.list_buckets()
    
    if not buckets:
        logger.info("No buckets found")
        return
    
    for bucket in buckets:
        logger.info(f"Bucket: {bucket['Name']}")
        logger.info(f"  Created: {bucket['CreationDate']}")
        
        # List first few objects in each bucket
        try:
            objects = s3.list_objects(bucket['Name'], max_keys=5)
            logger.info(f"  Objects: {len(objects)} (showing first 5)")
            
            for obj in objects[:5]:
                logger.info(f"    - {obj['Key']} ({obj['Size']} bytes)")
                
        except Exception as e:
            logger.warning(f"  Could not list objects: {e}")
        
        logger.info("  ---")


def demonstrate_advanced_features():
    """Demonstrate advanced S3 features."""
    config = Config()
    logger = get_logger(__name__)
    s3 = S3Manager(config)
    
    # Create a demo bucket for advanced features
    timestamp = int(time.time())
    bucket_name = f"aws-toolkit-advanced-{timestamp}"
    
    try:
        logger.info("=== Advanced S3 Features Demo ===")
        
        # Create bucket
        s3.create_bucket(bucket_name)
        logger.info(f"Created demo bucket: {bucket_name}")
        
        # Upload multiple files with different prefixes
        files_to_create = [
            ("documents/report.txt", "This is a report document."),
            ("documents/presentation.txt", "This is a presentation."),
            ("images/photo1.txt", "This represents an image file."),
            ("images/photo2.txt", "This represents another image."),
            ("backup/data.txt", "This is backup data.")
        ]
        
        for key, content in files_to_create:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            try:
                s3.upload_file(temp_file, bucket_name, key)
                logger.info(f"Uploaded: {key}")
            finally:
                os.unlink(temp_file)
        
        # Demonstrate prefix filtering
        logger.info("\n=== Prefix Filtering ===")
        
        prefixes = ["documents/", "images/", "backup/"]
        for prefix in prefixes:
            objects = s3.list_objects(bucket_name, prefix=prefix)
            logger.info(f"Objects with prefix '{prefix}': {len(objects)}")
            for obj in objects:
                logger.info(f"  - {obj['Key']}")
        
        # Set a simple bucket policy (public read)
        logger.info("\n=== Setting Bucket Policy ===")
        
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }
        
        try:
            s3.set_bucket_policy(bucket_name, policy)
            logger.info("Bucket policy set successfully")
        except Exception as e:
            logger.warning(f"Could not set bucket policy: {e}")
        
        # Clean up - delete all objects
        logger.info("\n=== Cleanup ===")
        deleted_count = s3.delete_all_objects(bucket_name)
        logger.info(f"Deleted {deleted_count} objects")
        
        # Delete bucket
        s3.delete_bucket(bucket_name)
        logger.info(f"Deleted bucket: {bucket_name}")
        
    except Exception as e:
        logger.error(f"Advanced features demo failed: {e}")


def main():
    """Main function."""
    logger = get_logger(__name__)
    
    # First, list existing buckets
    list_and_explore_buckets()
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Create and manage a demo bucket")
    print("2. Demonstrate advanced features")
    print("3. Just list buckets (already done)")
    print("Enter choice (1-3) or press Enter to exit: ", end="")
    
    choice = input().strip()
    
    if choice == "1":
        bucket_name = create_and_manage_bucket()
        if bucket_name:
            print(f"\nDemo bucket created: {bucket_name}")
            print("Remember to clean it up when done!")
    elif choice == "2":
        demonstrate_advanced_features()
    else:
        logger.info("Exiting")


if __name__ == "__main__":
    main()