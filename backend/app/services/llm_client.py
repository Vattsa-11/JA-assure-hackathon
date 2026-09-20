import json
import logging
import time
from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import SecretStr

from app.core.config import settings

logger = logging.getLogger(__name__)


def _content_str(message: AIMessage) -> str:
    """Extract the text content of an AIMessage as a plain str."""
    content = message.content
    if isinstance(content, str):
        return content
    # Non-string content (list of text/tool parts) — join the text parts.
    parts: list[str] = []
    for part in content:
        if isinstance(part, str):
            parts.append(part)
        elif isinstance(part, dict) and isinstance(part.get("text"), str):
            parts.append(part["text"])
    return "".join(parts)


class LLMClient:
    def __init__(self):
        # We fail fast at startup if GROQ_API_KEY is missing (via pydantic-settings in config.py)
        pass

    def _get_model(self, model_name: str, temperature: float = 0.7, json_mode: bool = False) -> ChatGroq:
        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        model: ChatGroq = ChatGroq(
            api_key=SecretStr(api_key),
            model=model_name,
            temperature=temperature,
        )
        if json_mode:
            model = model.bind(response_format={"type": "json_object"})  # type: ignore[assignment]
        return model

    def generate_text(self, prompt: str, system_prompt: str = "You are a helpful assistant.", model_name: str = "llama3-70b-8192", temperature: float = 0.7) -> str:
        model = self._get_model(model_name, temperature=temperature)
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        chain = chat_prompt | model

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = chain.invoke({"input": prompt})
                content = _content_str(response)
                if content.startswith("Error: "):
                    raise RuntimeError(f"API returned an error string instead of completion: {content}")
                return content
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt * 5  # 5s, 10s
                    logger.warning(f"Rate limited or error on LLM text generation. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries}): {e!s}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Error calling LLM after {max_retries} attempts: {e!s}")
                    raise
        raise RuntimeError("LLM text generation failed after all retries")

    def generate_json(self, prompt: str, system_prompt: str = "You are a helpful assistant. Always return valid JSON.", model_name: str = "llama3-8b-8192", temperature: float = 0.1) -> dict[str, Any]:
        model = self._get_model(model_name, temperature=temperature, json_mode=True)
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        chain = chat_prompt | model

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = chain.invoke({"input": prompt})
                content = _content_str(response)
                if content.startswith("Error: "):
                    raise RuntimeError(f"API returned an error string instead of JSON completion: {content}")
                if content.startswith("```json"):
                    content = content[7:-3]
                elif content.startswith("```"):
                    content = content[3:-3]
                return json.loads(content.strip())
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response. Error: {e!s}. Response content: {content}")
                raise  # Don't retry on bad JSON syntax here, mostly for 429 limits
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt * 5  # 5s, 10s
                    logger.warning(f"Rate limited or error on LLM JSON generation. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries}): {e!s}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Error calling LLM for JSON after {max_retries} attempts: {e!s}")
                    raise
        raise RuntimeError("LLM JSON generation failed after all retries")


llm_client = LLMClient()
