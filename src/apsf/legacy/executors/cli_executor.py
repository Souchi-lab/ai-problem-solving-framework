"""
CLIExecutor — ローカル CLI ツールを subprocess で実行する executor

対象ツール例:
- claude (Claude Code CLI)
- gemini (Gemini CLI)
- その他ローカルにインストール済みの AI CLI

v0.1 では対話型 CLI の完全自動化まではしない。
dry-run で「何を実行すべきか」を表示する機能を優先する。

API キー課金なしに、インストール済み CLI ツールを活用できる。
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from ...core.domain.models import ExecutionType
from ...core.executors.base import BaseExecutor, ExecuteRequest, ExecuteResponse, ExecutorError


class CLIExecutor(BaseExecutor):
    """
    CLI ツールを subprocess で実行する executor。

    使用例:
        executor = CLIExecutor(command="claude")
        response = executor.execute(ExecuteRequest(prompt="...", dry_run=True))

    dry_run=True の場合は実行内容を表示するだけで実際には呼び出さない。
    """

    def __init__(
        self,
        command: str,
        working_dir: Optional[Path] = None,
        timeout: int = 300,
    ):
        """
        Args:
            command: 実行する CLI コマンド名 (e.g. "claude", "gemini")
            working_dir: デフォルトの作業ディレクトリ（workspace に対応）
            timeout: タイムアウト秒数（デフォルト: 5分）
        """
        self._command = command
        self._working_dir = working_dir
        self._timeout = timeout

    @property
    def execution_type(self) -> ExecutionType:
        return ExecutionType.CLI

    @property
    def command(self) -> str:
        return self._command

    def execute(self, request: ExecuteRequest) -> ExecuteResponse:
        """
        CLI ツールにプロンプトを渡して実行する。

        dry_run=True の場合は実行コマンドのプレビューを返す。

        TODO(v0.2): 対話型 CLI の stdin 制御を実装する
        TODO(v0.2): stdout/stderr のストリーミング出力対応
        """
        working_dir = request.working_dir or self._working_dir

        if request.dry_run:
            return self._dry_run_response(request, working_dir)

        # 実際の CLI 呼び出し
        # v0.1 では prompt をファイルに書き出して CLI に渡す方式を想定
        # 完全な対話型自動化は v0.2 以降
        cmd = self._build_command(request)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=working_dir,
                timeout=self._timeout,
            )
            success = result.returncode == 0
            output = result.stdout if success else result.stderr

            return ExecuteResponse(
                content=output,
                execution_type=self.execution_type,
                success=success,
                dry_run=False,
                raw=result.stderr if success else None,
            )

        except subprocess.TimeoutExpired:
            raise ExecutorError(
                f"CLI command timed out after {self._timeout}s: {self._command}"
            )
        except FileNotFoundError:
            raise ExecutorError(
                f"CLI command not found: '{self._command}'\n"
                f"Please install it or check your PATH."
            )

    def _build_command(self, request: ExecuteRequest) -> list[str]:
        """
        実行コマンドリストを構築する。

        TODO(v0.2): ツール別のコマンド構築ロジックを分離する
        TODO(v0.2): プロンプトをファイル経由で渡す方式を実装する
        """
        # シンプルな実装: <command> <prompt>
        # 各 CLI ツールの引数形式に合わせて拡張が必要
        return [self._command, "--print", request.prompt]

    def _dry_run_response(
        self,
        request: ExecuteRequest,
        working_dir: Optional[Path],
    ) -> ExecuteResponse:
        """dry-run 時のレスポンスを生成する"""
        prompt_preview = request.prompt[:400] + ("..." if len(request.prompt) > 400 else "")
        working_dir_str = str(working_dir) if working_dir else "(current directory)"

        lines = [
            "=== CLI Executor -- Dry Run Preview ===",
            "",
            f"  Command     : {self._command}",
            f"  Working dir : {working_dir_str}",
            "",
            ">> Command to run manually:",
            f"  cd {working_dir_str}",
            f"  {self._command} \"<prompt>\"",
            "",
        ]

        if request.input_files:
            lines.append(">> Input files to include as context:")
            for f in request.input_files:
                lines.append(f"  - {f}")
            lines.append("")

        if request.system:
            system_preview = request.system[:200] + ("..." if len(request.system) > 200 else "")
            lines.extend([
                ">> System prompt (first 200 chars):",
                f"  {system_preview}",
                "",
            ])

        lines.extend([
            ">> Prompt to be sent (first 400 chars):",
            "  +-------------------------------------",
        ])
        for ln in prompt_preview.splitlines():
            lines.append(f"  | {ln}")
        lines.append("  +-------------------------------------")

        return ExecuteResponse(
            content="\n".join(lines),
            execution_type=self.execution_type,
            success=True,
            dry_run=True,
        )
