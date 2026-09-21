import json
from typing import Dict, Any
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
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = chain.invoke({"input": prompt})
                if response.content.startswith("Error: "):
                    raise RuntimeError(f"API returned an error string instead of completion: {response.content}")
                return response.content
            except Exception as e:
                import time
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt * 5  # 5s, 10s
                    logger.warning(f"Rate limited or error on LLM text generation. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries}): {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Error calling LLM after {max_retries} attempts: {str(e)}")
                    raise

    def generate_json(self, prompt: str, system_prompt: str = "You are a helpful assistant. Always return valid JSON.", model_name: str = "llama3-8b-8192", temperature: float = 0.1) -> Dict[str, Any]:
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
                content = response.content
                if content.startswith("Error: "):
                    raise RuntimeError(f"API returned an error string instead of JSON completion: {content}")
                if content.startswith("```json"):
                    content = content[7:-3]
                elif content.startswith("```"):
                    content = content[3:-3]
                return json.loads(content.strip())
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response. Error: {str(e)}. Response content: {response.content}")
                raise  # Don't retry on bad JSON syntax here, mostly for 429 limits
            except Exception as e:
                import time
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt * 5  # 5s, 10s
                    logger.warning(f"Rate limited or error on LLM JSON generation. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries}): {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Error calling LLM for JSON after {max_retries} attempts: {str(e)}")
                    raise

llm_client = LLMClient()
