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
from pytz import timezone


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


def format_datetime(date: dt.datetime | None):
    """Return a human formatted date and time."""
    return "-" if not date else date.astimezone(timezone("Europe/Paris")).strftime("%d/%m/%Y %H:%M:%S")


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

        exc: BaseException | None = None

        def invoke_excepthook(_thread):
            nonlocal exc
            exc = sys.exc_info()[1]

        thread._invoke_excepthook = invoke_excepthook  # type: ignore
        thread.start()
        thread.join()
        if exc:
            raise exc  # pylint: disable=E0702  # type: ignore
        return val

    return decorator  # type: ignore


collection_dir = Path(__file__).parent / "collection"
collection_dir.mkdir(exist_ok=True)


class CollectionWrapper:
    """A wrapper to use `anki.collection.Collection`."""

    @run_in_thread
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

    def all_decks(self) -> list[DeckNameId | None]:
        """Returns all the available decks (only name and ID)."""
        return [
            None,
            *run_in_thread(self.col.decks.all_names_and_ids)(skip_empty_default=True, include_filtered=False),
        ]

    def has_children(self, deck: DeckNameId):
        """Return `True` if the deck has children decks."""
        return bool(run_in_thread(self.col.decks.children)(deck.id))  # type: ignore

    def is_child(self, deck: DeckNameId):
        """Return `True` if the deck is a child deck."""
        return bool(run_in_thread(self.col.decks.parents)(deck.id))  # type: ignore

    @run_in_thread
    def modtime(self, deck: DeckNameId | None):
        """The modification time of the deck."""
        ret = (
            self.col.db.scalar(
                "select mod from cards where did = ? or odid = ? order by mod desc limit 1", deck.id, deck.id
            )
            if deck
            else self.col.db.scalar("select mod from cards order by mod desc limit 1")
        )
        ret = dt.datetime.fromtimestamp(ret, dt.timezone.utc) if ret else None
        rets: list[dt.datetime | None] = [ret]
        # recursively check for the largest modification time
        if deck and self.has_children(deck):
            for child in run_in_thread(self.col.decks.children)(deck.id):  # pylint: disable=E1133
                rets.append(self.modtime(DeckNameId(name=child[0], id=child[1])))

        rets2: list[dt.datetime] = [ret for ret in rets if ret]
        if not rets2:
            return None
        return max(rets2)

    @run_in_thread
    def card_count(self, deck: DeckNameId | None):
        """The number of cards in the deck."""
        return (
            self.col.decks.card_count(deck.id, include_subdecks=True)
            if deck
            else self.col.db.scalar("select count() from cards")
        )

    def export(self, deck: DeckNameId | None, output_dir):
        """Export a deck in a directory."""
        filename = sanitize_filename(deck.name) if deck else "all"
        output = Path(output_dir) / f"{filename}.apkg"

        limit = DeckIdLimit(deck.id) if deck else None  # type: ignore
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
