"""
GeminiProvider — Google Gemini API の実装

JuniorBuilder role に推奨。速度・コスト効率重視の工程に使用する。
Flash モデルは候補出し・下書き生成に適している。

接続方法:
    GEMINI_API_KEY を .env に設定してから使用する。
    pip install google-generativeai>=0.8
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


class GeminiProvider(BaseProvider):
    """
    Google Gemini API provider。

    使用例:
        provider = GeminiProvider(model="gemini-2.0-flash", api_key="AIza...")
        response = provider.generate(GenerateRequest(prompt="...", system="..."))
    """

    def __init__(self, model: str = "gemini-2.0-flash", api_key: str = ""):
        super().__init__(model=model, api_key=api_key)
        self._client = None

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _get_client(self):
        if self._client is None:
            try:
                import google.generativeai as genai  # type: ignore
            except ImportError:
                raise ProviderError(
                    "google-generativeai package is not installed. "
                    "Run: pip install google-generativeai>=0.8"
                )

            if not self._api_key:
                raise AuthenticationError(
                    "GEMINI_API_KEY is not set. Add it to .env file."
                )

            genai.configure(api_key=self._api_key)
            self._client = genai
        return self._client

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        """
        Gemini GenerativeModel API を呼び出してテキストを生成する。

        TODO: system instruction の正式サポート確認（モデルバージョン依存）
        TODO: safety settings の設定化（v0.2）
        """
        genai = self._get_client()
        model_name = request.model or self._model

        try:
            # system instruction はモデルによってサポートが異なる
            # TODO: v0.2 で system_instruction 対応モデルを自動判定する
            combined_prompt = request.prompt
            if request.system:
                combined_prompt = f"{request.system}\n\n---\n\n{request.prompt}"

            model = genai.GenerativeModel(model_name)
            response = model.generate_content(combined_prompt)
            content = response.text

            return GenerateResponse(
                content=content,
                model=model_name,
                provider=self.provider_name,
                raw=None,  # TODO: v0.2 で usage stats を取得する
            )

        except Exception as e:
            error_str = str(e).lower()
            if "api_key" in error_str or "authentication" in error_str:
                raise AuthenticationError(f"Gemini authentication failed: {e}") from e
            if "quota" in error_str or "rate" in error_str:
                raise RateLimitError(f"Gemini rate limit exceeded: {e}") from e
            raise ProviderError(f"Gemini API error: {e}") from e
