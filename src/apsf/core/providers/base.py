"""
BaseProvider - すべての provider の実装が守るべきインターフェース

設計前提:
- provider は「どの外部 API を呼ぶか」だけを責務にする
- agent の「何をするか」(role) とは切り離す
- generate() が唯一の共通インターフェース
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GenerateRequest:
    """API に投げるリクエスト。Provider 共通の形。"""

    prompt: str
    system: str = ""
    model: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7


@dataclass
class GenerateResponse:
    """API から返ってくるレスポンス。Provider 共通の形。"""

    content: str
    model: str
    provider: str
    raw: Optional[dict] = field(default=None, repr=False)


class ProviderError(Exception):
    """provider 側の基底エラー。"""


class AuthenticationError(ProviderError):
    """API キーが未設定または不正。"""


class RateLimitError(ProviderError):
    """レートリミット超過。"""


class ModelNotFoundError(ProviderError):
    """指定されたモデルが存在しない。"""


class BaseProvider(ABC):
    """
    すべての provider の基底クラス。
    実装クラスは generate() を実装するだけでよい。
    role / agent との結合は持たない。
    """

    def __init__(self, model: str, api_key: str = ""):
        self._model = model
        self._api_key = api_key

    @property
    def model(self) -> str:
        return self._model

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """プロバイダー名。ログ・表示に利用する。"""
        ...

    @abstractmethod
    def generate(self, request: GenerateRequest) -> GenerateResponse:
        """
        テキストを生成して返す。
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider_name}, model={self._model})"
