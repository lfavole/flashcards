"""Check if there are due cards. If it's the case, send a Telegram message."""

import json
import os
import sys
from urllib.request import Request, urlopen

from progress import Progress
from utils import CollectionWrapper


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> None:
    """
    Send a message to a Telegram chat.

    Args:
        bot_token (str): Token of the Telegram bot.
        chat_id (str): ID of the Telegram chat.
        message (str): The message to send.

    Raises:
        RuntimeError: if the call to the Telegram API fails.

    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        with urlopen(
            Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json"}, method="POST")
        ) as f:
            data = json.load(f)
    except Exception as e:
        print()
        print(e.fp.read())
        return
    if not data["ok"]:
        msg = f"Failed to send message: {data['description']}"
        raise RuntimeError(msg)


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
    send_telegram_message(os.getenv("TELEGRAM_BOT_TOKEN", ""), os.getenv("TELEGRAM_CHAT_ID", ""), message)
else:
    print("No flashcards to review")
