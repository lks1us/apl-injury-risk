import urllib.error
import urllib.request
from pathlib import Path

TOKEN = __import__("os").environ["PYTHONANYWHERE_API_TOKEN"]
WSGI_PATH = "/var/www/l1ksius_pythonanywhere_com_wsgi.py"
CONTENT = Path(__file__).with_name("wsgi_upload.py").read_bytes()
boundary = "----aplboundary"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="content"; filename="wsgi.py"\r\n'
    f"Content-Type: text/plain\r\n\r\n"
).encode("utf-8") + CONTENT + f"\r\n--{boundary}--\r\n".encode("utf-8")

request = urllib.request.Request(
    f"https://www.pythonanywhere.com/api/v0/user/L1ksius/files/path{WSGI_PATH}",
    data=body,
    method="POST",
    headers={
        "Authorization": f"Token {TOKEN}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    },
)
try:
    with urllib.request.urlopen(request, timeout=60) as response:
        print(response.status, response.read().decode())
except urllib.error.HTTPError as exc:
    print(exc.code, exc.read().decode())
