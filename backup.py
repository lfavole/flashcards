"""Back up the flashcards and send them by email."""

import datetime as dt
import os
import os.path
import smtplib
import sys
import tempfile
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from pytz import timezone

from progress import Progress
from utils import CollectionWrapper


def send_email_with_attachment(  # noqa: PLR0913, PLR0917
    sender_email: str,
    sender_password: str,
    recipient_email: str,
    subject: str,
    body: str,
    attachment_path: Path,
) -> None:
    """Send an email with an attachment."""
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(attachment_path.read_bytes())
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", f"attachment; filename={attachment_path.name}")
    msg.attach(attachment)

    with smtplib.SMTP_SSL(os.getenv("SMTP_SERVER", ""), int(os.getenv("SMTP_PORT", "465"))) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)


wrapper = CollectionWrapper()
if "--no-sync" not in sys.argv:
    with Progress("Syncing"):
        wrapper.sync()

with tempfile.TemporaryDirectory() as export_dir:
    with Progress("Exporting all the collection"):
        output_file = wrapper.export(None, export_dir, full_backup=True)

    now = dt.datetime.now().astimezone(timezone("Europe/Paris"))
    date = now.strftime("%d/%m/%Y %H:%M:%S")
    date_filename = now.strftime("%Y-%m-%d_%H-%M-%S")
    output_file = output_file.rename(output_file.parent / f"export_{date_filename}.apkg")

    with Progress("Sending email"):
        send_email_with_attachment(
            os.environ.get("ANKIWEB_EMAIL", ""),
            os.environ.get("EMAIL_PASSWORD", ""),
            os.environ.get("ANKIWEB_EMAIL", ""),
            f"Flashcards backup {date}",
            f"""\
The flashcards backup for {date} is attached.

When importing the file, remember to check:
- Import any learning progress
- Import any deck presets
""",
            output_file,
        )
