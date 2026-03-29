"""
OpenAIProvider — OpenAI (GPT) API の実装

Planner / Critic role に推奨。
Critic は Builder（Anthropic）と別系統モデルを使うことで独立した視点を確保する。

接続方法:
    OPENAI_API_KEY を .env に設定してから使用する。
    pip install openai>=1.0
"""

from __future__ import annotations

from ...core.providers.base import (
    AuthenticationError,
    BaseProvider,
    GenerateRequest,
    GenerateResponse,
    ProviderError,
    RateLimitError,
)


class OpenAIProvider(BaseProvider):
    """
    OpenAI API provider。

    使用例:
        provider = OpenAIProvider(model="gpt-4o", api_key="sk-...")
        response = provider.generate(GenerateRequest(prompt="...", system="..."))
    """

    def __init__(self, model: str = "gpt-4o", api_key: str = ""):
        super().__init__(model=model, api_key=api_key)
        self._client = None

    @property
    def provider_name(self) -> str:
        return "openai"

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI  # type: ignore
            except ImportError:
                raise ProviderError(
                    "openai package is not installed. Run: pip install openai>=1.0"
                )

            if not self._api_key:
                raise AuthenticationError(
                    "OPENAI_API_KEY is not set. Add it to .env file."
                )

            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        """
        OpenAI Chat Completions API を呼び出してテキストを生成する。

        TODO: streaming 対応（v0.2）
        TODO: function calling 対応（v0.2）
        """
        client = self._get_client()
        model = request.model or self._model

        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})

        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
            content = completion.choices[0].message.content or ""

            return GenerateResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                raw={"id": completion.id, "usage": completion.usage.__dict__ if completion.usage else None},
            )

        except Exception as e:
            error_str = str(e).lower()
            if "authentication" in error_str or "api_key" in error_str:
                raise AuthenticationError(f"OpenAI authentication failed: {e}") from e
            if "rate_limit" in error_str or "rate limit" in error_str:
                raise RateLimitError(f"OpenAI rate limit exceeded: {e}") from e
            raise ProviderError(f"OpenAI API error: {e}") from e
