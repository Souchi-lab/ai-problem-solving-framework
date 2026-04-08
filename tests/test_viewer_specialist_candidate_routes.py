from __future__ import annotations

from pathlib import Path

from starlette.routing import Match

from apsf.viewer.api import app


def _matching_route_paths(path: str, method: str = "GET") -> list[str]:
    scope = {
        "type": "http",
        "path": path,
        "method": method,
        "root_path": "",
        "scheme": "http",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 123),
        "server": ("testserver", 80),
    }
    matched: list[str] = []
    for route in app.router.routes:
        route_match, _ = route.matches(scope)
        if route_match is Match.FULL:
            matched.append(getattr(route, "path", ""))
    return matched


def test_specialist_candidates_route_precedes_broad_run_detail_route() -> None:
    matches = _matching_route_paths(
        "/api/runs/work/2026-04-04-001_parent/001c2_child/specialist-candidates"
    )

    assert "/api/runs/{taxonomy}/{run_name:path}/specialist-candidates" in matches
    assert "/api/runs/{taxonomy}/{run_name:path}" in matches
    assert matches.index("/api/runs/{taxonomy}/{run_name:path}/specialist-candidates") < matches.index(
        "/api/runs/{taxonomy}/{run_name:path}"
    )


def test_specialist_create_route_precedes_broad_run_detail_route() -> None:
    matches = _matching_route_paths(
        "/api/runs/work/2026-04-04-001_parent/001c2_child/specialists/create",
        method="POST",
    )

    assert "/api/runs/{taxonomy}/{run_name:path}/specialists/create" in matches
