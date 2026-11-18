#!/usr/bin/env python3
"""Builds the static site: src/layout.html + src/pages/*.html -> ./*.html

Run after editing anything in src/:  python3 build.py
No dependencies beyond the Python standard library.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"

# Where the tryout and highlight-tape forms are delivered. FormSubmit forwards each
# submission to this inbox; the first submission sends a one-time activation email.
FORM_ENDPOINT = "https://formsubmit.co/sanjeev@parmarsportstraining.com"
SITE_URL = "https://codebyjn.github.io/futuro-site/"
ACADEMY_EMAIL = "sanjeev@parmarsportstraining.com"

NAV = [
    ("about.html", "About"),
    ("success.html", "Success Stories"),
    ("coaches.html", "Coaches"),
    ("program.html", "Program"),
    ("apply.html", "Apply"),
    ("graduates.html", "Graduates"),
]

SPONSORS = [
    ("puma", "Puma", True), ("rbc", "RBC Dominion Securities, Jeanty Wealth Management", False),
    ("dominos", "Domino's", False), ("agropur", "Agropur", False),
    ("perley-robertson", "Perley-Robertson, Hill & McDougall", False), ("jiffy-lube", "Jiffy Lube", False),
    ("champion-petfoods", "Champion Petfoods", False), ("fitness-depot", "Fitness Depot", False),
    ("preston-hardware", "Preston Hardware", False), ("lapointe", "Lapointe", False),
    ("clocktower", "Clocktower Brew Pub", False), ("medron", "Medron Medical Systems", False),
    ("evangelista", "Evangelista Sports", False), ("mortgage-group", "The Mortgage Group", True),
    ("billings-bridge-dental", "Billings Bridge Dental Centre", True), ("happy-goat", "Happy Goat Coffee Company", False),
    ("east-india-company", "East India Company Restaurants", False), ("homestead", "Homestead", False),
    ("mercato-zacconi", "Mercato Zacconi", False), ("movement-union", "Movement Union", False),
    ("denis-labelle", "Denis Labelle Distribution", False), ("econo-gas", "Econo Gas", False),
    ("tosca", "Tosca Ristorante", False), ("infiniti-wealth", "Infiniti Wealth Management", False),
    ("pharmaco", "Pharmaco Alliance", True), ("electric-mark", "Electric Mark", True),
    ("laws-of-motion", "Laws of Motion", True), ("la-belle-la-boeuf", "La Belle & La Boeuf", False),
    ("aahar", "Aahar", False), ("sweda", "Sweda", True), ("reitano-concrete", "Reitano Concrete", True),
    ("maple-laundromart", "Maple Laundromart", False), ("p-design-studio", "P Design Studio", True),
]

# (file slug, title, group)
POLICIES = [
    ("childsafeguarding", "Child Safeguarding", "Safety & wellbeing"),
    ("concussioninfo", "Concussion Information & Protocol", "Safety & wellbeing"),
    ("emergencyactionplan", "Emergency Action Plan (EAP)", "Safety & wellbeing"),
    ("incidentguidelines", "Incident / Accident Guidelines", "Safety & wellbeing"),
    ("incidentaccidentreport", "Incident / Accident Report", "Safety & wellbeing"),
    ("adultpresence", "Adult Presence Policy", "Safety & wellbeing"),
    ("screening", "Screening Policy", "Safety & wellbeing"),
    ("weathercancellation", "Weather Cancellation Policy", "Safety & wellbeing"),
    ("healthysnack", "Healthy Snack Policy", "Safety & wellbeing"),
    ("tobaccofree", "Tobacco-Free Policy", "Safety & wellbeing"),
    ("parentcodeofconduct", "Parent Code of Conduct", "Codes of conduct"),
    ("playercodeofconduct", "Player Code of Conduct", "Codes of conduct"),
    ("coachescodeofconduct", "Coaches Code of Conduct", "Codes of conduct"),
    ("zerotolerance", "Zero Tolerance Policy", "Codes of conduct"),
    ("disciplinepolicy", "Discipline Policy", "Codes of conduct"),
    ("equityandharassment", "Equity & Harassment Policy", "Codes of conduct"),
    ("oathofconfidentiality", "Oath of Confidentiality", "Codes of conduct"),
    ("academycommunication", "Academy Communication Policy", "Club operations"),
    ("accessibilitypolicy", "Accessibility Policy", "Club operations"),
    ("refund", "Refund Policy", "Club operations"),
    ("playersuniform", "Players Uniform Policy", "Club operations"),
    ("foundationplayingup", "Playing Up / Down (U8–U12)", "Playing up"),
    ("youthplayingup", "Play-Up Procedures (13+)", "Playing up"),
]
POLICY_PDFS = {
    "incidentaccidentreport": ("assets/docs/incident-accident-report.pdf", "Download the Incident / Accident Report form (PDF)"),
    "oathofconfidentiality": ("assets/docs/oath-of-confidentiality.pdf", "Download the Oath of Confidentiality (PDF)"),
}


def esc(s):
    return html.escape(s, quote=True)


# ---------- Hero collage ----------
def collage():
    tiles = sorted((ROOT / "assets/img/collage").glob("*.webp"))
    rows, per = 5, (len(tiles) + 4) // 5
    out = []
    for r in range(rows):
        chunk = tiles[r * per:(r + 1) * per]
        imgs = "".join(
            f'<img src="assets/img/collage/{t.name}" alt="" width="144" height="180" decoding="async">'
            for t in chunk
        )
        # duplicated once so the loop is seamless
        out.append(f'<div class="c-row"><div class="c-track">{imgs}{imgs}</div></div>')
    return "\n".join(out)


# ---------- Sponsor marquee ----------
def sponsors():
    items = "".join(
        f'<li class="logo{" invert" if inv else ""}"><img src="assets/img/sponsors/{slug}.png" alt="{esc(name)}" loading="lazy"></li>'
        for slug, name, inv in SPONSORS
    )
    dup = items.replace('alt="', 'aria-hidden="true" alt="').replace('<li class="logo', '<li aria-hidden="true" class="logo')
    dup = re.sub(r'alt="[^"]*"', 'alt=""', dup)
    return f'<ul class="marquee-track">{items}{dup}</ul>'


def sponsor_grid():
    items = "".join(
        f'<li class="logo{" invert" if inv else ""}"><img src="assets/img/sponsors/{slug}.png" alt="{esc(name)}" loading="lazy"></li>'
        for slug, name, inv in SPONSORS
    )
    return (
        f'<details class="sponsor-all"><summary>See all {len(SPONSORS)} supporters</summary>'
        f'<ul class="logo-grid">{items}</ul></details>'
    )



# ---------- Carousels ----------
ARROW = '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def carousel(label, slides, cls=""):
    """Swipeable row: native scroll-snap, with prev/next buttons added by main.js."""
    return (
        f'<div class="carousel {cls}" data-carousel>'
        f'<div class="carousel-track" role="region" aria-label="{esc(label)}" tabindex="0">{"".join(slides)}</div>'
        '<div class="carousel-ctrl">'
        f'<button class="car-btn prev" type="button" data-dir="-1" aria-label="Previous">{ARROW}</button>'
        '<span class="car-count" aria-live="polite"></span>'
        f'<button class="car-btn" type="button" data-dir="1" aria-label="Next">{ARROW}</button>'
        "</div></div>"
    )


def load_coaches():
    return json.loads((SRC / "coaches.json").read_text())


def coach_carousel():
    slides = [
        f'<a class="slide coach-card" href="coaches.html#{c["slug"]}">'
        f'<img src="{c["photo"]}" alt="" loading="lazy" width="480" height="600">'
        f'<div><h3>{esc(c["name"])}</h3><p class="role">{esc(c["role"])}</p><p class="sum">{esc(c["summary"])}</p></div></a>'
        for c in load_coaches()
    ]
    return carousel("Coaching staff", slides, "coach-carousel")


def staff_carousel():
    slides = []
    for c in load_coaches():
        ticks = "".join(f"<li>{t}</li>" for t in c["credentials"])
        extra = (
            f'<p class="staff-mail"><a class="link-arrow" href="mailto:{ACADEMY_EMAIL}">{ACADEMY_EMAIL}</a></p>'
            if c["slug"] == "sanjeev-parmar" else ""
        )
        slides.append(
            f'<article class="slide staff-card" id="{c["slug"]}">'
            f'<img src="{c["photo"]}" alt="{esc(c["photo_alt"])}" loading="lazy" width="480" height="600">'
            f'<div><h2>{esc(c["name"])}</h2><p class="role">{esc(c["role"])}</p><ul class="ticks">{ticks}</ul>{extra}</div></article>'
        )
    return carousel("Coaching staff, swipe for more", slides, "staff-carousel")


# ---------- Policies ----------
URL_RE = re.compile(r"(https?://[^\s<]+)")


def linkify(s):
    return URL_RE.sub(lambda m: f'<a href="{m.group(1)}" rel="noopener" target="_blank">{m.group(1)}</a>', s)


def clean_policy(text, title):
    text = text.replace("​", "").replace("\xa0", " ")
    text = text.split("Quick Links")[0]
    lines = [l.strip() for l in text.splitlines()]
    lines = [l for l in lines if l and not l.startswith("[IMG")]
    if lines and lines[0].lower().startswith("policies"):
        lines = lines[1:]
    # drop the page's own heading (can be split across two short lines)
    while lines and len(lines[0]) < 70 and not lines[0].endswith("."):
        lines = lines[1:]
        if lines and len(lines[0]) < 40 and not lines[0].endswith(".") and lines[0][:1].isupper():
            continue
        break
    # rejoin hard-wrapped lines
    merged = []
    for l in lines:
        if merged:
            prev = merged[-1]
            wrapped = not re.search(r"[.:;!?)]$", prev) and (l[:1].islower() or prev.endswith((",", "-", "and", "or", "the", "of", "to")))
            if wrapped and not re.match(r"^(\d+\.|[a-z]\.|•|-)\s", l):
                merged[-1] = prev.rstrip("- ") + (" " if not prev.endswith("-") else "") + l
                continue
        merged.append(l)
    out, in_list = [], False
    for l in merged:
        bullet = re.match(r"^(?:•|-|\*)\s*(.+)", l)
        numbered = re.match(r"^(\d+|[a-z])\.\s+(.+)", l)
        if bullet or numbered:
            if not in_list:
                out.append('<ul class="plain">' if numbered else "<ul>")
                in_list = True
            body = bullet.group(1) if bullet else f"<b>{numbered.group(1)}.</b> {esc(numbered.group(2))}"
            out.append(f"<li>{linkify(esc(body)) if bullet else linkify(body)}</li>")
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        if len(l) < 70 and (l.endswith(":") or (l.isupper() and len(l) > 3)):
            out.append(f"<h4>{esc(l.rstrip(':'))}</h4>")
        else:
            out.append(f"<p>{linkify(esc(l))}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def policies():
    groups = {}
    for slug, title, group in POLICIES:
        body = clean_policy((SRC / "policies" / f"{slug}.txt").read_text(), title)
        if slug in POLICY_PDFS:
            href, label = POLICY_PDFS[slug]
            body += f'\n<p><a class="btn btn-small" href="{href}" download>{label}</a></p>'
        groups.setdefault(group, []).append(
            f'<details class="policy" id="{slug}" data-title="{esc(title.lower())}">'
            f'<summary>{esc(title)}</summary><div class="policy-body">{body}</div></details>'
        )
    return "\n".join(
        f'<section class="policy-group" aria-labelledby="g-{i}"><h2 id="g-{i}" class="group-title">{esc(g)}</h2>{"".join(items)}</section>'
        for i, (g, items) in enumerate(groups.items())
    )


# ---------- Graduates board ----------
def yt_id(url):
    m = re.search(r"(?:youtu\.be/|v=|embed/|shorts/)([\w-]{11})", url)
    return m.group(1) if m else None


def load_grads():
    return json.loads((SRC / "graduates.json").read_text())


def grads_home():
    """Home page: the newest approved graduates, or last year's commitments while the board is empty."""
    grads = load_grads()
    if grads:
        return grad_cards(grads[:3])
    picks = [
        ("NCAA D1", "Brianne MacDonald", "University of Central Florida"),
        ("NCAA", "Stella De Capua", "University of Bridgeport"),
        ("U SPORTS", "Justin Meka", "University of Toronto"),
        ("U SPORTS", "Amelia Racicot", "University of Toronto"),
    ]
    items = "".join(f"<li><strong>{n}</strong><span>{u}</span><small>{t}</small></li>" for t, n, u in picks)
    return f'<p class="mini-label">Class of 2025 commitments</p><ul class="commit-list">{items}</ul>'


def graduates():
    grads = load_grads()
    if not grads:
        return (
            '<div class="empty-board">'
            "<h3>The first highlight tapes are being reviewed.</h3>"
            "<p>Approved players will appear here with their highlight video, position and graduating class. "
            'Graduating players can submit their tape <a href="#submit">below</a>.</p></div>'
        )
    return grad_cards(grads)


def grad_cards(grads):
    cards = []
    for g in grads:
        vid = yt_id(g.get("youtube", ""))
        subject = f"Scout inquiry: {g['name']} (Class of {g['grad_year']})"
        video = (
            f'<button class="video" data-yt="{vid}"><img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy">'
            f'<span>{esc(g["name"])} highlights</span></button>' if vid else ""
        )
        cards.append(
            f'<article class="grad-card">{video}<div class="grad-body">'
            f'<span class="tag">Class of {esc(str(g["grad_year"]))}</span><h3>{esc(g["name"])}</h3>'
            f'<p class="meta">{esc(g.get("position", ""))}{", " + esc(g["team"]) if g.get("team") else ""}</p>'
            f'{"<p>" + esc(g["note"]) + "</p>" if g.get("note") else ""}'
            f'<a class="btn btn-small btn-ghost" href="mailto:{ACADEMY_EMAIL}?subject={html.escape(subject).replace(" ", "%20")}">Contact through the academy</a>'
            "</div></article>"
        )
    return '<div class="grad-grid">' + "".join(cards) + "</div>"


# ---------- Page assembly ----------
def nav(current):
    cur = ' aria-current="page"'
    links = "".join(
        f'<a href="{href}"{cur if href == current else ""}>{label}</a>' for href, label in NAV
    )
    return links + '<a class="btn btn-primary" href="register.html">Register for Tryouts</a>'


def main():
    layout = (SRC / "layout.html").read_text()
    parts = {
        "collage": collage, "sponsors": sponsors, "sponsor_grid": sponsor_grid, "policies": policies,
        "graduates": graduates, "grads_home": grads_home, "coach_carousel": coach_carousel,
        "staff_carousel": staff_carousel,
    }
    for page in sorted((SRC / "pages").glob("*.html")):
        raw = page.read_text()
        meta = dict(re.findall(r"^<!--\s*(\w+):\s*(.*?)\s*-->", raw, re.M))
        body = re.sub(r"^<!--\s*\w+:.*?-->\n", "", raw, flags=re.M)
        for key, fn in parts.items():
            if "{{" + key + "}}" in body:
                body = body.replace("{{" + key + "}}", fn())
        out = (
            layout.replace("{{title}}", esc(meta.get("title", "Futuro Soccer Academy")))
            .replace("{{description}}", esc(meta.get("description", "")))
            .replace("{{body_class}}", meta.get("body_class", ""))
            .replace("{{nav}}", nav(page.name))
            .replace("{{body}}", body)
        )
        out = (
            out.replace("{{form_endpoint}}", FORM_ENDPOINT)
            .replace("{{site_url}}", SITE_URL)
            .replace("{{email}}", ACADEMY_EMAIL)
        )
        (ROOT / page.name).write_text(out)
        print("built", page.name)


if __name__ == "__main__":
    main()
