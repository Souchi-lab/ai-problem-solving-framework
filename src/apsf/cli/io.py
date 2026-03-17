"""
apsf.cli.io — CLI 入出力ユーティリティ

stdin の UTF-8 読み込みなど、複数コマンドで共有する低レベル I/O を集約する。
将来の `apsf act` でも再利用できるよう CLI ロジックとは独立して定義する。
"""

from __future__ import annotations

import io
import sys


def read_stdin_utf8() -> str:
    """
    標準入力をすべて読み込み、UTF-8 文字列として返す。

    Windows では sys.stdin がシステムデフォルトエンコーディング（cp932 等）で
    開かれるため、PowerShell pipe / here-string 経由の UTF-8 入力が文字化けする。
    sys.stdin.buffer を UTF-8 で再ラップすることで正しくデコードする。

    CliRunner 等 buffer 属性を持たないフェイク stdin は通常の read() にフォールバック。
    """
    if hasattr(sys.stdin, "buffer"):
        return io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8").read()
    return sys.stdin.read()
