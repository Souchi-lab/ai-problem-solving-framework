"""
APIExecutor — 将来の API 直接呼び出し executor（v0.2+ 用 placeholder）

v0.1 では実装不要。
ただし将来 API executor を追加するための責務分離と拡張ポイントを示す。

実装時の方針（v0.2+）:
- src/apsf/providers/ 配下の各 provider（OpenAI / Anthropic / Gemini）を呼び出す
- ExecuteRequest を provider 固有のリクエスト形式に変換する
- ExecuteResponse に統一された形式で返す
- agent 側のコードは変えない（executor を差し替えるだけ）
"""

from __future__ import annotations

from ..core.domain.models import ExecutionType
from ..core.executors.base import BaseExecutor, ExecuteRequest, ExecuteResponse, ExecutorError


class APIExecutor(BaseExecutor):
    """
    API 直接呼び出し executor の placeholder。

    v0.1 では NotImplementedError を送出する。
    v0.2 以降で実装する際は、このクラスを拡張するか
    AnthropicAPIExecutor / OpenAIAPIExecutor として分離する。

    実装例（v0.2+）:
        class AnthropicAPIExecutor(APIExecutor):
            def __init__(self, model: str, api_key: str):
                from ..legacy.providers.anthropic_provider import AnthropicProvider
                self._provider = AnthropicProvider(model=model, api_key=api_key)

            def execute(self, request: ExecuteRequest) -> ExecuteResponse:
                from ..core.providers.base import GenerateRequest
                response = self._provider.generate(GenerateRequest(
                    prompt=request.prompt,
                    system=request.system,
                ))
                return ExecuteResponse(
                    content=response.content,
                    execution_type=self.execution_type,
                    success=True,
                )
    """

    def __init__(self, provider_type: str = "", model: str = ""):
        """
        Args:
            provider_type: "openai" / "anthropic" / "gemini"（将来使用）
            model: 使用するモデル名（将来使用）
        """
        # TODO(v0.2): provider_type と model を使って provider を初期化する
        self._provider_type = provider_type
        self._model = model

    @property
    def execution_type(self) -> ExecutionType:
        return ExecutionType.FUTURE_API

    def execute(self, request: ExecuteRequest) -> ExecuteResponse:
        """
        v0.1 では未実装。dry-run の場合はプレビューを返す。

        TODO(v0.2): provider を使った実際の API 呼び出しを実装する
        """
        if request.dry_run:
            return ExecuteResponse(
                content=(
                    f"[DRY RUN] API Executor (future): provider={self._provider_type}, "
                    f"model={self._model}\n"
                    f"Prompt preview: {request.prompt[:200]}..."
                ),
                execution_type=self.execution_type,
                success=True,
                dry_run=True,
            )

        raise ExecutorError(
            "APIExecutor is not implemented in v0.1.\n"
            "Use CLIExecutor or HumanExecutor instead.\n"
            "For future-api support, install API extras: pip install 'apsf[api]'"
        )
