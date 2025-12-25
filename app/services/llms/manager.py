import logging
from langchain.chat_models import init_chat_model
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class LLMManager:
    def __init__(self, temperature: float = 0.2):
        self.priority_list = settings.LLM_PRIORITY_LIST
        self.llm_temperature = temperature
        self.mode = settings.LLM_MODE
        self.static_provider = settings.LLM_STATIC_PROVIDER.lower()

        self.providers_map = {
            "openai": {
                "api_key": settings.OPENAI_API_KEY,
                "model": settings.OPENAI_MODEL,
                "langchain_name": lambda m: f"openai:{m}",
            },
            "googlegenai": {
                "api_key": settings.GOOGLEGENAI_API_KEY,
                "model": settings.GOOGLEGENAI_MODEL,
                "langchain_name": lambda m: f"google_genai:{m}",
            },
            "groq": {
                "api_key": settings.GROQ_API_KEY,
                "model": settings.GROQ_MODEL,
                "langchain_name": lambda m: f"groq:{m}",
            },
            "ollama": {
                "base_url": settings.OLLAMA_BASE_URL,
                "model": settings.OLLAMA_MODEL,
                "langchain_name": lambda m: f"ollama:{m}",
            },
        }

    def get_llm(self, **kwargs):
        """
        Get an llm instance based on llm selection mode
        """
        if self.mode == "static":
            return self._get_static_llm(**kwargs)

        return self._get_auto_llm(**kwargs)

    def _get_auto_llm(self, **kwargs):
        for provider in self.priority_list:
            provider = provider.lower()
            provider_map = self.providers_map.get(provider)

            if not provider_map:
                logger.warning(f"Provider {provider} not registered")
                continue

            model_name = provider_map.get("model")
            if not model_name:
                logger.warning(f"Model for provider {provider} is not configured")
                continue

            llm_id = provider_map["langchain_name"](model_name)

            try:
                if provider == "ollama":
                    llm = init_chat_model(
                        llm_id,
                        base_url=provider_map["base_url"],
                        **kwargs,
                    )
                else:
                    api_key = provider_map.get("api_key")
                    if not api_key:
                        logger.warning(f"API key for {provider} not set")
                        continue

                    llm = init_chat_model(
                        llm_id,
                        api_key=api_key,
                        **kwargs,
                    )
                    
                response = llm.invoke("Reply with the word OK only.")
                logger.info(f"✔ LLM {provider} active → {response.content}")

                return llm

            except Exception as e:
                logger.error(f"❌ {provider} failed → {e}")
                continue

        raise RuntimeError("No available LLM provider passed health check")

    def _get_static_llm(self, **kwargs):
        provider = self.static_provider

        provider_map = self.providers_map.get(provider)
        if not provider_map:
            raise RuntimeError(f"Static provider '{provider}' not found")

        model_name = provider_map.get("model")
        if not model_name:
            raise RuntimeError(f"Static LLM '{provider}' missing model config")

        llm_id = provider_map["langchain_name"](model_name)

        try:
            if provider == "ollama":
                return init_chat_model(
                    llm_id,
                    base_url=provider_map["base_url"],
                    **kwargs,
                )

            api_key = provider_map.get("api_key")
            if not api_key:
                raise RuntimeError(f"API key for static provider '{provider}' not set")

            return init_chat_model(
                llm_id,
                api_key=api_key,
                **kwargs,
            )

        except Exception as e:
            logger.error(f"Static provider '{provider}' init failed → {e}")
            raise

    def check_all_provider(self):
        results = {}
        for provider in self.priority_list:
            provider = provider.lower()
            provider_map = self.providers_map.get(provider)

            if not provider_map:
                results[provider] = "not registered"
                continue

            model_name = provider_map.get("model")
            if not model_name:
                results[provider] = "model not configured"
                continue

            llm_id = provider_map["langchain_name"](model_name)

            try:
                if provider == "ollama":
                    llm = init_chat_model(
                        llm_id,
                        base_url=provider_map["base_url"],
                        temperature=self.llm_temperature,
                    )
                else:
                    api_key = provider_map.get("api_key")
                    if not api_key:
                        results[provider] = "API key not set"
                        continue

                    llm = init_chat_model(
                        llm_id,
                        api_key=api_key,
                        temperature=self.llm_temperature,
                    )

                response = llm.invoke("Reply with the word OK only.")
                results[provider] = f"active → {response.content}"

            except Exception as e:
                results[provider] = f"failed → {e}"

        return results