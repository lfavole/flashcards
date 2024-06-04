import datetime as dt
import os
import re
import sys
import threading
from functools import wraps
from pathlib import Path
from typing import Callable, TypeVar

from anki.collection import Collection, DeckIdLimit, ExportAnkiPackageOptions
from anki.decks import DeckNameId


def sanitize_filename(filename: str):
    """Sanitizes a string so it could be used as part of a filename."""
    for char in '\\/:*?"<>|':
        filename = filename.replace(char, "_")
    return filename


def format_size(size):
    """Return a human formatted file size"""
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(size) < 1024:
            return f"{size:3.1f} {unit}o"
        size /= 1024
    return f"{size:.1f} Yo"


def format_date(date: dt.date | None):
    """Return a human formatted date."""
    return "-" if not date else date.strftime("%d/%m/%Y %H:%M:%S")


def format_number(number: int):
    """Return a human formatted number."""
    return re.sub(r"(\d\d\d)", r"\1 ", str(number)[::-1])[::-1]


FunctionT = TypeVar("FunctionT", bound=Callable)


def run_in_thread(func: FunctionT) -> FunctionT:
    """Run a function in a thread"""

    @wraps(func)
    def decorator(*args, **kwargs):
        val = None

        def thread_func(*args, **kwargs):
            nonlocal val
            val = func(*args, **kwargs)

        thread = threading.Thread(target=thread_func, args=args, kwargs=kwargs)
        thread.start()
        thread.join()
        return val

    return decorator  # type: ignore


collection_dir = Path(__file__).parent / "collection"
collection_dir.mkdir(exist_ok=True)


class CollectionWrapper:
    """A wrapper to use `anki.collection.Collection`."""

    def __init__(
        self,
        file=collection_dir / "collection.anki2",
        email=os.environ.get("ANKIWEB_EMAIL", ""),
        password=os.environ.get("ANKIWEB_PASSWORD", ""),
    ):
        self.col = Collection(str(Path(file).absolute()))
        self.email = email
        self.password = password

    @run_in_thread
    def sync(self):
        """Sync the flashcards."""
        if not self.email and not self.password:
            raise ValueError("Username and password not provided")
        endpoint = None
        auth = self.col.sync_login(self.email, self.password, endpoint=endpoint)
        output = self.col.sync_collection(auth, True)
        status = self.col.sync_status(auth)

        # https://github.com/ankitects/anki/blob/a515463/qt/aqt/sync.py#L93
        if output.new_endpoint:
            endpoint = output.new_endpoint

        if output.server_message:
            print(output.server_message, file=sys.stderr)
            return

        if status.required == status.NO_CHANGES:
            return

        auth = self.col.sync_login(self.email, self.password, endpoint=endpoint)
        self.col.full_upload_or_download(auth=auth, server_usn=getattr(output, "server_media_usn", None), upload=False)

    def all_decks(self):
        """Returns all the available decks (only name and ID)."""
        return run_in_thread(self.col.decks.all_names_and_ids)(skip_empty_default=True, include_filtered=False)

    def has_children(self, deck: DeckNameId):
        """Return `True` if the deck has children decks."""
        return bool(run_in_thread(self.col.decks.children)(deck.id))  # type: ignore

    @run_in_thread
    def modtime(self, deck: DeckNameId):
        ret = self.col.db.execute("select mod from cards where did = ? order by mod desc limit 1", deck.id)
        if not ret:
            return None
        return dt.datetime.fromtimestamp(ret[0][0])

    @run_in_thread
    def card_count(self, deck: DeckNameId):
        return self.col.decks.card_count(deck.id, include_subdecks=True)

    def export(self, deck: DeckNameId | None, output_dir):
        """Export a deck in a directory."""
        filename = sanitize_filename(deck.name) if deck else "all"
        output = Path(output_dir) / f"{filename}.apkg"

        limit = DeckIdLimit(deck.id)  # type: ignore
        run_in_thread(self.col.export_anki_package)(
            out_path=str(output.absolute()),
            limit=limit,
            options=ExportAnkiPackageOptions(
                with_scheduling=False,
                with_deck_configs=False,
                with_media=True,
                legacy=True,
            ),
        )
        return output
