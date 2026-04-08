import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

CREATE_ACTION_EXECUTIONS = """
CREATE TABLE IF NOT EXISTS action_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taxonomy TEXT NOT NULL,
    run_name TEXT NOT NULL,
    action_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    command TEXT NOT NULL,
    triggered_at TEXT NOT NULL,
    finished_at TEXT,
    result_status TEXT NOT NULL,
    exit_code INTEGER,
    stdout_summary TEXT,
    stderr_summary TEXT,
    stdout_full TEXT,
    stderr_full TEXT
)
"""

CREATE_RERUN_COMMENTS = """
CREATE TABLE IF NOT EXISTS rerun_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taxonomy TEXT NOT NULL,
    run_name TEXT NOT NULL,
    action_id TEXT NOT NULL,
    execution_id INTEGER,
    comment_artifact TEXT NOT NULL,
    comment_body TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""

_SUMMARY_MAX = 2000


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _summarize(text: str, max_len: int = _SUMMARY_MAX) -> str:
    if len(text) <= max_len:
        return text
    half = max_len // 2
    return text[:half] + "\n...[truncated]...\n" + text[-half:]


class ViewerDB:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(CREATE_ACTION_EXECUTIONS)
            conn.execute(CREATE_RERUN_COMMENTS)
            self._ensure_action_execution_columns(conn)
            conn.commit()

    def _ensure_action_execution_columns(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute("PRAGMA table_info(action_executions)").fetchall()
        existing = {row["name"] for row in rows}
        if "stdout_full" not in existing:
            conn.execute("ALTER TABLE action_executions ADD COLUMN stdout_full TEXT")
        if "stderr_full" not in existing:
            conn.execute("ALTER TABLE action_executions ADD COLUMN stderr_full TEXT")

    def insert_execution_pending(
        self,
        taxonomy: str,
        run_name: str,
        action_id: str,
        action_type: str,
        command: str,
    ) -> int:
        triggered_at = _now_iso()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO action_executions
                    (taxonomy, run_name, action_id, action_type, command, triggered_at, result_status)
                VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
                """,
                (taxonomy, run_name, action_id, action_type, command, triggered_at),
            )
            conn.commit()
            return cursor.lastrowid  # type: ignore[return-value]

    def update_execution_result(
        self,
        execution_id: int,
        result_status: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        command: Optional[str] = None,
    ) -> None:
        finished_at = _now_iso()
        command_sql = ", command = ?" if command is not None else ""
        params = [
            finished_at,
            result_status,
            exit_code,
            _summarize(stdout),
            _summarize(stderr),
            stdout,
            stderr,
        ]
        if command is not None:
            params.append(command)
        params.append(execution_id)
        with self._connect() as conn:
            conn.execute(
                f"""
                UPDATE action_executions
                SET finished_at = ?, result_status = ?, exit_code = ?,
                    stdout_summary = ?, stderr_summary = ?,
                    stdout_full = ?, stderr_full = ?
                    {command_sql}
                WHERE id = ?
                """,
                tuple(params),
            )
            conn.commit()

    def insert_rerun_comment(
        self,
        taxonomy: str,
        run_name: str,
        action_id: str,
        comment_artifact: str,
        comment_body: str,
        execution_id: Optional[int] = None,
    ) -> int:
        created_at = _now_iso()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO rerun_comments
                    (taxonomy, run_name, action_id, execution_id,
                     comment_artifact, comment_body, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    taxonomy,
                    run_name,
                    action_id,
                    execution_id,
                    comment_artifact,
                    comment_body,
                    created_at,
                ),
            )
            conn.commit()
            return cursor.lastrowid  # type: ignore[return-value]

    def get_latest_execution(self, taxonomy: str, run_name: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM action_executions
                WHERE taxonomy = ? AND run_name = ?
                ORDER BY id DESC LIMIT 1
                """,
                (taxonomy, run_name),
            ).fetchone()
        return dict(row) if row is not None else None

    def list_recent_executions_for_run(self, taxonomy: str, run_name: str, limit: int = 5) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM action_executions
                WHERE taxonomy = ? AND run_name = ?
                ORDER BY id DESC LIMIT ?
                """,
                (taxonomy, run_name, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_latest_rerun_comment(self, taxonomy: str, run_name: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM rerun_comments
                WHERE taxonomy = ? AND run_name = ?
                ORDER BY id DESC LIMIT 1
                """,
                (taxonomy, run_name),
            ).fetchone()
        return dict(row) if row is not None else None

    def list_recent_executions(self, limit: int = 12, top_level_only: bool = False) -> list[dict]:
        query = """
            SELECT * FROM action_executions
        """
        params: tuple = ()
        if top_level_only:
            query += " WHERE run_name NOT LIKE ?"
            params = ("%/%",)
        query += " ORDER BY id DESC LIMIT ?"
        params = (*params, limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_execution_log(self, execution_id: int) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, taxonomy, run_name, action_id, action_type, command,
                       triggered_at, finished_at, result_status, exit_code,
                       stdout_summary, stderr_summary, stdout_full, stderr_full
                FROM action_executions
                WHERE id = ?
                """,
                (execution_id,),
            ).fetchone()
        return dict(row) if row is not None else None
