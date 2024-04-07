import datetime as dt
import os.path
import re
import shutil
from pathlib import Path

from progress import Progress
from utils import CollectionWrapper, format_size


def link(target: Path, source: Path, remove_index=False):
    """Return a link pointing to `target` that can be put in the `source` file."""
    ret = target.relative_to(
        source.parent if source.suffix == ".md" else source, walk_up=True  # type: ignore
    ).as_posix()
    if remove_index:
        ret = ret.removesuffix("index.md")
    return ret


wrapper = CollectionWrapper()
with Progress("Syncing"):
    wrapper.sync()

with Progress("Cleaning up"):
    docs_dir = Path(__file__).parent / "docs"
    if docs_dir.exists():
        shutil.rmtree(docs_dir)
    docs_dir.mkdir(exist_ok=True)

    export_dir = docs_dir

    list_file = docs_dir / ".flashcards.md"
    list_file.touch(exist_ok=True)

TEMPLATE = """\
| Titre | Taille |
| ----- | ------ |
"""

files: dict[Path, str] = {}
files[docs_dir / "index.md"] = "# Mes flashcards\n\n" + TEMPLATE

sizes: dict[Path, int] = {}
written = []  # parent decks that have already been written

for deck in wrapper.all_decks():  # pylint: disable=E1133
    with Progress(f"Exporting {deck.name} ({deck.id})"):
        output_file = wrapper.export(deck, export_dir)
    sizes[output_file] = os.path.getsize(docs_dir / output_file)
    parts = deck.name.split("::")

    # file that will contain the link to the deck
    filename = docs_dir / "/".join([*parts[:-1], "index.md"])  # pylint: disable=C0103
    if not wrapper.has_children(deck):
        # if the deck has children, the first child will add a link
        output_url = link(output_file, filename)
        files[filename] += f"| [{deck.name}]({output_url}) | {format_size(sizes[output_file])} |\n"

    if wrapper.has_children(deck):
        old_filename = filename  # file in which the link is added
        new_filename = docs_dir / "/".join([*parts, "index.md"])  # file to be linked (index page of the deck)

        files[
            old_filename
        ] += f"| \
[:material-folder: {deck.name}]({link(new_filename, old_filename, remove_index=True)}) | \
{format_size(sizes[output_file])} |\n"

        files[
            new_filename
        ] = f"""\
# {deck.name}

[:material-download: Télécharger toutes les flashcards]({link(output_file, new_filename)})

{TEMPLATE}"""

for filename, content in files.items():
    with Progress(f"Writing {filename}"):
        file = docs_dir / filename
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")

with Progress("Adding last change date"):
    mkdocs_yml = Path(__file__).parent / "mkdocs.yml"
    data = mkdocs_yml.read_text("utf-8")
    last_change = f'copyright: "Dernière mise à jour : {dt.datetime.now()}"\n'
    if "copyright" not in data:
        data += "\n" + last_change
    else:
        data = re.sub(r"copyright: .*\n", last_change, data)
    mkdocs_yml.write_text(data, "utf-8")
