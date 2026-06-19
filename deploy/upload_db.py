import os
import urllib.error
import urllib.request
from pathlib import Path

TOKEN = os.environ["PYTHONANYWHERE_API_TOKEN"]
REMOTE = "/home/L1ksius/apl-injury-risk/db.sqlite3"
CONTENT = Path(__file__).resolve().parent.parent.joinpath("db.sqlite3").read_bytes()
boundary = "----dbboundary"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="content"; filename="db.sqlite3"\r\n'
    f"Content-Type: application/octet-stream\r\n\r\n"
).encode("utf-8") + CONTENT + f"\r\n--{boundary}--\r\n".encode("utf-8")

request = urllib.request.Request(
    f"https://www.pythonanywhere.com/api/v0/user/L1ksius/files/path{REMOTE}",
    data=body,
    method="POST",
    headers={
        "Authorization": f"Token {TOKEN}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    },
)
try:
    with urllib.request.urlopen(request, timeout=180) as response:
        print("db upload", response.status)
except urllib.error.HTTPError as exc:
    print("err", exc.code, exc.read()[:300])

reload_req = urllib.request.Request(
    "https://www.pythonanywhere.com/api/v0/user/L1ksius/webapps/l1ksius.pythonanywhere.com/reload/",
    data=b"",
    method="POST",
    headers={"Authorization": f"Token {TOKEN}"},
)
with urllib.request.urlopen(reload_req, timeout=60) as response:
    print("reload", response.status, response.read().decode())
