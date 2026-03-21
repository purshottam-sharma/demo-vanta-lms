#!/usr/bin/env python3
"""
Visual diff helper: starts the Vite dev server (if not running), injects mock
auth into sessionStorage, mocks the /api/v1/users/me endpoint, screenshots
the target route, and saves the PNG to the given output path.

Usage:
    # Full-page screenshot
    python3 agents/shared/playwright_screenshot.py <route> <output_path> [width] [height]

    # Element-level screenshot (eliminates Y-alignment issues with Figma)
    python3 agents/shared/playwright_screenshot.py <route> <output_path> --selector "[data-component='school-health']"

Examples:
    python3 agents/shared/playwright_screenshot.py /dashboard /tmp/rendered-86d2c0nmj.png
    python3 agents/shared/playwright_screenshot.py /dashboard /tmp/rendered.png 1440 1332
    python3 agents/shared/playwright_screenshot.py /dashboard /tmp/school-health.png --selector "[data-component='school-health']"
"""

import sys
import time
import subprocess
import socket
import os
import json
import argparse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# Vite can start on 3000, 3001, 3002, etc. if a port is occupied.
DEV_PORT_CANDIDATES = [3000, 3001, 3002, 3003, 5173]
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


def find_vite_port() -> int | None:
    """Find the port where the Vite dev server is serving HTML."""
    import urllib.request
    for port in DEV_PORT_CANDIDATES:
        if not is_port_open(port):
            continue
        try:
            with urllib.request.urlopen(f"http://localhost:{port}/", timeout=2) as resp:
                content = resp.read(500).decode("utf-8", errors="ignore")
                if "vite" in content.lower() or "<!doctype html" in content.lower():
                    return port
        except Exception:
            continue
    return None


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
    viewport_height: int = 1332,
    selector: str | None = None,
) -> None:
    """
    Take a screenshot of a route.

    If selector is provided, screenshots only the matching element (bounding box crop).
    This eliminates Y-coordinate misalignment between Figma sections and rendered layout.
    Element screenshots are saved at the element's natural size — compare against the
    corresponding Figma crop (not the full Figma frame).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    server_proc = None
    started_server = False

    dev_port = find_vite_port()
    if dev_port is None:
        print("Dev server not detected — starting...", flush=True)
        server_proc = subprocess.Popen(
            ["npx", "nx", "serve", "web"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(40):
            time.sleep(1)
            dev_port = find_vite_port()
            if dev_port:
                break
        if not dev_port:
            server_proc.terminate()
            raise RuntimeError("Dev server did not become ready within 40s")
        time.sleep(2)  # HMR warm-up buffer
        started_server = True
    print(f"Dev server on :{dev_port}", flush=True)

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

            url = f"http://localhost:{dev_port}{route}"
            print(f"Navigating to {url} ...", flush=True)
            page.goto(url, wait_until="networkidle", timeout=30_000)
            page.wait_for_timeout(2000)  # Extra buffer for web fonts / CSS injection

            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

            if selector:
                # Element-level screenshot: only captures the matched element's bounding box.
                # This bypasses Y-coordinate misalignment between Figma and rendered layout.
                element = page.locator(selector).first
                element.wait_for(state="visible", timeout=5000)
                element.screenshot(path=output_path)
                box = element.bounding_box()
                print(f"Element screenshot saved → {output_path} (size: {box['width']:.0f}x{box['height']:.0f})", flush=True)
            else:
                page.screenshot(path=output_path, full_page=True)
                print(f"Screenshot saved → {output_path}", flush=True)

            browser.close()

    finally:
        if started_server and server_proc:
            print("Stopping dev server...", flush=True)
            server_proc.terminate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Screenshot a Vite dev route for visual diff")
    parser.add_argument("route", help="Frontend route, e.g. /dashboard")
    parser.add_argument("output", help="Output PNG path")
    parser.add_argument("width", nargs="?", type=int, default=1440)
    parser.add_argument("height", nargs="?", type=int, default=1332)
    parser.add_argument("--selector", help="CSS selector for element-level screenshot, e.g. \"[data-component='school-health']\"")
    args = parser.parse_args()

    screenshot(args.route, args.output, args.width, args.height, args.selector)
