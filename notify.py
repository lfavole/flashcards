"""Check if there are due cards. If it's the case, send a Telegram message."""

import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from progress import Progress
from utils import CollectionWrapper


def make_request(bot_token: str, method: str, params: dict) -> Any:  # noqa: ANN401
    """
    Make a request to the Telegram API.

    Raises:
        RuntimeError: if the call to the Telegram API fails.

    """
    with urlopen(
        Request(
            f"https://api.telegram.org/bot{bot_token}/{method}",
            json.dumps(params).encode(),
            {"Content-Type": "application/json"},
            method="POST",
        )
    ) as f:
        data = json.load(f)

    if not data["ok"]:
        msg = f"Failed to call Telegram API: {data['description']}"
        raise RuntimeError(msg)
    return data["result"]


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> None:
    """
    Send a message to a Telegram chat.

    Args:
        bot_token (str): Token of the Telegram bot.
        chat_id (str): ID of the Telegram chat.
        message (str): The message to send.

    """
    return make_request(bot_token, "sendMessage", {"chat_id": chat_id, "text": message})


def delete_telegram_message(bot_token: str, chat_id: str, message_id: str) -> None:
    """
    Delete a message in a Telegram chat.

    Args:
        bot_token (str): Token of the Telegram bot.
        chat_id (str): ID of the Telegram chat.
        message_id (str): The ID of the message to delete.

    """
    return make_request(bot_token, "deleteMessage", {"chat_id": chat_id, "message_id": message_id})


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

MESSAGE_ID_FILE = Path(__file__).parent / ".message_id"

if MESSAGE_ID_FILE.exists():
    message_id = MESSAGE_ID_FILE.read_text("utf-8").strip()
    if message_id:
        delete_telegram_message(BOT_TOKEN, CHAT_ID, message_id)
        MESSAGE_ID_FILE.unlink()

wrapper = CollectionWrapper()
if "--no-sync" not in sys.argv:
    with Progress("Syncing"):
        wrapper.sync()

counts = {
    "new": 0,
    "learn": 0,
    "review": 0,
}
for deck in wrapper.col.sched.deck_due_tree().children:
    counts["new"] += deck.new_count
    counts["learn"] += deck.learn_count
    counts["review"] += deck.review_count

if counts["new"] > 0 or counts["learn"] > 0 or counts["review"] > 0:
    message = (
        f"Review your flashcards today!\n"
        "\n"
        f"New cards: {counts['new']}\n"
        f"Learning cards: {counts['learn']}\n"
        f"Cards to review: {counts['review']}"
    )
    print(message)
    result = send_telegram_message(BOT_TOKEN, CHAT_ID, message)
    MESSAGE_ID_FILE.write_text(str(result["message_id"]), "utf-8")
else:
    print("No flashcards to review")
