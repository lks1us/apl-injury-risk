"""Upload changed template files to PythonAnywhere."""
import os
import urllib.error
import urllib.request
from pathlib import Path

TOKEN = os.environ["PYTHONANYWHERE_API_TOKEN"]
USERNAME = "L1ksius"
BASE = Path(__file__).resolve().parent.parent
FILES = [
    BASE / "rotations/templates/rotations/base.html",
    BASE / "rotations/templates/rotations/player_detail.html",
]


def upload(relative_path: str, content: bytes) -> None:
    remote = f"/home/{USERNAME}/apl-injury-risk/{relative_path.replace(chr(92), '/')}"
    boundary = "----uploadboundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="content"; filename="{Path(relative_path).name}"\r\n'
        f"Content-Type: text/html\r\n\r\n"
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
    with urllib.request.urlopen(request, timeout=60) as response:
        print(relative_path, response.status)


def reload() -> None:
    request = urllib.request.Request(
        f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/l1ksius.pythonanywhere.com/reload/",
        data=b"",
        method="POST",
        headers={"Authorization": f"Token {TOKEN}"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        print("reload", response.status, response.read().decode())


def main() -> None:
    for path in FILES:
        relative = path.relative_to(BASE).as_posix()
        upload(relative, path.read_bytes())
    reload()


if __name__ == "__main__":
    main()
