from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="aws-utility-toolkit",
    version="1.0.0",
    author="O-deepcodee",
    author_email="OzqrK@deepcode.com.tr",
    description="Comprehensive AWS utility toolkit for managing AWS services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/O-deepcodee/AWS",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "aws-toolkit=aws_toolkit.cli:main",
        ],
    },
)