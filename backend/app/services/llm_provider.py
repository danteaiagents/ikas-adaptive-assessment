from abc import ABC, abstractmethod
import google.generativeai as genai
import requests
from flask import current_app

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass

    @abstractmethod
    def generate_structured(self, prompt: str, schema: dict) -> dict:
        pass

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text

    def generate_structured(self, prompt: str, schema: dict) -> dict:
        # Simplistic implementation for struct
        response = self.model.generate_content(f"{prompt}\n\nRespond in JSON matching this schema: {schema}")
        import json
        try:
            return json.loads(response.text.strip('```json').strip('```').strip())
        except:
            return {}

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str, model_name: str):
        self.base_url = base_url.rstrip('/')
        self.model = model_name

    def generate(self, prompt: str) -> str:
        res = requests.post(f"{self.base_url}/api/generate", json={"model": self.model, "prompt": prompt, "stream": False})
        return res.json().get("response", "")

    def generate_structured(self, prompt: str, schema: dict) -> dict:
        # Ollama supports json format flag
        res = requests.post(f"{self.base_url}/api/generate", json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"})
        import json
        try:
            return json.loads(res.json().get("response", "{}"))
        except:
            return {}

def get_llm_provider() -> LLMProvider:
    provider = current_app.config['LLM_PROVIDER']
    model = current_app.config['LLM_MODEL']
    if provider == 'gemini':
        return GeminiProvider(current_app.config['LLM_API_KEY'], model)
    elif provider == 'ollama':
        return OllamaProvider(current_app.config['LLM_BASE_URL'], model)
    else:
        raise ValueError(f"Unknown LLM Provider: {provider}")
