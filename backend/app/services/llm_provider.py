"""
LLM Provider abstraction — supports Gemini, Anthropic (Claude), and Ollama.

Configuration (environment variables):
    LLM_PROVIDER = gemini | anthropic | ollama
    LLM_MODEL    = provider-specific model name
    LLM_API_KEY  = API key (not required for Ollama)
    LLM_BASE_URL = base URL for Ollama (e.g. http://localhost:11434)
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

import requests
from flask import current_app

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a free-text response."""

    @abstractmethod
    def generate_structured(self, prompt: str, schema: dict, system_prompt: Optional[str] = None) -> dict:
        """Generate a structured JSON response matching the given schema."""


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = self.model.generate_content(full_prompt)
        return response.text

    def generate_structured(self, prompt: str, schema: dict, system_prompt: Optional[str] = None) -> dict:
        full_prompt = (
            f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        ) + f"\n\nRespond ONLY with valid JSON matching this schema: {json.dumps(schema)}"
        response = self.model.generate_content(full_prompt)
        try:
            text = response.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            logger.warning("GeminiProvider: failed to parse structured response")
            return {}


# ---------------------------------------------------------------------------
# Anthropic (Claude)
# ---------------------------------------------------------------------------

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model_name
        self.max_tokens = 2048

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def generate_structured(self, prompt: str, schema: dict, system_prompt: Optional[str] = None) -> dict:
        json_prompt = (
            f"{prompt}\n\nRespond ONLY with a valid JSON object matching this schema "
            f"(no markdown, no explanation, just JSON):\n{json.dumps(schema, indent=2)}"
        )
        system = (system_prompt or "") + (
            "\nYou are a precise JSON responder. Return only valid JSON, nothing else."
        )
        response_text = self.generate(json_prompt, system_prompt=system.strip())
        try:
            # Strip any accidental markdown fences
            text = response_text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            logger.warning("AnthropicProvider: failed to parse structured response: %s", response_text[:200])
            return {}


# ---------------------------------------------------------------------------
# Ollama (local)
# ---------------------------------------------------------------------------

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str, model_name: str):
        self.base_url = base_url.rstrip("/")
        self.model = model_name

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        if system_prompt:
            payload["system"] = system_prompt
        res = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=60)
        res.raise_for_status()
        return res.json().get("response", "")

    def generate_structured(self, prompt: str, schema: dict, system_prompt: Optional[str] = None) -> dict:
        full_prompt = (
            f"{prompt}\n\nRespond ONLY with valid JSON matching this schema: {json.dumps(schema)}"
        )
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "format": "json",
        }
        if system_prompt:
            payload["system"] = system_prompt
        res = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=60)
        res.raise_for_status()
        try:
            return json.loads(res.json().get("response", "{}"))
        except (json.JSONDecodeError, ValueError):
            logger.warning("OllamaProvider: failed to parse structured response")
            return {}


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_llm_provider() -> LLMProvider:
    """
    Instantiate and return the configured LLM provider.

    Reads from Flask app config (populated from environment variables):
        LLM_PROVIDER: 'gemini' | 'anthropic' | 'ollama'
        LLM_MODEL:    model name for the selected provider
        LLM_API_KEY:  API key (Gemini / Anthropic)
        LLM_BASE_URL: base URL for Ollama
    """
    provider = current_app.config.get("LLM_PROVIDER", "anthropic")
    model = current_app.config.get("LLM_MODEL", "claude-sonnet-4-20250514")
    api_key = current_app.config.get("LLM_API_KEY", "")
    base_url = current_app.config.get("LLM_BASE_URL", "")

    if provider == "anthropic":
        if not api_key:
            raise ValueError("LLM_API_KEY must be set for the Anthropic provider")
        return AnthropicProvider(api_key, model)
    elif provider == "gemini":
        if not api_key:
            raise ValueError("LLM_API_KEY must be set for the Gemini provider")
        return GeminiProvider(api_key, model)
    elif provider == "ollama":
        if not base_url:
            raise ValueError("LLM_BASE_URL must be set for the Ollama provider")
        return OllamaProvider(base_url, model)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: '{provider}'. Choose from: anthropic, gemini, ollama")

