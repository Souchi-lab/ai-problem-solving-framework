"""
Settings — 環境変数の読み込みとプロジェクトパスの設定

v0.1 は CLI / Human 実行が主体のため、API キーは optional。
パスはプロジェクトルートからの相対パスをデフォルトとして使用する。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# プロジェクトルート: src/apsf/config/settings.py から 4 階層上
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


@dataclass
class Settings:
    # Framework paths
    framework_root: Path = field(
        default_factory=lambda: Path(os.getenv("APSF_ROOT", str(_PROJECT_ROOT)))
    )

    # Optional: API keys (only needed for future-api executor)
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))

    # Optional: default model names
    default_openai_model: str = field(
        default_factory=lambda: os.getenv("DEFAULT_OPENAI_MODEL", "gpt-4o")
    )
    default_anthropic_model: str = field(
        default_factory=lambda: os.getenv("DEFAULT_ANTHROPIC_MODEL", "claude-sonnet-4-6")
    )
    default_gemini_model: str = field(
        default_factory=lambda: os.getenv("DEFAULT_GEMINI_MODEL", "gemini-2.0-flash")
    )

    @property
    def runs_dir(self) -> Path:
        return self.framework_root / os.getenv("DEFAULT_RUNS_DIR", "runs")

    @property
    def workspaces_dir(self) -> Path:
        return self.framework_root / os.getenv("DEFAULT_WORKSPACES_DIR", "workspaces")

    @property
    def template_dir(self) -> Path:
        return self.framework_root / os.getenv("DEFAULT_TEMPLATE_DIR", "runs/_template")

    @property
    def framework_dir(self) -> Path:
        return self.framework_root / "framework"

    def has_api_key(self, provider: str) -> bool:
        """指定プロバイダーの API キーが設定されているかを確認する"""
        return {
            "openai": bool(self.openai_api_key),
            "anthropic": bool(self.anthropic_api_key),
            "gemini": bool(self.gemini_api_key),
        }.get(provider, False)

    def configured_api_providers(self) -> list[str]:
        """API キーが設定されているプロバイダーの一覧を返す"""
        return [p for p in ["openai", "anthropic", "gemini"] if self.has_api_key(p)]


_settings_instance: Settings | None = None


def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
