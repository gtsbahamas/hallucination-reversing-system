"""Shared test helpers for app generation evaluation.

Provides utilities to build, start, and test generated applications.
Tests score against the 5-point rubric:
  - Builds (20%): npm install + build succeeds
  - Renders (15%): dev server starts, pages return 200
  - Core functionality (35%): requirements met
  - Edge cases (15%): handles edge inputs
  - Error handling (15%): graceful degradation
"""

import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx


@dataclass
class BuildResult:
    """Result of attempting to build an app."""
    success: bool
    clean: bool = False  # True if no warnings
    install_output: str = ""
    build_output: str = ""
    error: str = ""


@dataclass
class ServerHandle:
    """Handle to a running dev server process."""
    process: subprocess.Popen
    port: int
    base_url: str

    def stop(self):
        """Stop the dev server."""
        try:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
        except (ProcessLookupError, OSError):
            pass
        self.process.wait(timeout=5)


@dataclass
class RubricScore:
    """Score on the 5-point rubric."""
    builds: int = 0       # 0, 1, or 2
    renders: int = 0      # 0, 1, or 2
    core: int = 0         # 0, 1, or 2
    edge: int = 0         # 0, 1, or 2
    error: int = 0        # 0, 1, or 2
    details: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def weighted_score(self) -> float:
        """Compute weighted score (0.0 to 1.0)."""
        return (
            (self.builds / 2) * 0.20
            + (self.renders / 2) * 0.15
            + (self.core / 2) * 0.35
            + (self.edge / 2) * 0.15
            + (self.error / 2) * 0.15
        )

    @property
    def percentage(self) -> float:
        return self.weighted_score * 100

    def to_dict(self) -> dict:
        return {
            "builds": self.builds,
            "renders": self.renders,
            "core": self.core,
            "edge": self.edge,
            "error": self.error,
            "weighted_score": self.weighted_score,
            "percentage": self.percentage,
            "details": self.details,
        }


def detect_framework(app_dir: str) -> str:
    """Detect which framework the generated app uses."""
    pkg_path = os.path.join(app_dir, "package.json")
    if os.path.exists(pkg_path):
        with open(pkg_path) as f:
            pkg = json.load(f)
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        if "next" in deps:
            return "next"
        if "vite" in deps or "@vitejs/plugin-react" in deps:
            return "vite"
        if "react-scripts" in deps:
            return "cra"
        if "vue" in deps:
            return "vue"
        if "svelte" in deps:
            return "svelte"
        return "node"

    # Python frameworks
    req_path = os.path.join(app_dir, "requirements.txt")
    if os.path.exists(req_path):
        with open(req_path) as f:
            reqs = f.read().lower()
        if "flask" in reqs:
            return "flask"
        if "fastapi" in reqs:
            return "fastapi"
        if "django" in reqs:
            return "django"
        return "python"

    return "unknown"


def install_deps(app_dir: str, timeout: int = 120) -> Tuple[bool, str]:
    """Run npm install (or pip install) and return (success, output)."""
    framework = detect_framework(app_dir)

    if framework in ("flask", "fastapi", "django", "python"):
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    else:
        cmd = ["npm", "install"]

    try:
        result = subprocess.run(
            cmd,
            cwd=app_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Install timed out"
    except FileNotFoundError as e:
        return False, f"Command not found: {e}"


def build_app(app_dir: str, timeout: int = 120) -> BuildResult:
    """Install deps and build the app."""
    ok, install_out = install_deps(app_dir)
    if not ok:
        return BuildResult(
            success=False,
            install_output=install_out,
            error="Install failed",
        )

    framework = detect_framework(app_dir)

    # Not all frameworks need a build step for dev mode
    if framework in ("flask", "fastapi", "django", "python"):
        return BuildResult(success=True, clean=True, install_output=install_out)

    # Try npm run build
    pkg_path = os.path.join(app_dir, "package.json")
    if os.path.exists(pkg_path):
        with open(pkg_path) as f:
            pkg = json.load(f)
        if "build" not in pkg.get("scripts", {}):
            # No build script -- that's fine for dev mode
            return BuildResult(success=True, clean=True, install_output=install_out)

    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=app_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        clean = result.returncode == 0 and "warning" not in result.stderr.lower()
        return BuildResult(
            success=result.returncode == 0,
            clean=clean,
            install_output=install_out,
            build_output=result.stdout + result.stderr,
        )
    except subprocess.TimeoutExpired:
        return BuildResult(success=False, error="Build timed out")


def start_server(app_dir: str, port: int = 0, timeout: int = 30) -> Optional[ServerHandle]:
    """Start the dev server and wait for it to be ready.

    If port is 0, a random available port is chosen.
    Returns None if the server fails to start.
    """
    if port == 0:
        import socket
        with socket.socket() as s:
            s.bind(("", 0))
            port = s.getsockname()[1]

    framework = detect_framework(app_dir)
    env = {**os.environ, "PORT": str(port)}

    if framework == "next":
        cmd = ["npx", "next", "dev", "-p", str(port)]
    elif framework == "vite":
        cmd = ["npx", "vite", "--port", str(port), "--strictPort"]
    elif framework == "cra":
        cmd = ["npx", "react-scripts", "start"]
        env["BROWSER"] = "none"
    elif framework == "flask":
        cmd = [sys.executable, "-m", "flask", "run", "--port", str(port)]
        env["FLASK_APP"] = "app.py"
    elif framework == "fastapi":
        cmd = [sys.executable, "-m", "uvicorn", "main:app", "--port", str(port)]
    else:
        # Fallback: try npm start
        cmd = ["npm", "start"]

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=app_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )
    except FileNotFoundError:
        return None

    base_url = f"http://localhost:{port}"
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            resp = httpx.get(base_url, timeout=2, follow_redirects=True)
            if resp.status_code < 500:
                return ServerHandle(process=proc, port=port, base_url=base_url)
        except (httpx.ConnectError, httpx.ReadTimeout):
            pass

        if proc.poll() is not None:
            return None

        time.sleep(0.5)

    # Timed out waiting for server
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (ProcessLookupError, OSError):
        pass
    return None


def check_route(base_url: str, path: str = "/", expect_status: int = 200) -> bool:
    """Check that a route returns the expected status."""
    try:
        resp = httpx.get(f"{base_url}{path}", timeout=10, follow_redirects=True)
        return resp.status_code == expect_status
    except (httpx.ConnectError, httpx.ReadTimeout):
        return False


def check_html_contains(base_url: str, path: str, texts: List[str]) -> List[bool]:
    """Check that a page's HTML contains the given text strings."""
    try:
        resp = httpx.get(f"{base_url}{path}", timeout=10, follow_redirects=True)
        html = resp.text.lower()
        return [t.lower() in html for t in texts]
    except (httpx.ConnectError, httpx.ReadTimeout):
        return [False] * len(texts)


def check_api_json(
    base_url: str,
    method: str,
    path: str,
    body: Optional[dict] = None,
    expect_status: int = 200,
) -> Tuple[bool, Optional[dict]]:
    """Make an API call and check status. Returns (status_ok, response_json)."""
    try:
        client = httpx.Client(base_url=base_url, timeout=10)
        if method.upper() == "GET":
            resp = client.get(path)
        elif method.upper() == "POST":
            resp = client.post(path, json=body)
        elif method.upper() == "PUT":
            resp = client.put(path, json=body)
        elif method.upper() == "DELETE":
            resp = client.delete(path)
        else:
            return False, None
        client.close()

        status_ok = resp.status_code == expect_status
        try:
            data = resp.json()
        except (json.JSONDecodeError, ValueError):
            data = None
        return status_ok, data
    except (httpx.ConnectError, httpx.ReadTimeout):
        return False, None
