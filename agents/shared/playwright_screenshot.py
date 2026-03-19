#!/usr/bin/env python3
"""
Visual diff helper: starts the Vite dev server (if not running), injects mock
auth into sessionStorage, mocks the /api/v1/users/me endpoint, screenshots
the target route, and saves the PNG to the given output path.

Usage:
    python3 agents/shared/playwright_screenshot.py <route> <output_path> [width] [height]

Examples:
    python3 agents/shared/playwright_screenshot.py /dashboard /tmp/rendered-86d2c0nmj.png
    python3 agents/shared/playwright_screenshot.py /dashboard /tmp/rendered.png 1440 900
"""

import sys
import time
import subprocess
import socket
import os
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEV_PORT = 5173
MOCK_USER = json.dumps({
    "id": "visual-diff-user",
    "email": "demo@vanta.lms",
    "full_name": "Demo User",
    "is_active": True,
})


def is_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("localhost", port)) == 0


def wait_for_port(port: int, timeout: int = 40) -> bool:
    for _ in range(timeout):
        if is_port_open(port):
            return True
        time.sleep(1)
    return False


def screenshot(
    route: str,
    output_path: str,
    viewport_width: int = 1440,
    viewport_height: int = 900,
) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    server_proc = None
    started_server = False

    if not is_port_open(DEV_PORT):
        print(f"Dev server not running on :{DEV_PORT} — starting...", flush=True)
        server_proc = subprocess.Popen(
            ["npx", "nx", "serve", "web"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not wait_for_port(DEV_PORT, timeout=40):
            server_proc.terminate()
            raise RuntimeError(f"Dev server did not become ready on :{DEV_PORT} within 40s")
        time.sleep(2)  # HMR warm-up buffer
        started_server = True
        print(f"Dev server ready on :{DEV_PORT}", flush=True)
    else:
        print(f"Dev server already running on :{DEV_PORT}", flush=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(
                viewport={"width": viewport_width, "height": viewport_height}
            )

            # Inject mock auth token into sessionStorage before page load.
            # Matches the Zustand persist key used by auth-store.ts.
            page.add_init_script(f"""
                sessionStorage.setItem('vanta-auth', JSON.stringify({{
                    state: {{ accessToken: 'visual-diff-mock-token' }},
                    version: 0
                }}));
            """)

            # Mock GET /api/v1/users/me so Navbar renders with a real user name.
            page.route(
                "**/api/v1/users/me",
                lambda route: route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=MOCK_USER,
                ),
            )

            url = f"http://localhost:{DEV_PORT}{route}"
            print(f"Navigating to {url} ...", flush=True)
            page.goto(url, wait_until="networkidle", timeout=30_000)
            page.wait_for_timeout(1500)  # Extra buffer for web fonts / images

            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            page.screenshot(path=output_path, full_page=False)
            browser.close()
            print(f"Screenshot saved → {output_path}", flush=True)

    finally:
        if started_server and server_proc:
            print("Stopping dev server...", flush=True)
            server_proc.terminate()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    _route = sys.argv[1]
    _output = sys.argv[2]
    _width = int(sys.argv[3]) if len(sys.argv) > 3 else 1440
    _height = int(sys.argv[4]) if len(sys.argv) > 4 else 900

    screenshot(_route, _output, _width, _height)
