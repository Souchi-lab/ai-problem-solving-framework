"""
AnthropicProvider — Anthropic (Claude) API の実装

Builder role に推奨。高品質なアウトプットが求められる工程に集中投入する。

接続方法:
    ANTHROPIC_API_KEY を .env に設定してから使用する。
    pip install anthropic>=0.20
"""

from __future__ import annotations

from ..core.providers.base import (
    AuthenticationError,
    BaseProvider,
    GenerateRequest,
    GenerateResponse,
    ProviderError,
    RateLimitError,
)


class AnthropicProvider(BaseProvider):
    """
    Anthropic Claude API provider。

    使用例:
        provider = AnthropicProvider(model="claude-sonnet-4-6", api_key="sk-ant-...")
        response = provider.generate(GenerateRequest(prompt="...", system="..."))
    """

    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str = ""):
        super().__init__(model=model, api_key=api_key)
        self._client = None  # 遅延初期化

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def _get_client(self):
        """Anthropic クライアントを遅延初期化する"""
        if self._client is None:
            try:
                import anthropic  # type: ignore
            except ImportError:
                raise ProviderError(
                    "anthropic package is not installed. Run: pip install anthropic>=0.20"
                )

            if not self._api_key:
                raise AuthenticationError(
                    "ANTHROPIC_API_KEY is not set. Add it to .env file."
                )

            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        """
        Anthropic Messages API を呼び出してテキストを生成する。

        TODO: streaming 対応（v0.2）
        TODO: retry / backoff 実装（v0.2）
        """
        client = self._get_client()
        model = request.model or self._model

        try:
            kwargs: dict = {
                "model": model,
                "max_tokens": request.max_tokens,
                "messages": [{"role": "user", "content": request.prompt}],
            }
            if request.system:
                kwargs["system"] = request.system

            message = client.messages.create(**kwargs)
            content = message.content[0].text

            return GenerateResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                raw={"id": message.id, "usage": message.usage.__dict__ if message.usage else None},
            )

        except Exception as e:
            # anthropic ライブラリの例外を ProviderError に変換する
            # TODO: v0.2 で anthropic 固有例外クラスに対応した分岐を追加する
            error_str = str(e).lower()
            if "authentication" in error_str or "api_key" in error_str:
                raise AuthenticationError(f"Anthropic authentication failed: {e}") from e
            if "rate_limit" in error_str or "rate limit" in error_str:
                raise RateLimitError(f"Anthropic rate limit exceeded: {e}") from e
            raise ProviderError(f"Anthropic API error: {e}") from e
