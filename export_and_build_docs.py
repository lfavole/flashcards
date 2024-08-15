import datetime as dt
import os.path
import re
import shutil
from pathlib import Path
from urllib.parse import urljoin

from progress import Progress
from utils import CollectionWrapper, format_datetime, format_number, format_size


def link(target: Path, source: Path):
    """Return a link pointing to `target` that can be put in the `source` file."""
    return target.relative_to(
        source.parent if source.suffix == ".md" else source, walk_up=True  # type: ignore
    ).as_posix()


wrapper = CollectionWrapper()
with Progress("Syncing"):
    wrapper.sync()

with Progress("Cleaning up"):
    docs_dir = Path(__file__).parent / "docs/export"
    if docs_dir.exists():
        shutil.rmtree(docs_dir)
    docs_dir.mkdir(exist_ok=True)

    # remove the exported files
    export_dir = docs_dir.parent
    for file in export_dir.iterdir():
        if file.suffix == ".apkg":
            file.unlink()

    list_file = docs_dir / ".flashcards.md"
    list_file.touch(exist_ok=True)

TEMPLATE = """\
| Titre { aria-sort="ascending" } | Aperçu | Taille | Nombre de cartes | Dernière modification |
| ------------------------------- | ------ | ------ | ---------------- | --------------------- |
"""
FLASHCARDS_VIEWER = "https://lfavole.github.io/flashcards-viewer/"
BASE_URL = os.getenv("BASE_URL", "https://lfavole.github.io/flashcards/")

files: dict[Path, str] = {}

GLOBAL_METADATA = ""
GLOBAL_CONTENT = """\
Pour utiliser mes flashcards, vous devez auparavant
installer [Anki][anki]{:target="_blank"} puis importer le fichier que vous aurez téléchargé.

Sur les iPhones, **l'application est payante** : vous devez donc installer
[Anki][anki]{:target="_blank"} sur un autre appareil,
créer un compte [AnkiWeb][ankiweb_signup]{:target="_blank"},
l'associer à votre appareil et réviser depuis [AnkiWeb][ankiweb]{:target="_blank"}.

[anki]: https://apps.ankiweb.net/#download
[ankiweb_signup]: https://ankiweb.net/account/signup
[ankiweb]: https://ankiweb.net
"""

HOMEPAGE_METADATA = """\
---
icon: material/download
---
"""
HOMEPAGE_TITLE = "Télécharger mes flashcards"
HOMEPAGE_CONTENT = GLOBAL_CONTENT

sizes: dict[Path, int] = {}


# sort the decks so the parent deck appears before the child deck
for deck in sorted(wrapper.all_decks(), key=lambda deck: deck.name if deck else ""):  # pylint: disable=E1133
    with Progress(f"Exporting {deck.name} ({deck.id})" if deck else "Exporting all the collection"):
        output_file = wrapper.export(deck, export_dir)
    sizes[output_file] = os.path.getsize(docs_dir / output_file)
    size = format_size(sizes[output_file])

    card_count = format_number(wrapper.card_count(deck))
    modtime = format_datetime(wrapper.modtime(deck))  # pylint: disable=C0103
    parts = deck.name.split("::") if deck else ""

    # file that will contain the link to the deck
    # (page of the parent deck)
    filename = docs_dir.joinpath(*parts[:-1], "index.md")  # pylint: disable=C0103
    folder_icon = ""  # pylint: disable=C0103

    if not deck or wrapper.has_children(deck):
        # if the deck has children:
        # - add a link to the deck page (that lists the subdecks) with a folder icon
        # - create the deck page
        new_filename = docs_dir.joinpath(*parts, "index.md")  # file to be linked (deck page)
        output_url = link(new_filename, filename)
        folder_icon = ":material-folder: "  # pylint: disable=C0103
        # create the deck page
        files[
            new_filename
        ] = f"""\
{HOMEPAGE_METADATA if not deck else GLOBAL_METADATA}
# {deck.name if deck else HOMEPAGE_TITLE}

{HOMEPAGE_CONTENT if not deck else GLOBAL_CONTENT}

[:material-download: Télécharger toutes les flashcards]({link(output_file, new_filename)}) ({size}) \
[Aperçu]({FLASHCARDS_VIEWER}#{urljoin(BASE_URL, link(output_file, new_filename))}) {{ target=\"_blank\" }} (1)
{{ .annotate }}

1. {"Dernière modification : " + modtime + "  \n" if modtime != "-" else ""}\
   Nombre de cartes : {card_count}

{TEMPLATE}"""

    else:
        output_url = link(output_file, filename)

    if deck:
        # add a link to the deck / deck page
        # (not for all the collection)
        files[
            filename
        ] += f"| \
[{folder_icon}{parts[-1]}]({output_url}) | \
[Aperçu]({FLASHCARDS_VIEWER}#{urljoin(BASE_URL, output_url)}) {{ target=\"_blank\" }} | \
{size} | \
{card_count} | \
{modtime}\n"


for filename, content in files.items():
    with Progress(f"Writing {filename}"):
        file = docs_dir / filename
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")

with Progress("Adding last change date"):
    mkdocs_yml = Path(__file__).parent / "mkdocs.yml"
    data = mkdocs_yml.read_text("utf-8")
    now = dt.datetime.now(dt.timezone.utc)
    last_change = f'copyright: "Dernière mise à jour : {format_datetime(now)}"\n'
    if "copyright" not in data:
        data += "\n" + last_change
    else:
        data = re.sub(r"copyright: .*\n", last_change, data)
    mkdocs_yml.write_text(data, "utf-8")
