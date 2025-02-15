"""Utility functions to manage Anki flashcards."""

import datetime as dt
import os
import random
import re
import sys
import threading
import time
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import TypeVar

from anki.collection import Collection, DeckIdLimit, ExportAnkiPackageOptions
from anki.decks import DeckNameId
from anki.errors import SyncError
from pytz import timezone


def sanitize_filename(filename: str) -> str:
    """Sanitizes a string so it could be used as part of a filename."""
    for char in '\\/:*?"<>|':
        filename = filename.replace(char, "_")
    return filename


def format_size(size: float) -> str:
    """Return a human formatted file size."""
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(size) < 1024:  # noqa: PLR2004
            return f"{size:3.1f} {unit}o"
        size /= 1024
    return f"{size:.1f} Yo"


def format_datetime(date: dt.datetime | None) -> str:
    """Return a human formatted date and time."""
    return "-" if not date else date.astimezone(timezone("Europe/Paris")).strftime("%d/%m/%Y %H:%M:%S")


def format_number(number: int) -> str:
    """Return a human formatted number."""
    return re.sub(r"(\d\d\d)", r"\1 ", str(number)[::-1])[::-1]


FunctionT = TypeVar("FunctionT", bound=Callable)


def run_in_thread(func: FunctionT) -> FunctionT:
    """Run a function in a thread."""

    @wraps(func)
    def decorator(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        val = None

        def thread_func(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            nonlocal val
            val = func(*args, **kwargs)

        thread = threading.Thread(target=thread_func, args=args, kwargs=kwargs)

        exc: BaseException | None = None

        def invoke_excepthook(_thread: threading.Thread) -> None:
            nonlocal exc
            exc = sys.exc_info()[1]

        thread._invoke_excepthook = invoke_excepthook  # noqa: SLF001
        thread.start()
        thread.join()
        if exc:
            raise exc
        return val

    return decorator


collection_dir = Path(__file__).parent / "collection"
collection_dir.mkdir(exist_ok=True)


class CollectionWrapper:
    """A wrapper to use `anki.collection.Collection`."""

    @run_in_thread
    def __init__(
        self,
        file: Path = collection_dir / "collection.anki2",
        email: str = os.environ.get("ANKIWEB_EMAIL", ""),
        password: str = os.environ.get("ANKIWEB_PASSWORD", ""),
    ) -> None:
        """Create a `Collection`."""
        self.col = Collection(str(Path(file).absolute()))
        self.email = email
        self.password = password

    @run_in_thread
    def sync(self) -> None:
        """
        Sync the flashcards.

        Raises:
            ValueError: if the email or password is not provided.
            SyncError: if an error occurs during sync.

        """
        if not self.email and not self.password:
            msg = "Username and password not provided"
            raise ValueError(msg)
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

        # Retry if multiple programs are connecting to the same account in the same time
        while True:
            try:
                auth = self.col.sync_login(self.email, self.password, endpoint=endpoint)
                self.col.full_upload_or_download(
                    auth=auth, server_usn=getattr(output, "server_media_usn", None), upload=False
                )
            except SyncError as err:
                if "try again" in str(err).lower():
                    seconds = random.randint(0, 30)  # noqa: S311
                    print(f"{type(err).__name__}: {err}")
                    print(f"Too many connections, retrying in {seconds} seconds...")
                    time.sleep(seconds)
                    continue
                raise
            break

    def all_decks(self) -> list[DeckNameId | None]:
        """Return all the available decks (only name and ID)."""
        return [
            None,
            *run_in_thread(self.col.decks.all_names_and_ids)(skip_empty_default=True, include_filtered=False),
        ]

    def has_children(self, deck: DeckNameId) -> bool:
        """Return `True` if the deck has children decks."""
        return bool(run_in_thread(self.col.decks.children)(deck.id))

    def is_child(self, deck: DeckNameId) -> bool:
        """Return `True` if the deck is a child deck."""
        return bool(run_in_thread(self.col.decks.parents)(deck.id))

    @run_in_thread
    def modtime(self, deck: DeckNameId | None) -> dt.datetime | None:
        """Return the modification time of the deck."""
        ret = (
            self.col.db.scalar(
                "select mod from cards where did = ? or odid = ? order by mod desc limit 1", deck.id, deck.id
            )
            if deck
            else self.col.db.scalar("select mod from cards order by mod desc limit 1")
        )
        ret = dt.datetime.fromtimestamp(ret, dt.UTC) if ret else None
        rets: list[dt.datetime | None] = [ret]
        # recursively check for the largest modification time
        if deck and self.has_children(deck):
            rets.extend(
                self.modtime(DeckNameId(name=child[0], id=child[1]))
                for child in run_in_thread(self.col.decks.children)(deck.id)
            )

        rets2: list[dt.datetime] = [ret for ret in rets if ret]
        if not rets2:
            return None
        return max(rets2)

    @run_in_thread
    def card_count(self, deck: DeckNameId | None) -> int:
        """Return the number of cards in the deck."""
        return (
            self.col.decks.card_count(deck.id, include_subdecks=True)
            if deck
            else self.col.db.scalar("select count() from cards")
        )

    @staticmethod
    def get_export_file(deck: DeckNameId | None, output_dir: str | Path) -> Path:
        """Return the path where the deck will be been exported."""
        filename = sanitize_filename(deck.name) if deck else "all"
        return Path(output_dir) / f"{filename}.apkg"

    def export(self, deck: DeckNameId | None, output_dir: str | Path) -> Path:
        """Export a deck in a directory. Return the path where the deck has been exported."""
        output = self.get_export_file(deck, output_dir)

        limit = DeckIdLimit(deck.id) if deck else None
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
