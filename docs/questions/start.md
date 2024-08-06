# Introduction

## Que dois-je faire quoi sur ce site ? { id="start" }

1. [Installez l'application Anki](anki/index.md#download).
2. [Téléchargez des paquets de cartes qui vous intéressent](#download-decks).
3. [Importez-les](anki/importing.md#import).

## Comment télécharge-t-on des paquets de cartes sur ce site ? { id="download-decks" }

Sur chacune des pages, vous avez un tableau indiquant tous les [paquets de cartes](anki/concepts.md#decks) disponibles. Cliquez sur un des liens dans la première colonne du tableau pour télécharger les flashcards en question.

## Pourquoi y a-t-il une icône de dossier :material-folder: à gauche de certains paquets de cartes ? { id="folder-icon" }

J'organise les paquets de cartes en [dossiers :material-folder:](anki/concepts.md#folders) pour mieux m'y retrouver lors de mes révisions. Les liens précédés d'une icône de dossier :material-folder: pointent donc vers une page indiquant tous les paquets de cartes de ce dossier.

## Comment dois-je faire pour télécharger un dossier ? { id="download-folder" }

Vous pouvez télécharger un dossier entier en utilisant le lien "Télécharger toutes les flashcards" sur sa page dédiée.

## Quelle est la différence entre le lien "Télécharger toutes les flashcards" et les liens présents dans le tableau ? { id="download-all-flashcards" }

Le lien "Télécharger toutes les flashcards" permet de télécharger toutes les flashcards du dossier, c'est-à-dire toutes celles qui sont présentes dans le tableau en-dessous. Importer ce fichier revient au même que d'importer tous les fichiers présents dans le tableau.

## Pourquoi certains fichiers sont-ils plus lourds que d'autres ? { id="filesize" }

Si un fichier contient plus de cartes ou d'images, alors il sera nécessairement plus lourd.

## Comment as-tu créé ce site ? { id="creating" }

J'ai utilisé [l'API (interface de programmation) Python d'Anki](https://addon-docs.ankiweb.net/the-anki-module.html) pour [exporter les paquets de cartes](https://github.com/ankitects/anki/blob/e0de13e/pylib/anki/collection.py#L366) un par un. [Voici le code source que j'utilise](https://github.com/lfavole/flashcards/blob/main/export_and_build_docs.py).

## Ce site est-il open source ? { id="opensource" }

Oui, vous pouvez trouver le code source [sur GitHub](https://github.com/lfavole/flashcards){ target="_blank" }. (Sachez qu'un lien :fontawesome-brands-github: est disponible en haut à droite de chaque page ou dans le menu sur les téléphones)

## Quel thème as-tu utilisé ? { id="theme" }

J'ai utilisé [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/), qui sert normalement à générer des documentations techniques. (Sachez que c'est marqué en bas de chaque page)

## Ce site est-il mis à jour régulièrement ? { id="updating" }

Oui, le site se met à jour [automatiquement](#cron) toutes les 3 heures. (Sachez que c'est marqué en bas de chaque page)

## Comment s'effectue l'actualisation du site ? { id="cron" }

Grâce à une [tâche cron sur GitHub](https://docs.github.com/fr/actions/using-workflows/events-that-trigger-workflows#schedule) : [voici le code que j'utilise](https://github.com/lfavole/flashcards/actions/workflows/build.yml).
