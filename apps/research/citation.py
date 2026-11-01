"""Formats de citation des publications (spec M3 : export BibTeX ; RIS et CSL-JSON à venir)."""

import unicodedata

from .models import Publication

Kind = Publication.Kind

BIBTEX_TYPES = {
    Kind.JOURNAL_ARTICLE: "article",
    Kind.CONFERENCE_PAPER: "inproceedings",
    Kind.BOOK_CHAPTER: "incollection",
    Kind.BOOK: "book",
    Kind.THESIS: "phdthesis",
    Kind.MASTER_THESIS: "mastersthesis",
    Kind.PREPRINT: "misc",
    Kind.REPORT: "techreport",
}
# Champ BibTeX qui reçoit la revue ou la conférence selon le type d'entrée.
VENUE_FIELDS = {
    "article": "journal",
    "inproceedings": "booktitle",
    "incollection": "booktitle",
    "techreport": "institution",
    "phdthesis": "school",
    "mastersthesis": "school",
    "misc": "howpublished",
    "book": "series",
}


def _ascii(text):
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if char.isascii() and char.isalnum())


def _escape(value):
    return str(value).replace("\\", "\\\\").replace("&", r"\&").replace("%", r"\%")


def authors(publication):
    return [authorship.name for authorship in publication.authorships.all()]


def bibtex_key(publication):
    names = authors(publication)
    last_name = _ascii(names[0].split()[-1]) if names else "daara"
    first_word = next((_ascii(word) for word in publication.title.split() if len(word) > 3), "")
    return f"{last_name.lower()}{publication.year or ''}{first_word.lower()}"


def bibtex(publication):
    entry_type = BIBTEX_TYPES[publication.kind]
    fields = [
        ("title", "{" + _escape(publication.title) + "}"),
        ("author", " and ".join(_escape(name) for name in authors(publication))),
        ("year", publication.year),
        (VENUE_FIELDS[entry_type], _escape(publication.venue)),
        ("publisher", _escape(publication.publisher)),
        ("volume", publication.volume),
        ("number", publication.issue),
        ("pages", publication.pages.replace("–", "--")),
        ("doi", publication.doi),
        ("url", "" if publication.doi else publication.url),
    ]
    lines = [f"@{entry_type}{{{bibtex_key(publication)},"]
    lines += [f"  {name} = {{{value}}}," for name, value in fields if value]
    lines.append("}")
    return "\n".join(lines) + "\n"


def reference(publication):
    """Référence lisible : Auteurs (Année). Titre. Revue, volume(numéro), pages. DOI."""
    names = authors(publication)
    if len(names) > 6:
        names = [*names[:6], "et al."]
    parts = [", ".join(names)]
    if publication.year:
        parts[0] += f" ({publication.year})"
    parts.append(publication.title.rstrip("."))
    venue = publication.venue
    if venue and publication.volume:
        venue += f", {publication.volume}"
        if publication.issue:
            venue += f"({publication.issue})"
    if venue and publication.pages:
        venue += f", {publication.pages}"
    if venue:
        parts.append(venue)
    text = ". ".join(part for part in parts if part) + "."
    if publication.doi:
        text += f" {publication.doi_url}"
    return text
