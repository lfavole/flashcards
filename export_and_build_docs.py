"""Export all the flashcards and build the documentation with mkdocs."""

import datetime as dt
import os.path
import shutil
import sys
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING
from urllib.parse import urljoin

import mkdocs.commands.build
import mkdocs.config

if TYPE_CHECKING:
    from anki.decks import DeckNameId

from progress import Progress
from utils import CollectionWrapper, collection_dir, format_datetime, format_number, format_size


def link(target: Path, source: Path) -> str:
    """Return a link pointing to `target` that can be put in the `source` file."""
    return target.relative_to(
        source.parent if source.suffix == ".md" else source,
        walk_up=True,
    ).as_posix()


wrapper = CollectionWrapper()
if "--no-sync" not in sys.argv:
    with Progress("Syncing"):
        wrapper.sync()

with Progress("Cleaning up"):
    docs_dir = Path(__file__).parent / "docs/export"
    if docs_dir.exists():
        shutil.rmtree(docs_dir)
    docs_dir.mkdir()

    media_dir = Path(__file__).parent / "docs/media"
    if media_dir.exists():
        shutil.rmtree(media_dir)
    media_dir.mkdir()

    # remove the exported files
    export_dir = docs_dir.parent
    for file in export_dir.iterdir():
        if file.suffix == ".apkg":
            file.unlink()

TEMPLATE = """\
| Titre { aria-sort="ascending" } | Aperçu | Taille | Nombre de cartes | Dernière modification |
| ------------------------------- | ------ | ------ | ---------------- | --------------------- |
"""
FLASHCARDS_VIEWER = "https://lfavole.github.io/flashcards-viewer/"
BASE_URL = os.getenv("BASE_URL", "https://lfavole.github.io/flashcards/")

files: dict[Path, str] = {}

GLOBAL_METADATA = ""
GLOBAL_CONTENT = """\
[Comment utiliser ce site ?](HELP)
"""

HOMEPAGE_METADATA = """\
---
icon: material/download
---
"""
HOMEPAGE_TITLE = "Télécharger mes flashcards"
HOMEPAGE_CONTENT = GLOBAL_CONTENT

sizes: dict[Path, int] = {}

threads: list[Thread] = []


def export_deck(deck: "DeckNameId") -> None:
    """Export a deck and save its size."""
    with Progress(f"Exporting {deck.name} ({deck.id})" if deck else "Exporting all the collection"):
        wrapper.export(deck, export_dir)

    output_file = wrapper.get_export_file(deck, export_dir)
    sizes[output_file] = (docs_dir / output_file).stat().st_size


# sort the decks so the parent deck appears before the child deck
decks = sorted(wrapper.all_decks(), key=lambda deck: deck.name if deck else "")

for deck in decks:  # pylint: disable=E1133
    thread = Thread(target=export_deck, args=(deck,))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()


for deck in decks:  # pylint: disable=E1133
    output_file = wrapper.get_export_file(deck, export_dir)
    size = format_size(sizes[output_file])

    card_count = format_number(wrapper.card_count(deck))
    modtime = format_datetime(wrapper.modtime(deck))
    parts = deck.name.split("::") if deck else ""

    # file that will contain the link to the deck
    # (page of the parent deck)
    filename = docs_dir.joinpath(*parts[:-1], "index.md")
    folder_icon = ""

    if not deck or wrapper.has_children(deck):
        # if the deck has children:
        # - add a link to the deck page (that lists the subdecks) with a folder icon
        # - create the deck page
        new_filename = docs_dir.joinpath(*parts, "index.md")  # file to be linked (deck page)
        output_url = link(new_filename, filename)
        folder_icon = ":material-folder: "
        # create the deck page
        help_link = link(docs_dir.parent / "questions/start.md", new_filename)
        NEWLINE = "\n"
        files[new_filename] = f"""\
{HOMEPAGE_METADATA if not deck else GLOBAL_METADATA}
# {deck.name if deck else HOMEPAGE_TITLE}

{(HOMEPAGE_CONTENT if not deck else GLOBAL_CONTENT).replace("HELP", help_link)}

[Fichiers média manquants ? Cliquez ici]({link(media_dir / "index.md", new_filename)})

[:material-download: Télécharger toutes les flashcards]({link(output_file, new_filename)}) ({size}) - \
[Aperçu]({FLASHCARDS_VIEWER}#{urljoin(BASE_URL, link(output_file, docs_dir.parent))}){{ target=\"_blank\" }} (1)
{{ .annotate }}

1. {"Dernière modification : " + modtime + NEWLINE + "  " if modtime != "-" else ""}\
   Nombre de cartes : {card_count}

{TEMPLATE}"""

    else:
        output_url = link(output_file, filename)

    if deck:
        # add a link to the deck / deck page
        # (not for all the collection)
        files[filename] += f'| \
[{folder_icon}{parts[-1]}]({output_url}) | \
[Aperçu]({FLASHCARDS_VIEWER}#{urljoin(BASE_URL, link(output_file, docs_dir.parent))}){{ target="_blank" }} | \
{size} | \
{card_count} | \
{modtime}\n'

files[media_dir / "index.md"] = """\
# Fichiers média

Il peut vous arriver de rencontrer des erreurs "Impossible de trouver ...".

Dans ce cas, téléchargez le fichier manquant sur cette page
(clic droit / appui long → Enregistrer la cible du lien sous...)
et déplacez-le dans le dossier suivant :

- Sur Windows / macOS / Linux : <br> ouvrez Anki → *Outils* → *Vérifier les médias* → *Afficher les fichiers*
- Sur Android :
    - S'il existe : <br> Stockage interne → AnkiDroid → collection.media
    - Sinon (vous pourriez avoir besoin d'un ordinateur) : <br>
      Stockage interne / Carte SD → Android → data → com.ichi2.anki → collection.media

| Nom du fichier { aria-sort="ascending" } | Taille | Dernière modification |
| ---------------------------------------- | ------ | --------------------- |
"""

(docs_dir / "media").mkdir(parents=True, exist_ok=True)

for file in (collection_dir / "collection.media").iterdir():
    with Progress(f"Copying media file {file}"):
        shutil.copy(file, media_dir / file.name)
    mtime = dt.datetime.fromtimestamp(file.stat().st_mtime, tz=dt.UTC)
    files[media_dir / "index.md"] += f"""\
| [{file.name}]({file.name}) | {format_size(file.stat().st_size)} | {format_datetime(mtime)} |
"""


for filename, content in files.items():
    with Progress(f"Writing {filename}"):
        file = docs_dir / filename
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")

mkdocs_config = Path(__file__).parent / "mkdocs.yml"

with Progress("Building documentation"):
    now = dt.datetime.now(dt.UTC)
    last_change = f"Dernière mise à jour : {format_datetime(now)}"

    # Load the MkDocs configuration
    config = mkdocs.config.load_config(str(mkdocs_config))

    # Add the last change date
    config["copyright"] = (config["copyright"] + "\n" if config["copyright"] else "") + last_change

    # Change the output directory on GitLab
    if os.environ.get("GITLAB_CI"):
        config["site_dir"] = str(Path(__file__).parent / "public")

    # Build the documentation
    mkdocs.commands.build.build(config)
