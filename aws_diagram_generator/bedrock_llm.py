"""Custom Bedrock LLM wrapper for CrewAI that supports inference profiles.

This wrapper is necessary because:
1. CrewAI uses LiteLLM which doesn't support AWS Bedrock inference profiles yet
2. Inference profiles are required for newer models (Claude 4.x, Nova Premier, etc.)
3. We need to implement CrewAI's BaseLLM interface while using ChatBedrock underneath

Alternative approaches that DON'T work:
- langchain.llms.Bedrock: Deprecated, completion-only, not BaseLLM compatible
- Direct boto3 client: Too low-level, doesn't handle message formatting
- LiteLLM with inference profiles: Not supported yet
"""

import os
import boto3
from typing import Any, Optional, List, Dict
from botocore.config import Config
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from crewai.llms.base_llm import BaseLLM

# Disable telemetry
os.environ['OTEL_SDK_DISABLED'] = 'true'


class BedrockLLM(BaseLLM):
    """
    Custom LLM wrapper for AWS Bedrock that works with CrewAI.
    Supports inference profiles for Claude Sonnet 4.5 and other newer models.
    """

    def __init__(
        self,
        model_id: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        region_name: str = "us-east-1",
        **kwargs
    ):
        """
        Initialize the Bedrock LLM wrapper.

        Args:
            model_id: Bedrock model ID or inference profile ID
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            region_name: AWS region
            **kwargs: Additional arguments passed to ChatBedrock
        """
        # Store attributes before calling super().__init__
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.region_name = region_name

        # Initialize BaseLLM with the model parameter
        super().__init__(model=model_id)

        # Initialize the underlying ChatBedrock client with extended timeout
        # Create boto3 client with extended timeout
        bedrock_config = Config(
            read_timeout=900,  # 15 minutes
            connect_timeout=60,  # 1 minute
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )

        bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=region_name,
            config=bedrock_config
        )

        self._client = ChatBedrock(
            client=bedrock_client,
            model_id=model_id,
            model_kwargs={
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            **kwargs
        )

    def call(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """
        Call the LLM with messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional arguments

        Returns:
            Generated text response
        """
        
        # Convert CrewAI message format to LangChain format
        lc_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:  # user or any other role
                lc_messages.append(HumanMessage(content=content))

        # Call the underlying ChatBedrock
        response = self._client.invoke(lc_messages)

        return response.content

    def supports_streaming(self) -> bool:
        """Check if streaming is supported."""
        return True

    def stream(self, messages: List[Dict[str, Any]], **kwargs):
        """
        Stream responses from the LLM.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional arguments

        Yields:
            Chunks of generated text
        """

        # Convert messages
        lc_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:
                lc_messages.append(HumanMessage(content=content))

        # Stream from ChatBedrock
        for chunk in self._client.stream(lc_messages):
            if hasattr(chunk, 'content'):
                yield chunk.content

    @property
    def model(self) -> str:
        """Return the model ID."""
        return self.model_id

    @model.setter
    def model(self, value: str):
        """Set the model ID."""
        self.model_id = value

    def __repr__(self) -> str:
        return f"BedrockLLM(model_id={self.model_id})"
