# AWS Utility Toolkit

A comprehensive Python toolkit for managing AWS services including EC2, S3, Lambda, RDS, and more.

## Features

- **EC2 Management**: Create, manage, and monitor EC2 instances
- **S3 Operations**: Upload, download, and manage S3 buckets and objects
- **Lambda Functions**: Deploy and manage serverless functions
- **RDS Management**: Database instance creation and management
- **IAM Utilities**: User and role management
- **CloudWatch Integration**: Monitoring and logging
- **Security Best Practices**: Built-in security features and validations
- **CLI Interface**: Easy-to-use command-line interface
- **Comprehensive Testing**: Full test coverage with unit and integration tests

## Installation

```bash
# Clone the repository
git clone https://github.com/O-deepcodee/AWS.git
cd AWS

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Configuration

1. Copy the environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your AWS credentials:
```bash
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
```

3. Alternatively, use AWS CLI configuration:
```bash
aws configure
```

## Usage

### Command Line Interface

```bash
# List EC2 instances
aws-toolkit ec2 list

# Create S3 bucket
aws-toolkit s3 create-bucket my-bucket

# Deploy Lambda function
aws-toolkit lambda deploy my-function.zip

# Monitor resources
aws-toolkit monitor dashboard
```

### Python API

```python
from aws_toolkit import EC2Manager, S3Manager, LambdaManager

# EC2 operations
ec2 = EC2Manager()
instances = ec2.list_instances()
new_instance = ec2.create_instance('t2.micro', 'ami-12345')

# S3 operations
s3 = S3Manager()
s3.create_bucket('my-unique-bucket')
s3.upload_file('local-file.txt', 'my-unique-bucket', 'remote-file.txt')

# Lambda operations
lambda_mgr = LambdaManager()
lambda_mgr.deploy_function('my-function', 'function.zip')
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aws_toolkit

# Run specific test module
pytest tests/test_ec2.py
```

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run linting
flake8 aws_toolkit/
black aws_toolkit/
mypy aws_toolkit/

# Run tests
pytest tests/
```

## Security

- Always use IAM roles when possible
- Never commit AWS credentials to version control
- Follow AWS security best practices
- Use least privilege principle for IAM policies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions, please open an issue on GitHub.