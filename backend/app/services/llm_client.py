import json
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        # We fail fast at startup if GROQ_API_KEY is missing (via pydantic-settings in config.py)
        pass

    def _get_model(self, model_name: str, temperature: float = 0.7, json_mode: bool = False):
        model = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=model_name,
            temperature=temperature,
        )
        if json_mode:
            model = model.bind(response_format={"type": "json_object"})
        return model

    def generate_text(self, prompt: str, system_prompt: str = "You are a helpful assistant.", model_name: str = "llama3-70b-8192", temperature: float = 0.7) -> str:
        model = self._get_model(model_name, temperature=temperature)
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        chain = chat_prompt | model
        try:
            response = chain.invoke({"input": prompt})
            return response.content
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}")
            raise

    def generate_json(self, prompt: str, system_prompt: str = "You are a helpful assistant. Always return valid JSON.", model_name: str = "llama3-8b-8192", temperature: float = 0.1) -> Dict[str, Any]:
        model = self._get_model(model_name, temperature=temperature, json_mode=True)
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        chain = chat_prompt | model
        try:
            response = chain.invoke({"input": prompt})
            content = response.content
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response. Error: {str(e)}. Response content: {response.content}")
            raise
        except Exception as e:
            logger.error(f"Error calling LLM for JSON: {str(e)}")
            raise

llm_client = LLMClient()
