"""Upload full site update to PythonAnywhere."""
import os
import urllib.error
import urllib.request
from pathlib import Path

TOKEN = os.environ["PYTHONANYWHERE_API_TOKEN"]
USERNAME = "L1ksius"
DOMAIN = "l1ksius.pythonanywhere.com"
BASE = Path(__file__).resolve().parent.parent

UPLOADS = [
    "apl_risk/settings.py",
    "rotations/models.py",
    "rotations/risk_engine.py",
    "rotations/analytics.py",
    "rotations/admin.py",
    "rotations/forms.py",
    "rotations/views.py",
    "rotations/urls.py",
    "rotations/services/__init__.py",
    "rotations/services/transfermarkt_sync.py",
    "rotations/management/commands/sync_transfermarkt_injuries.py",
    "rotations/management/commands/sync_apl_data.py",
    "rotations/migrations/0007_player_transfermarkt_id_and_more.py",
    "rotations/management/commands/seed_demo.py",
    "rotations/static/rotations/site.css",
    "staticfiles/rotations/site.css",
    "rotations/templates/rotations/base.html",
    "rotations/templates/rotations/dashboard.html",
    "rotations/templates/rotations/player_detail.html",
    "rotations/templates/rotations/player_list.html",
    "rotations/templates/rotations/form.html",
    "README.md",
]


def upload(relative_path: str, content: bytes) -> None:
    remote = f"/home/{USERNAME}/apl-injury-risk/{relative_path.replace(chr(92), '/')}"
    boundary = "----uploadboundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="content"; filename="{Path(relative_path).name}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    request = urllib.request.Request(
        f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote}",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Token {TOKEN}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        print("upload", relative_path, response.status)


def upload_db() -> None:
    content = (BASE / "db.sqlite3").read_bytes()
    remote = f"/home/{USERNAME}/apl-injury-risk/db.sqlite3"
    boundary = "----dbboundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="content"; filename="db.sqlite3"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    request = urllib.request.Request(
        f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote}",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Token {TOKEN}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        print("db upload", response.status)


def reload() -> None:
    request = urllib.request.Request(
        f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/",
        data=b"",
        method="POST",
        headers={"Authorization": f"Token {TOKEN}"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        print("reload", response.read().decode())


def main() -> None:
    for path in UPLOADS:
        file_path = BASE / path
        if file_path.is_file():
            upload(path, file_path.read_bytes())
    upload_db()
    reload()
    print(f"https://{DOMAIN}/")


if __name__ == "__main__":
    main()
