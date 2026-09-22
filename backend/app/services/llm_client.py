import json
import logging
import re
import time
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_groq import ChatGroq
from pydantic import SecretStr

from app.core.config import settings
from app.services.groq_key_pool import AllKeysCoolingDown, GroqKeyPool

logger = logging.getLogger(__name__)

MAX_RETRIES = 4


class LLMClient:
    def __init__(self):
        # Pool = GROQ_API_KEY + GROQ_API_KEYS (comma-separated). One key works fine;
        # more keys multiply the provider rate-limit budget and enable instant
        # failover instead of sleeping through 429 cooldowns.
        self._pool = GroqKeyPool(settings.groq_api_key_list)

    @property
    def pool_status(self) -> dict:
        return self._pool.status()

    def _get_model(self, api_key: str, model_name: str, temperature: float = 0.7, json_mode: bool = False) -> Runnable:
        model = ChatGroq(
            api_key=SecretStr(api_key),
            model=model_name,
            temperature=temperature,
            max_retries=0,  # let the key pool own failover: SDK-internal retries would
            # keep hammering the same rate-limited key before we can swap to another
        )
        if json_mode:
            return model.bind(response_format={"type": "json_object"})
        return model

    def _cooldown_from_error(self, error: Exception) -> float:
        """Extract the wait time the provider suggests in a 429 message, if any."""
        hint = re.search(r"try again in ([\d.]+)s", str(error))
        if hint:
            return min(float(hint.group(1)) + 1.0, 60.0)
        return 15.0

    def _invoke_with_pool(
        self,
        prompt: str,
        system_prompt: str,
        model_name: str,
        temperature: float,
        json_mode: bool,
    ) -> Any:
        """Run one chat completion, failing over across pooled API keys.

        Per attempt: acquire the next healthy key and try it. On a rate limit,
        that key goes into cooldown and the NEXT attempt uses another key
        immediately. Only when all keys are cooling do we sleep until the
        earliest one frees up.
        """
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
        ])

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                api_key = self._pool.acquire()
            except AllKeysCoolingDown as e:
                wait = self._cooldown_from_error(e) if last_error else 5.0
                logger.warning(f"All Groq keys cooling down; waiting {wait:.0f}s ({e})")
                time.sleep(wait)
                last_error = e
                continue

            try:
                chain = chat_prompt | self._get_model(api_key, model_name, temperature, json_mode)
                response = chain.invoke({"input": prompt})
                self._pool.report_success(api_key)
                content = response.content
                if content.startswith("Error: "):
                    raise RuntimeError(f"API returned an error string instead of completion: {content}")
                return content
            except Exception as e:  # noqa: BLE001 - provider/network errors, retried below
                last_error = e
                is_rate_limit = "429" in str(e) or "rate_limit" in str(e).lower()
                if is_rate_limit:
                    cooldown = self._cooldown_from_error(e)
                    self._pool.report_rate_limited(api_key, cooldown)
                    logger.warning(
                        f"Groq key ...{api_key[-6:]} rate-limited; cooling down {cooldown:.0f}s "
                        f"(pool: {self._pool.status()})"
                    )
                    continue  # next attempt picks a different healthy key, if any
                # Non-rate-limit errors: brief linear backoff, then retry
                logger.warning(f"LLM call error on attempt {attempt + 1}/{MAX_RETRIES}: {str(e)[:150]}")
                time.sleep(2 * (attempt + 1))

        raise RuntimeError(f"LLM call failed after {MAX_RETRIES} attempts: {last_error}")

    def generate_text(self, prompt: str, system_prompt: str = "You are a helpful assistant.", model_name: str = "llama3-70b-8192", temperature: float = 0.7) -> str:
        content = self._invoke_with_pool(prompt, system_prompt, model_name, temperature, json_mode=False)
        return content

    def generate_json(self, prompt: str, system_prompt: str = "You are a helpful assistant. Always return valid JSON.", model_name: str = "llama3-8b-8192", temperature: float = 0.1) -> dict[str, Any]:
        content = self._invoke_with_pool(prompt, system_prompt, model_name, temperature, json_mode=True)
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        return json.loads(content.strip())


llm_client = LLMClient()
