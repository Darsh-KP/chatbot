

from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel

from config import Settings, settings


def build_llm(s: Settings) -> BaseChatModel:
    if s.llm_provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=s.llm_model,
            base_url=s.ollama_base_url,
            temperature=s.llm_temperature,
            num_predict=s.llm_max_tokens,
            num_ctx=s.llm_num_ctx,
            client_kwargs={"timeout": s.llm_timeout_seconds},
        )

    if s.llm_provider == "fake":
        from langchain_core.language_models.fake_chat_models import FakeListChatModel

        return FakeListChatModel(
            responses=["(fake LLM) Hello! Set LLM_PROVIDER=ollama in .env to talk to a real model."]
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {s.llm_provider}")


@lru_cache
def get_llm() -> BaseChatModel:
    """Build the model once and reuse it for every request."""
    return build_llm(settings)