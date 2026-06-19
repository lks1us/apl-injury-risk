"""Upload project updates and reseed database on PythonAnywhere."""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

TOKEN = os.environ["PYTHONANYWHERE_API_TOKEN"]
USERNAME = "L1ksius"
DOMAIN = "l1ksius.pythonanywhere.com"
BASE = Path(__file__).resolve().parent.parent
FILES = [
    BASE / "rotations/models.py",
    BASE / "rotations/migrations/0004_injuryassessment_snapshot_fields.py",
    BASE / "rotations/management/commands/seed_demo.py",
    BASE / "rotations/templates/rotations/player_detail.html",
]


def api(method: str, path: str, data: dict | None = None, raw: bytes | None = None, content_type: str | None = None):
    headers = {"Authorization": f"Token {TOKEN}"}
    body = raw
    if data is not None:
        body = urllib.parse.urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if content_type:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(
        f"https://www.pythonanywhere.com{path}",
        data=body,
        method=method,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


import urllib.parse  # noqa: E402


def upload(relative_path: str, content: bytes) -> None:
    remote = f"/home/{USERNAME}/apl-injury-risk/{relative_path.replace(chr(92), '/')}"
    boundary = "----uploadboundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="content"; filename="{Path(relative_path).name}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    status, payload = api(
        "POST",
        f"/api/v0/user/{USERNAME}/files/path{remote}",
        raw=body,
        content_type=f"multipart/form-data; boundary={boundary}",
    )
    print("upload", relative_path, status, payload[:120])


def run_setup_task() -> None:
    command = (
        "bash -lc 'source ~/.virtualenvs/apl-risk/bin/activate && "
        "cd ~/apl-injury-risk && python manage.py migrate --noinput && "
        "python manage.py seed_demo && echo DONE > ~/deploy_done.txt'"
    )
    status, payload = api(
        "POST",
        f"/api/v0/user/{USERNAME}/always_on/",
        data={"command": command, "description": "apl deploy setup", "enabled": "true"},
    )
    print("always_on create", status, payload.decode())
    if status not in (200, 201):
        return

    task_id = json.loads(payload.decode())["id"]
    for _ in range(40):
        time.sleep(5)
        status, payload = api("GET", f"/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/deploy_done.txt")
        if status == 200:
            print("setup finished")
            break
    api("DELETE", f"/api/v0/user/{USERNAME}/always_on/{task_id}/")
    api("DELETE", f"/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/deploy_done.txt")
    api("POST", f"/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/")


def main() -> None:
    for path in FILES:
        upload(path.relative_to(BASE).as_posix(), path.read_bytes())
    run_setup_task()
    print("https://l1ksius.pythonanywhere.com/")


if __name__ == "__main__":
    main()
