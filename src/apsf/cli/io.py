"""
apsf.cli.io — CLI 入出力ユーティリティ

stdin の UTF-8 読み込みなど、複数コマンドで共有する低レベル I/O を集約する。
将来の `apsf act` でも再利用できるよう CLI ロジックとは独立して定義する。
"""

from __future__ import annotations

import sys


def read_stdin_utf8() -> str:
    """
    標準入力をすべて読み込み、UTF-8 文字列として返す。

    Windows では sys.stdin がシステムデフォルトエンコーディング（cp932 等）で
    開かれるため、PowerShell pipe / here-string 経由の UTF-8 入力が文字化けする。
    sys.stdin.buffer を直接読んで UTF-8 でデコードすることで正しく処理する。

    ## Windows PowerShell 5.1 でのパイプ文字化けについて

    PowerShell 5.1 はパイプ通過時に外部プロセスの stdout を
    [Console]::OutputEncoding でデコードし、$OutputEncoding で再エンコードする。
    日本語 Windows のデフォルト（cp932）では UTF-8 テキストが壊れる。

    修正方法（PowerShell セッションに 1 回設定すれば有効）:
        $OutputEncoding = [System.Text.Encoding]::UTF8
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

    PowerShell 7+ (pwsh) はデフォルトで UTF-8 のため不要。

    ## フォールバック動作

    UTF-8 でのデコードに失敗した場合（PowerShell 5.1 が cp932 変換した場合等）:
    - stderr にエンコーディング修正ガイダンスを出力する
    - cp932 でフォールバックデコードする（一部文字は置換される）

    CliRunner 等 buffer 属性を持たないフェイク stdin は通常の read() にフォールバック。
    """
    if not hasattr(sys.stdin, "buffer"):
        return sys.stdin.read()

    raw: bytes = sys.stdin.buffer.read()

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        sys.stderr.write(
            "\n[Warn] stdin のデコードに失敗しました（UTF-8 ではないバイト列を検出）。\n"
            "       PowerShell 5.1 のパイプエンコーディング変換が原因の可能性があります。\n"
            "\n"
            "       修正方法（PowerShell セッション開始時に 1 回実行）:\n"
            "         $OutputEncoding = [System.Text.Encoding]::UTF8\n"
            "         [Console]::OutputEncoding = [System.Text.Encoding]::UTF8\n"
            "\n"
            "       または PowerShell 7+ (pwsh) を使用してください。\n"
            "\n"
            "       cp932 でフォールバックデコードして続行します（文字化けの可能性あり）。\n"
        )
        return raw.decode("cp932", errors="replace")
