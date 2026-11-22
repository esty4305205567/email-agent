import base64
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# קריאה ויצירת טיוטות בלבד. אין בקוד שליחה של מיילים.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]


def get_service():
    creds = None
    if Path("token.json").exists():
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        Path("token.json").write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def _get_body(payload):
    if payload.get("mimeType") == "text/plain" and payload["body"].get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", "ignore")
    for part in payload.get("parts", []):
        text = _get_body(part)
        if text:
            return text
    return ""


def fetch_email(message_id: str) -> dict:
    service = get_service()
    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    headers = {h["name"].lower(): h["value"] for h in msg["payload"]["headers"]}
    return {
        "id": msg["id"],
        "thread_id": msg["threadId"],
        "from": headers.get("from", ""),
        "subject": headers.get("subject", ""),
        "body": _get_body(msg["payload"]),
        "message_id_header": headers.get("message-id", ""),
    }


def list_unread(max_results: int = 5) -> list[str]:
    service = get_service()
    res = service.users().messages().list(
        userId="me", q="is:unread in:inbox", maxResults=max_results
    ).execute()
    return [m["id"] for m in res.get("messages", [])]


def create_draft(email: dict, reply_text: str) -> str:
    service = get_service()
    msg = EmailMessage()
    msg.set_content(reply_text)
    msg["To"] = email["from"]
    msg["Subject"] = "Re: " + email["subject"].removeprefix("Re: ")
    msg["In-Reply-To"] = email["message_id_header"]
    msg["References"] = email["message_id_header"]
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw, "threadId": email["thread_id"]}},
    ).execute()
    return draft["id"]
