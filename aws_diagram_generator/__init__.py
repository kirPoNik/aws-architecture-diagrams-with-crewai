"""
AWS Architecture Diagrams Generator

Automatically generate comprehensive AWS architecture documentation including
PlantUML diagrams, technical runbooks, executive summaries, and developer guides
using AI agents powered by CrewAI and AWS Bedrock Claude 3.5 Sonnet.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from aws_diagram_generator.core import (
    process_target,
    process_targets_parallel,
    initialize_llm,
)

__all__ = [
    "process_target",
    "process_targets_parallel",
    "initialize_llm",
]
