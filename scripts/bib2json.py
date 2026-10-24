#!/usr/bin/env python3
"""Convert the .bib files in bib/ into assets/publications.json for Hugo.

No dependencies beyond the Python standard library. Run it before `hugo`:

    python3 scripts/bib2json.py && hugo server

Which section an entry lands in is decided by the file it is in and its type:
    ref_arxiv.bib    -> Preprints
    ref_conf.bib     -> Conference papers
    ref_journal.bib  -> @article: Journal articles, @book: Books, @patent: Patents
    ref_talks.bib    -> Talks
    site_only.bib    -> by type (@mastersthesis/@phdthesis: Theses)

Website-only fields (LaTeX ignores them): pdf, poster, slides, amazon,
worldcat, proquest, award. Add `website = {no}` to hide an entry.
Only entries with Anubhav Gupta as an author are published.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB_DIR = ROOT / "bib"
OUT = ROOT / "assets" / "publications.json"
ME = ("gupta", "anubhav")

SECTION_BY_FILE = {
    "ref_arxiv.bib": "preprint",
    "ref_conf.bib": "conference",
    "ref_talks.bib": "talk",
}
SECTION_BY_TYPE = {
    "article": "journal",
    "book": "book",
    "patent": "patent",
    "mastersthesis": "thesis",
    "phdthesis": "thesis",
    "inproceedings": "conference",
    "misc": "preprint",
}
# Label prefix for each section's numbering (J3, C9, P2, ...).
PREFIX = {"journal": "J", "conference": "C", "preprint": "P", "book": "B",
          "thesis": "Th", "patent": "P", "talk": "T", "other": "O"}
# Fields copied into the BibTeX block shown on each page (standard fields only).
CITE_FIELDS = ["title", "author", "booktitle", "journal", "school", "publisher",
               "address", "edition", "volume", "number", "pages", "year", "date",
               "type", "doi", "eprint", "archiveprefix", "primaryclass", "url", "note"]
MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()


# ---------------------------------------------------------------- parsing
def parse_bib(text):
    """Yield (entry_type, key, {field: raw_value}) from BibTeX text."""
    i, n = 0, len(text)
    while True:
        at = text.find("@", i)
        if at < 0:
            return
        m = re.match(r"@\s*(\w+)\s*\{\s*([^,\s]+)\s*,", text[at:])
        if not m:
            i = at + 1
            continue
        etype, key = m.group(1).lower(), m.group(2)
        if etype in ("comment", "string", "preamble"):
            i = at + 1
            continue
        j = at + m.end()
        fields = {}
        while j < n:
            while j < n and text[j] in " \t\r\n,":
                j += 1
            if j >= n or text[j] == "}":
                j += 1
                break
            fm = re.match(r"([\w+\-]+)\s*=\s*", text[j:])
            if not fm:  # malformed; skip to end of entry
                break
            name = fm.group(1).lower()
            j += fm.end()
            if text[j] == "{":
                depth, start = 0, j
                while j < n:
                    if text[j] == "{":
                        depth += 1
                    elif text[j] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                value = text[start + 1:j]
                j += 1
            elif text[j] == '"':
                end = text.index('"', j + 1)
                value, j = text[j + 1:end], end + 1
            else:
                vm = re.match(r"[^,}\s]+", text[j:])
                value, j = vm.group(0), j + vm.end()
            fields[name] = value.strip()
        yield etype, key, fields
        i = j


# ---------------------------------------------------------------- LaTeX to text
ACCENTS = {'"': "\u0308", "'": "\u0301", "`": "\u0300", "^": "\u0302",
           "~": "\u0303", "=": "\u0304", ".": "\u0307", "c": "\u0327",
           "v": "\u030c", "u": "\u0306", "H": "\u030b"}
SYMBOLS = {r"\&": "&", r"\%": "%", r"\$": "$", r"\_": "_", r"\#": "#",
           r"\o": "ø", r"\O": "Ø", r"\ss": "ß", r"\aa": "å", r"\AA": "Å",
           r"\l": "ł", r"\L": "Ł", r"\ae": "æ", r"\AE": "Æ", "~": "\u00a0"}


def latex_to_text(s):
    import unicodedata
    if not s:
        return ""
    # drop decorations used only in the CV
    s = re.sub(r"\\(?:color|textcolor)\{[^}]*\}", "", s)
    s = re.sub(r"\\FiveStar\b", "", s)
    # accents: \"o, \"{o}, {\"o}
    s = re.sub(r"\\([\"'`^~=.cvuH])\s*\{?(\w)\}?",
               lambda m: unicodedata.normalize("NFC", m.group(2) + ACCENTS[m.group(1)]), s)
    for k, v in SYMBOLS.items():
        s = s.replace(k, v)
    s = s.replace("---", "\u2014").replace("--", "\u2013")
    s = re.sub(r"\\\\", " ", s)
    # unwrap formatting commands, keep their argument
    s = re.sub(r"\\(?:textbf|textit|emph|textsc|mathrm|text)\s*", "", s)
    s = re.sub(r"\\[a-zA-Z]+\s*", "", s)  # any other command: drop
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- helpers
def split_authors(raw):
    names = [a.strip() for a in re.split(r"\s+and\s+", raw) if a.strip()]
    out = []
    for a in names:
        a = latex_to_text(a)
        if "," in a:
            last, first = [p.strip() for p in a.split(",", 1)]
        else:
            parts = a.split()
            last, first = parts[-1], " ".join(parts[:-1])
        out.append((last, first))
    return out


def initials(first):
    toks = []
    for t in re.split(r"[\s.]+", first):
        if not t:
            continue
        if t.isupper() and len(t) <= 3:  # "CM" -> C. M.
            toks += [c + "." for c in t]
        else:
            toks += ["-".join(p[0] + "." for p in t.split("-") if p)]
    return " ".join(toks)


def highlighted(fields):
    """Author indices (0-based) marked with Author+an = {1=highlight}."""
    raw = fields.get("author+an", "")
    return {int(m) - 1 for m in re.findall(r"(\d+)\s*=\s*highlight", raw)}


def clean_location(note, year):
    """'Breckenridge, CO, Jan 30-Feb 4,' -> ('Breckenridge, CO', 'Jan 30-Feb 4')."""
    note = re.split(r"\\\\", note)[0]  # anything after a LaTeX line break is CV-only
    note = latex_to_text(note).strip().rstrip(",").strip()
    if year:
        note = re.sub(rf",?\s*{year}$", "", note).strip().rstrip(",")
    parts = [p.strip() for p in note.split(",")]
    if parts and re.match(rf"({'|'.join(m.capitalize() for m in MONTHS)})\b", parts[-1]):
        return ", ".join(parts[:-1]), parts[-1]
    return note, ""


def iso_date(fields, year, dates):
    if fields.get("date"):
        return fields["date"]
    m = re.match(r"(\d{2})(\d{2})\.\d+", fields.get("eprint", ""))  # arXiv 2605.x -> 2026-05
    if m:
        return f"20{m.group(1)}-{m.group(2)}-01"
    if dates:  # 'Jan 30-Feb 4' -> 2026-01-30
        m = re.match(r"(\w{3})\w*\s+(\d+)", dates)
        if m and m.group(1).lower() in MONTHS:
            return f"{year}-{MONTHS.index(m.group(1).lower()) + 1:02d}-{int(m.group(2)):02d}"
    return f"{year}-01-01" if year else ""


def site_url(u):
    """pdfs/x.pdf -> /pdfs/x.pdf; leave absolute URLs alone."""
    return u if re.match(r"https?://", u) else "/" + u.lstrip("/")


def cite_block(etype, key, fields):
    lines = [f"@{etype}{{{key},"]
    for f in CITE_FIELDS:
        v = fields.get(f, "").strip()
        if not v:
            continue
        if f == "author":
            v = re.sub(r"\{?\\color\{[^}]*\}\{?\\FiveStar\}?\}?\s*", "", v)
        if f == "note":
            v = re.split(r"\\\\", v)[0].strip().rstrip(",")
        lines.append(f"  {f} = {{{v}}},")
    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------- main
def build():
    entries, problems = [], []
    this_year = date.today().year
    for path in sorted(BIB_DIR.glob("*.bib")):
        for etype, key, f in parse_bib(path.read_text(encoding="utf-8")):
            if f.get("website", "").lower() in ("no", "false", "hide"):
                continue
            authors = split_authors(f.get("author", ""))
            mine = highlighted(f) or {i for i, (l, fi) in enumerate(authors)
                                      if l.lower() == ME[0] and fi.lower().startswith(ME[1])}
            if not any(l.lower() == ME[0] and fi.lower().startswith(ME[1]) for l, fi in authors):
                problems.append(f"{path.name}:{key} skipped (Anubhav Gupta is not an author)")
                continue
            section = SECTION_BY_FILE.get(path.name) or SECTION_BY_TYPE.get(etype, "other")
            if path.name == "ref_journal.bib":
                section = SECTION_BY_TYPE.get(etype, "journal")
            year = (f.get("year") or f.get("date", "")[:4]).strip()
            if not year:
                problems.append(f"{path.name}:{key} has no year")
            location, dates = clean_location(f.get("note", ""), year)
            publisher = latex_to_text(f.get("publisher", ""))
            status = ""
            if "preparation" in publisher.lower():
                status, publisher = "In preparation", ""
            elif year.isdigit() and int(year) > this_year:
                status = "Forthcoming"

            venue = latex_to_text(f.get("booktitle") or f.get("journal") or f.get("school") or "")
            detail = []
            if section == "book":
                ed = latex_to_text(f.get("edition", ""))
                if ed and not ed.lower().startswith("1st"):
                    detail.append(ed)
                if publisher:
                    venue = publisher
                location = latex_to_text(f.get("address", ""))
            elif section == "thesis":
                detail.append("Master's thesis" if etype == "mastersthesis" else "PhD dissertation")
            elif section == "patent":
                venue = f"{latex_to_text(f.get('type', 'Patent'))} {latex_to_text(f.get('number', ''))}".strip()
                note = latex_to_text(f.get("note", ""))
                filed = f.get("date", "")
                if filed:
                    y, mth, d = (filed.split("-") + ["01", "01"])[:3]
                    note = f"{note or 'Filed'} {['January','February','March','April','May','June','July','August','September','October','November','December'][int(mth)-1]} {int(d)}, {y}"
                if note:
                    detail.append(note)
                location = ""
            elif section == "journal":
                vol, num, pages = f.get("volume", ""), f.get("number", ""), latex_to_text(f.get("pages", ""))
                vi = vol + (f"({num})" if num else "")
                detail.append(", ".join(x for x in [vi, pages] if x))
            elif section == "talk" and etype == "article":
                detail.append("Invited talk")
            elif section == "preprint" and f.get("eprint"):
                venue = f"arXiv:{f['eprint']}" + (f" [{f['primaryclass']}]" if f.get("primaryclass") else "")
            if section == "book" and f.get("note"):
                detail.append(latex_to_text(f["note"]).strip("()").rstrip("."))

            links = []
            def link(label, url):
                if url:
                    links.append({"label": label, "url": url})
            link("PDF", site_url(f["pdf"]) if f.get("pdf") else "")
            if f.get("doi"):
                link("DOI", f"https://doi.org/{f['doi']}")
            if section == "preprint" and f.get("eprint"):
                link("arXiv", f"https://arxiv.org/abs/{f['eprint']}")
            elif f.get("url"):
                host = re.sub(r"^https?://(www\.)?([^/]+).*", r"\2", f["url"])
                label = {"ieeexplore.ieee.org": "IEEE Xplore", "zenodo.org": "Zenodo",
                         "scholar.colorado.edu": "CU Scholar", "arc.aiaa.org": "AIAA"}.get(host, "Link")
                link(label, f["url"])
            link("Poster", f.get("poster", ""))
            link("Slides", f.get("slides", ""))
            link("ProQuest", f.get("proquest", ""))
            link("WorldCat", f.get("worldcat", ""))
            link("Amazon", f.get("amazon", ""))

            pdf = f.get("pdf", "")
            entries.append({
                "key": key,
                "type": etype,
                "section": section,
                "title": latex_to_text(f.get("title", "")),
                "authors": [{"name": f"{fi} {l}".strip(), "short": f"{l}, {initials(fi)}".strip(", "),
                             "full": f"{l}, {fi}".strip(", "),
                             "me": i in mine} for i, (l, fi) in enumerate(authors)],
                "venue": venue,
                "detail": "; ".join(d for d in detail if d),
                "location": location,
                "dates": dates,
                "year": year,
                "date": iso_date(f, year, dates),
                "status": status,
                "award": latex_to_text(f.get("award", "")),
                "doi": f.get("doi", ""),
                "pdf": site_url(pdf) if pdf else "",
                "pdfHosted": bool(pdf) and not re.match(r"https?://", pdf),
                "abstract": latex_to_text(f.get("abstract", "")),
                "links": links,
                "bibtex": cite_block(etype, key, f),
                "source": path.name,
            })
    keys = [e["key"] for e in entries]
    for k in {k for k in keys if keys.count(k) > 1}:
        problems.append(f"duplicate key {k}")
    # Number entries within each section, oldest = 1, so existing numbers stay
    # the same when a newer entry is added (C9 stays C9 when C10 arrives).
    for section, prefix in PREFIX.items():
        items = sorted((e for e in entries if e["section"] == section),
                       key=lambda e: (e["date"], e["key"]))
        for n, e in enumerate(items, 1):
            e["num"], e["n"] = f"{prefix}{n}", n
    entries.sort(key=lambda e: (e["date"], e["key"]), reverse=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(entries, indent=1, ensure_ascii=False), encoding="utf-8")
    for p in problems:
        print("note:", p, file=sys.stderr)
    print(f"Wrote {len(entries)} entries to {OUT.relative_to(ROOT)}")
    return 1 if any("duplicate" in p for p in problems) else 0


if __name__ == "__main__":
    sys.exit(build())
