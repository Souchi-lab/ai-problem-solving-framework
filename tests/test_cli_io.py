"""
test_cli_io.py — apsf.cli.io のユニットテスト

read_stdin_utf8() のエンコーディング処理を検証する:
- UTF-8 バイト列 → 正常デコード
- cp932 バイト列 → フォールバックデコード + stderr 警告
- buffer なし stdin → sys.stdin.read() フォールバック
"""

from __future__ import annotations

import io
import sys
from unittest.mock import MagicMock, patch


class TestReadStdinUtf8:
    """read_stdin_utf8() のエンコーディング処理テスト"""

    def _call(self):
        from apsf.cli.io import read_stdin_utf8
        return read_stdin_utf8

    def test_utf8_bytes_decoded_correctly(self) -> None:
        """UTF-8 バイト列は正常にデコードされる。"""
        text = "Hello, 日本語テスト\n"
        raw = text.encode("utf-8")

        mock_stdin = MagicMock()
        mock_stdin.buffer = io.BytesIO(raw)

        with patch("sys.stdin", mock_stdin):
            result = self._call()()

        assert result == text

    def test_ascii_utf8_bytes(self) -> None:
        """ASCII のみの UTF-8 バイト列は正常デコードされる。"""
        text = "Hello, world\nLine 2\n"
        raw = text.encode("utf-8")

        mock_stdin = MagicMock()
        mock_stdin.buffer = io.BytesIO(raw)

        with patch("sys.stdin", mock_stdin):
            result = self._call()()

        assert result == text

    def test_cp932_bytes_fallback_with_stderr_warning(
        self, capsys
    ) -> None:
        """cp932 バイト列（UTF-8 デコード失敗）は stderr に警告を出してフォールバックする。"""
        text = "テスト文字列"
        raw = text.encode("cp932")  # cp932 エンコード → UTF-8 では無効なバイト列

        mock_stdin = MagicMock()
        mock_stdin.buffer = io.BytesIO(raw)

        with patch("sys.stdin", mock_stdin):
            result = self._call()()

        # cp932 でデコードできる文字は復元される
        assert "テスト文字列" in result

        # stderr に警告が出る
        captured = capsys.readouterr()
        assert "[Warn]" in captured.err
        assert "PowerShell" in captured.err
        assert "$OutputEncoding" in captured.err
        assert "[Console]::OutputEncoding" in captured.err

    def test_cp932_fallback_mentions_utf8_fix(self, capsys) -> None:
        """フォールバック時の警告に UTF-8 修正コマンドが含まれる。"""
        raw = "日本語".encode("cp932")

        mock_stdin = MagicMock()
        mock_stdin.buffer = io.BytesIO(raw)

        with patch("sys.stdin", mock_stdin):
            self._call()()

        captured = capsys.readouterr()
        assert "UTF-8" in captured.err
        assert "pwsh" in captured.err

    def test_no_buffer_falls_back_to_read(self) -> None:
        """buffer 属性のない stdin (CliRunner 等) は sys.stdin.read() にフォールバック。"""
        text = "fallback content\n"

        mock_stdin = MagicMock(spec=[])  # buffer 属性なし
        mock_stdin.read = MagicMock(return_value=text)

        with patch("sys.stdin", mock_stdin):
            result = self._call()()

        assert result == text
        mock_stdin.read.assert_called_once()

    def test_empty_stdin(self) -> None:
        """空の stdin は空文字列を返す。"""
        mock_stdin = MagicMock()
        mock_stdin.buffer = io.BytesIO(b"")

        with patch("sys.stdin", mock_stdin):
            result = self._call()()

        assert result == ""
