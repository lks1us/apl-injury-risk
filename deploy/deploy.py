"""Deploy APL Injury Risk to PythonAnywhere via API.

Usage (PowerShell):
    $env:PYTHONANYWHERE_API_TOKEN = "your-token-here"
    python deploy/deploy.py
"""
from __future__ import annotations

import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USERNAME = "L1ksius"
HOST = "www.pythonanywhere.com"
DOMAIN = f"{USERNAME.lower()}.pythonanywhere.com"
PROJECT_DIR = f"/home/{USERNAME}/apl-injury-risk"
VENV = f"/home/{USERNAME}/.virtualenvs/apl-risk"
REPO = "https://github.com/lks1us/apl-injury-risk.git"
BASE = Path(__file__).resolve().parent.parent


def token() -> str:
    value = os.environ.get("PYTHONANYWHERE_API_TOKEN") or os.environ.get("API_TOKEN")
    if not value:
        print("Set PYTHONANYWHERE_API_TOKEN environment variable.")
        print("Get it: pythonanywhere.com -> Account -> API token -> Create")
        sys.exit(1)
    return value.strip()


def api(method: str, path: str, data: dict | None = None, raw: bytes | None = None, content_type: str | None = None):
    url = f"https://{HOST}{path}"
    headers = {"Authorization": f"Token {token()}"}
    body = raw
    if data is not None:
        body = urllib.parse.urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if content_type:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            content = response.read()
            return response.status, content
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def run_bash(script: str) -> None:
    status, content = api("POST", f"/api/v0/user/{USERNAME}/consoles/", data={"executable": "bash"})
    if status not in (200, 201):
        raise RuntimeError(f"Cannot create console: {status} {content!r}")

    console_id = json.loads(content.decode("utf-8"))["id"]
    print(f"Console {console_id} created, running setup...")

    for line in script.strip().splitlines():
        command = line.strip()
        if not command or command.startswith("#"):
            continue
        payload = f"{command}\n"
        sent_status, sent_body = api(
            "POST",
            f"/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/",
            data={"input": payload},
        )
        if sent_status != 200:
            raise RuntimeError(f"Command failed: {command!r} -> {sent_status} {sent_body!r}")
        time.sleep(2 if "pip install" in command or "git clone" in command else 1)

    for _ in range(30):
        time.sleep(3)
        out_status, out_body = api(
            "GET",
            f"/api/v0/user/{USERNAME}/consoles/{console_id}/get_latest_output/",
        )
        text = out_body.decode("utf-8", errors="replace")
        if "SETUP_DONE" in text:
            print("Setup commands finished.")
            break
    else:
        print("Warning: setup may still be running. Check PythonAnywhere consoles.")

    api("DELETE", f"/api/v0/user/{USERNAME}/consoles/{console_id}/")


def ensure_webapp(secret_key: str) -> None:
    domain_path = f"/api/v0/user/{USERNAME}/webapps/{DOMAIN}/"
    status, _ = api("GET", domain_path)
    if status == 404:
        created_status, created_body = api(
            "POST",
            f"/api/v0/user/{USERNAME}/webapps/",
            data={"domain_name": DOMAIN, "python_version": "python310"},
        )
        if created_status not in (200, 201):
            raise RuntimeError(f"Cannot create webapp: {created_status} {created_body!r}")
        print(f"Web app created: {DOMAIN}")

    patched_status, patched_body = api(
        "PATCH",
        domain_path,
        data={
            "source_directory": PROJECT_DIR,
            "virtualenv_path": VENV,
            "force_https": "true",
        },
    )
    if patched_status != 200:
        raise RuntimeError(f"Cannot configure webapp: {patched_status} {patched_body!r}")

    wsgi = f'''import os
import sys

path = "{PROJECT_DIR}"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["DJANGO_SECRET_KEY"] = "{secret_key}"
os.environ["DJANGO_DEBUG"] = "False"
os.environ["DJANGO_ALLOWED_HOSTS"] = "{DOMAIN},{USERNAME}.pythonanywhere.com"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apl_risk.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
'''
    wsgi_path = f"/var/www/{USERNAME}_pythonanywhere_com_wsgi.py"
    boundary = "----apldeployboundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="content"; filename="wsgi.py"\r\n'
        f"Content-Type: text/plain\r\n\r\n"
        f"{wsgi}\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    uploaded_status, uploaded_body = api(
        "POST",
        f"/api/v0/user/{USERNAME}/files/path{wsgi_path}",
        raw=body,
        content_type=f"multipart/form-data; boundary={boundary}",
    )
    if uploaded_status not in (200, 201):
        raise RuntimeError(f"Cannot upload WSGI: {uploaded_status} {uploaded_body!r}")

    static_status, static_body = api("GET", f"/api/v0/user/{USERNAME}/webapps/{DOMAIN}/static_files/")
    mappings = json.loads(static_body.decode("utf-8")) if static_status == 200 else []
    has_static = any(m.get("url") == "/static/" for m in mappings)
    if not has_static:
        created_status, created_body = api(
            "POST",
            f"/api/v0/user/{USERNAME}/webapps/{DOMAIN}/static_files/",
            data={"url": "/static/", "path": f"{PROJECT_DIR}/staticfiles"},
        )
        if created_status not in (200, 201):
            raise RuntimeError(f"Cannot add static mapping: {created_status} {created_body!r}")

    reloaded_status, reloaded_body = api("POST", f"/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/")
    if reloaded_status != 200:
        raise RuntimeError(f"Cannot reload webapp: {reloaded_status} {reloaded_body!r}")

    print(f"Site live: https://{DOMAIN}/")


def main() -> None:
    secret_key = secrets.token_urlsafe(50)
    setup_script = f"""
cd ~
if [ ! -d apl-injury-risk ]; then
  git clone {REPO}
fi
cd apl-injury-risk
git pull
if [ ! -d ~/.virtualenvs/apl-risk ]; then
  mkvirtualenv --python=/usr/bin/python3.10 apl-risk
fi
workon apl-risk
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py seed_demo
python manage.py collectstatic --noinput
echo SETUP_DONE
"""
    run_bash(setup_script)
    ensure_webapp(secret_key)
    print("Deployment complete.")


if __name__ == "__main__":
    main()
