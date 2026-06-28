#!/usr/bin/env python3
"""JS renderer for opportunity scanner — uses headless Chrome via CDP.

Fetches pages that require JavaScript rendering (Product Hunt, Indie Hackers, Reddit).
Uses Chrome's --remote-debugging-port for reliable page loading.
"""

import json
import subprocess
import sys
import time
import urllib.request
import socket
import os
import signal
import atexit
from pathlib import Path

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEBUG_PORT = 9222
PROFILE_DIR = Path(__file__).resolve().parent / ".chrome_profile"
_process = None


def start_chrome():
    """Start Chrome with remote debugging port."""
    global _process
    if _process is not None:
        return
    PROFILE_DIR.mkdir(exist_ok=True)
    cmd = [
        CHROME_PATH,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={PROFILE_DIR}",
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--disable-extensions",
        "--window-size=1280,720",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    ]
    _process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Wait for debug endpoint
    for _ in range(20):
        try:
            urllib.request.urlopen(f"http://localhost:{DEBUG_PORT}/json/version", timeout=1)
            return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Chrome debug port didn't respond")


def stop_chrome():
    """Kill Chrome process."""
    global _process
    if _process:
        try:
            _process.terminate()
            _process.wait(timeout=5)
        except Exception:
            _process.kill()
        _process = None


atexit.register(stop_chrome)


def get_ws_url():
    """Get WebSocket debugger URL for first page."""
    resp = urllib.request.urlopen(f"http://localhost:{DEBUG_PORT}/json")
    tabs = json.loads(resp.read())
    for tab in tabs:
        if tab.get("type") == "page":
            return tab["webSocketDebuggerUrl"]
    # Create new tab
    resp = urllib.request.urlopen(f"http://localhost:{DEBUG_PORT}/json/new?about:blank")
    tab = json.loads(resp.read())
    return tab["webSocketDebuggerUrl"]


def cdp_send(ws, method, params=None, timeout=15):
    """Send CDP command and get response via raw WebSocket (no deps)."""
    import hashlib
    import base64
    import struct

    msg_id = int(time.time() * 1000) % 1000000
    msg = json.dumps({"id": msg_id, "method": method, "params": params or {}})

    # Minimal WebSocket client
    import ssl
    from urllib.parse import urlparse
    parsed = urlparse(ws)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "wss" else 80)
    path = parsed.path

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect((host, port))

    if parsed.scheme == "wss":
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        sock = ctx.wrap_socket(sock, server_hostname=host)

    # WebSocket handshake
    key = base64.b64encode(os.urandom(16)).decode()
    handshake = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n\r\n"
    )
    sock.send(handshake.encode())

    # Read response headers
    header_data = b""
    while b"\r\n\r\n" not in header_data:
        header_data += sock.recv(4096)

    # Send frame
    payload = msg.encode("utf-8")
    frame = bytearray()
    frame.append(0x81)  # text frame
    mask_key = os.urandom(4)
    length = len(payload)
    if length < 126:
        frame.append(0x80 | length)
    elif length < 65536:
        frame.append(0x80 | 126)
        frame.extend(struct.pack(">H", length))
    else:
        frame.append(0x80 | 127)
        frame.extend(struct.pack(">Q", length))
    frame.extend(mask_key)
    masked = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(payload))
    frame.extend(masked)
    sock.send(frame)

    # Read response frames until we get msg_id match
    buf = b""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buf += chunk
            # Try to parse frames
            while len(buf) >= 2:
                opcode = buf[0] & 0x0F
                masked = (buf[1] & 0x80) != 0
                length = buf[1] & 0x7F
                offset = 2
                if length == 126:
                    if len(buf) < 4:
                        break
                    length = struct.unpack(">H", buf[2:4])[0]
                    offset = 4
                elif length == 127:
                    if len(buf) < 10:
                        break
                    length = struct.unpack(">Q", buf[2:10])[0]
                    offset = 10
                if masked:
                    offset += 4
                if len(buf) < offset + length:
                    break
                payload_data = buf[offset:offset + length]
                if masked:
                    mk = buf[offset - 4:offset]
                    payload_data = bytearray(b ^ mk[i % 4] for i, b in enumerate(payload_data))
                buf = buf[offset + length:]
                if opcode == 1:  # text
                    try:
                        result = json.loads(payload_data.decode("utf-8"))
                        if result.get("id") == msg_id:
                            sock.close()
                            return result
                    except Exception:
                        pass
        except socket.timeout:
            break
    sock.close()
    return None


def render_page(url: str, wait_seconds: float = 3.0) -> str:
    """Load a page in headless Chrome and return the DOM HTML."""
    start_chrome()
    ws_url = get_ws_url()

    # Navigate
    cdp_send(ws_url, "Page.enable")
    cdp_send(ws_url, "Page.navigate", {"url": url})

    # Wait for load
    time.sleep(wait_seconds)

    # Get DOM
    result = cdp_send(ws_url, "Runtime.evaluate", {
        "expression": "document.documentElement.outerHTML",
        "returnByValue": True,
    })

    if result and "result" in result:
        return result["result"]["result"].get("value", "")
    return ""


def render_and_extract_links(url: str, pattern: str, prefix: str = "",
                              wait: float = 4.0) -> list:
    """Render a page and extract links matching a regex pattern."""
    try:
        html = render_page(url, wait_seconds=wait)
    except Exception as e:
        return []

    results = []
    seen = set()
    for match in re.finditer(pattern, html):
        value = match.group(1)
        if value not in seen:
            seen.add(value)
            link = f"{prefix}{value}" if prefix else value
            results.append({"slug": value, "url": link})
    return results


# ── Direct exports for scanner integration ──

import re

def fetch_producthunt_chrome(limit: int = 10) -> list[dict]:
    """Fetch Product Hunt launches using headless Chrome (extracts from rendered text)."""
    try:
        start_chrome()
        ws = get_ws_url()
        cdp_send(ws, "Page.enable")
        cdp_send(ws, "Page.navigate", {"url": "https://www.producthunt.com"})
        time.sleep(5)
        result = cdp_send(ws, "Runtime.evaluate", {
            "expression": "document.body.innerText",
            "returnByValue": True,
        })
        text = result["result"]["result"]["value"]
    except Exception:
        return []

    # Pattern: NUMBER. NAME\nDESCRIPTION\nTAG1•TAG2\n\nVOTES\n\nCOMMENTS
    products = re.findall(
        r'(\d+)\.\s+(.+?)\n(.+?)\n(?:[A-Za-z\s•]+)\n\n(\d+)\n\n(\d+)',
        text,
    )
    results = []
    seen = set()
    for num, name, desc, votes, comments in products[:limit * 2]:
        name = name.strip()
        if name.lower() in seen or len(name) < 3:
            continue
        seen.add(name.lower())
        slug = name.lower().replace(" ", "-")
        results.append({
            "source": "producthunt",
            "title": name[:100],
            "url": f"https://www.producthunt.com/posts/{slug}",
            "score": int(votes),
            "comments": int(comments),
            "text": desc.strip()[:200],
        })
        if len(results) >= limit:
            break
    return results


def fetch_indiehackers_chrome(limit: int = 10) -> list[dict]:
    """Fetch Indie Hackers latest posts using headless Chrome."""
    try:
        start_chrome()
        ws = get_ws_url()
        cdp_send(ws, "Page.enable")
        cdp_send(ws, "Page.navigate", {"url": "https://www.indiehackers.com/latest"})
        time.sleep(6)
        result = cdp_send(ws, "Runtime.evaluate", {
            "expression": "document.body.innerText",
            "returnByValue": True,
        })
        text = result["result"]["result"]["value"]
    except Exception:
        return []

    # Remove blank lines, then match: TITLE\nAUTHOR\nUPVOTES\nCOMMENTS
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    results = []
    seen = set()
    i = 0
    while i < len(lines) - 3:
        title = lines[i]
        author = lines[i + 1]
        upvotes = lines[i + 2]
        comments = lines[i + 3]
        if (upvotes.isdigit() and comments.isdigit()
                and 10 <= len(title) <= 150
                and len(author) > 1 and title.lower() not in seen):
            seen.add(title.lower())
            results.append({
                "source": "indiehackers",
                "title": title[:120],
                "url": "https://www.indiehackers.com/latest",
                "score": int(upvotes),
                "comments": int(comments),
                "author": author.strip(),
                "text": title,
            })
            i += 4
        else:
            i += 1
        if len(results) >= limit:
            break
    return results


def fetch_reddit_chrome(subreddit: str = "startups", limit: int = 20) -> list[dict]:
    """Fetch Reddit posts using old.reddit.com via headless Chrome."""
    url = f"https://old.reddit.com/r/{subreddit}/"
    try:
        start_chrome()
        ws = get_ws_url()
        cdp_send(ws, "Page.enable")
        cdp_send(ws, "Page.navigate", {"url": url})
        time.sleep(5)
        result = cdp_send(ws, "Runtime.evaluate", {
            "expression": "document.body.innerText",
            "returnByValue": True,
        })
        text = result["result"]["result"]["value"]
    except Exception:
        return []

    if "blocked" in text.lower() and len(text) < 2000:
        return []

    # old.reddit text pattern: TITLE by AUTHOR • TIME\nSCORE points • NUM_COMMENTS comments
    posts = re.findall(
        r'(.{10,120})\n(.+?)\n(\d+) points? • (\d+) comments?',
        text,
    )
    results = []
    seen = set()
    for title, meta, score, comments in posts[:limit]:
        title = title.strip()
        if title.lower() in seen or len(title) < 10:
            continue
        seen.add(title.lower())
        results.append({
            "source": "reddit",
            "title": title[:150],
            "url": f"https://old.reddit.com/r/{subreddit}/",
            "score": int(score),
            "comments": int(comments),
            "text": title,
        })
    return results


if __name__ == "__main__":
    print("Testing JS renderer...")
    print("\n--- Product Hunt ---")
    ph = fetch_producthunt_chrome(5)
    for p in ph:
        print(f"  {p['title']}")
    if not ph:
        print("  (empty - Cloudflare may be blocking)")

    print("\n--- Indie Hackers ---")
    ih = fetch_indiehackers_chrome(5)
    for p in ih:
        print(f"  {p['title'][:70]}")
    if not ih:
        print("  (empty - JS rendering issue)")

    print("\n--- Reddit ---")
    rd = fetch_reddit_chrome("startups", 5)
    for p in rd:
        print(f"  {p['title'][:70]}")
    if not rd:
        print("  (empty - blocked)")

    stop_chrome()
    print("\nDone.")
