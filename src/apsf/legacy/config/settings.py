"""
Settings module for APSF.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent


@dataclass
class Settings:
    framework_root: Path = field(
        default_factory=lambda: Path(os.getenv("APSF_ROOT", str(_PROJECT_ROOT)))
    )

    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))

    default_openai_model: str = field(
        default_factory=lambda: os.getenv("DEFAULT_OPENAI_MODEL", "gpt-4o")
    )
    default_anthropic_model: str = field(
        default_factory=lambda: os.getenv("DEFAULT_ANTHROPIC_MODEL", "claude-sonnet-4-6")
    )
    default_gemini_model: str = field(
        default_factory=lambda: os.getenv("DEFAULT_GEMINI_MODEL", "gemini-2.0-flash")
    )
    disabled_api_providers_raw: str = field(
        default_factory=lambda: os.getenv("APSF_DISABLED_API_PROVIDERS", "gemini")
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

    @property
    def disabled_api_providers(self) -> set[str]:
        return {
            provider.strip().lower()
            for provider in self.disabled_api_providers_raw.split(",")
            if provider.strip()
        }

    def is_provider_disabled(self, provider: str) -> bool:
        return provider.strip().lower() in self.disabled_api_providers

    def has_api_key(self, provider: str) -> bool:
        if self.is_provider_disabled(provider):
            return False
        return {
            "openai": bool(self.openai_api_key),
            "anthropic": bool(self.anthropic_api_key),
            "gemini": bool(self.gemini_api_key),
        }.get(provider, False)

    def configured_api_providers(self) -> list[str]:
        return [p for p in ["openai", "anthropic", "gemini"] if self.has_api_key(p)]


_settings_instance: Settings | None = None


def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
