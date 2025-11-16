from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="aws-architecture-diagrams",
    version="1.0.0",
    author="Kirill Polishchuk",
    author_email="kirponil@gmail.com",
    description="Automatically generate AWS architecture documentation using AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/aws-architecture-diagrams-with-crewai",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Documentation",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "crewai>=0.1.0",
        "crewai-tools>=0.1.0",
        "boto3>=1.28.0",
        "PyYAML>=6.0",
        "python-dotenv>=1.0.0",
        "langchain-aws>=0.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aws-diagram-generator=aws_diagram_generator.cli:main",
            "aws-diagrams=aws_diagram_generator.cli:main",
        ],
    },
    package_data={
        "aws_diagram_generator": [
            "config.yaml.example",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="aws architecture diagrams documentation crewai ai bedrock claude plantuml",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/aws-architecture-diagrams-with-crewai/issues",
        "Source": "https://github.com/yourusername/aws-architecture-diagrams-with-crewai",
    },
)
