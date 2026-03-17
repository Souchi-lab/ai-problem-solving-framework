"""
BaseProvider — すべての provider が実装する共通インターフェース

設計原則:
- provider は「どの会社の API を呼ぶか」だけを担当する
- agent の「何をするか（role）」は知らない
- generate() が唯一の外部向けインターフェース
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GenerateRequest:
    """API に渡すリクエスト。provider 共通の形式。"""

    prompt: str
    system: str = ""
    model: str = ""  # 空の場合は provider のデフォルトモデルを使用
    max_tokens: int = 4096
    temperature: float = 0.7


@dataclass
class GenerateResponse:
    """API から受け取るレスポンス。provider 共通の形式。"""

    content: str
    model: str
    provider: str
    raw: Optional[dict] = field(default=None, repr=False)  # 元のレスポンスを保存（デバッグ用）


class ProviderError(Exception):
    """provider 層の基底例外"""
    pass


class AuthenticationError(ProviderError):
    """API キーが未設定または無効"""
    pass


class RateLimitError(ProviderError):
    """レートリミット超過"""
    pass


class ModelNotFoundError(ProviderError):
    """指定されたモデルが存在しない"""
    pass


class BaseProvider(ABC):
    """
    すべての provider の基底クラス。

    実装クラスは generate() を実装するだけでよい。
    role / agent との依存は持たない。
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
        """プロバイダー名。ログ・表示に使用。"""
        ...

    @abstractmethod
    def generate(self, request: GenerateRequest) -> GenerateResponse:
        """
        テキストを生成して返す。

        Args:
            request: プロンプト・システムメッセージ・モデル設定

        Returns:
            GenerateResponse: 生成されたテキストとメタ情報

        Raises:
            AuthenticationError: API キーが無効
            RateLimitError: レートリミット超過
            ProviderError: その他の API エラー
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider_name}, model={self._model})"
