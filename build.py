#!/usr/bin/env python3
"""Builds the static site.

  content/*.json, content/policies/*.md   what the site says (edited by the academy in Pages CMS)
  src/layout.html, src/pages/*.html       how it looks (page templates with {{placeholders}})
  ->  ./*.html

Run:  python3 build.py
Only the standard library is required. If Pillow is installed, uploaded photos are resized and
converted to WebP; if ffmpeg is on the PATH, uploaded videos are compressed. GitHub Actions has both.

A bad or missing entry in a content file prints a warning and is skipped, so one typo can't take the
site down.
"""
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
CONTENT = ROOT / "content"
OPT = ROOT / "assets" / "opt"          # generated, resized copies of uploads (not committed)
UPLOADS = ("assets/uploads/",)         # only files Sanj uploads get optimized; hand-made assets are already
SITE_URL = "https://codebyjn.github.io/futuro-site/"

NAV = [
    ("about.html", "About"),
    ("success.html", "Success Stories"),
    ("coaches.html", "Coaches"),
    ("program.html", "Program"),
    ("apply.html", "Apply"),
    ("graduates.html", "Graduates"),
]

POLICY_SECTIONS = ["Safety & wellbeing", "Codes of conduct", "Club operations", "Playing up"]

WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)
    print("WARNING:", msg, file=sys.stderr)


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=False).replace('"', "&quot;")


def md(s):
    """Escape text, then allow **bold** and *italic* (all the formatting the editor needs)."""
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(s))
    return re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)


def slugify(s):
    s = re.sub(r"[^\w\s-]", "", str(s).lower().replace("&", "and"))
    return re.sub(r"[\s_-]+", "-", s).strip("-") or "item"


def load(name, default):
    path = CONTENT / name
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        warn(f"{name} is missing; using defaults")
        return default
    except json.JSONDecodeError as e:
        warn(f"{name} could not be read ({e}); using defaults")
        return default
    return data


def items(name, required=("name",)):
    """A content list, keeping only entries that have their required fields filled in."""
    data = load(name, [])
    if isinstance(data, dict):  # tolerate {"items": [...]}
        data = next((v for v in data.values() if isinstance(v, list)), [])
    out = []
    for i, d in enumerate(data, 1):
        if not isinstance(d, dict):
            continue
        missing = [k for k in required if not str(d.get(k) or "").strip()]
        if missing:
            warn(f"{name}: entry {i} skipped, missing {', '.join(missing)}")
            continue
        out.append(d)
    return out


SETTINGS = {}


def setting(*keys, default=""):
    d = SETTINGS
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d if d not in (None, "") else default


# ---------- Media: clean paths, resize uploads ----------
def path_of(p):
    """Editor paths may start with '/'; the site lives under /futuro-site/, so keep them relative."""
    return str(p or "").strip().lstrip("/")


def _opt_name(src, suffix):
    h = hashlib.md5(src.read_bytes()).hexdigest()[:10]
    return OPT / f"{src.stem[:40]}-{h}{suffix}"


def img(p, width=1200, force=False):
    """Return a web-ready path for an image. Uploads are resized to `width` and saved as WebP."""
    p = path_of(p)
    src = ROOT / p
    if not (force or p.startswith(UPLOADS)) or not src.is_file():
        if p and not src.is_file():
            warn(f"image not found: {p}")
        return p
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return p
    try:  # iPhone photos (.heic)
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    out = _opt_name(src, f"-{width}.webp")
    if not out.exists():
        OPT.mkdir(parents=True, exist_ok=True)
        try:
            with Image.open(src) as im:
                im = ImageOps.exif_transpose(im)
                if im.width > width:
                    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
                im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
                im.save(out, "WEBP", quality=82, method=5)
        except Exception as e:  # unreadable upload: fall back to the original file
            warn(f"could not resize {p}: {e}")
            return p
    return out.relative_to(ROOT).as_posix()


def video(p):
    """Compress an uploaded video to a 540px-wide silent MP4 (and make a poster frame). Returns (video, poster)."""
    p = path_of(p)
    src = ROOT / p
    if not p.startswith(UPLOADS) or not src.is_file():
        if p and not src.is_file():
            warn(f"video not found: {p}")
        return p, ""
    out, poster = _opt_name(src, ".mp4"), _opt_name(src, ".jpg")
    if out.exists() and poster.exists():  # compressed in an earlier build
        return out.relative_to(ROOT).as_posix(), poster.relative_to(ROOT).as_posix()
    if not shutil.which("ffmpeg"):
        warn(f"ffmpeg is not installed, so {p} is used uncompressed")
        return p, ""
    OPT.mkdir(parents=True, exist_ok=True)
    try:
        if not out.exists():
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-an", "-vf", "scale=540:-2",
                            "-c:v", "libx264", "-crf", "30", "-maxrate", "1000k", "-bufsize", "2000k",
                            "-preset", "slow", "-movflags", "+faststart", "-pix_fmt", "yuv420p", str(out)],
                           check=True, timeout=900)
        if not poster.exists():
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1", "-i", str(out), "-frames:v", "1",
                            "-q:v", "4", str(poster)], check=True, timeout=120)
    except Exception as e:
        warn(f"could not compress {p}: {e}")
        return p, ""
    return out.relative_to(ROOT).as_posix(), poster.relative_to(ROOT).as_posix()


FOCUS = {"Far left": "12% center", "Left": "28% center", "Right": "72% center", "Top": "center 20%", "Bottom": "center 80%"}


def focus_style(d, legend=False):
    f = d.get("photo_focus") or "Center"
    if f == "Center":
        return ""
    return f' style="object-position:{FOCUS.get(f, "center")}"'


# ---------- Announcement bar ----------
def announcement():
    a = setting("announcement", default={})
    if not isinstance(a, dict) or not a.get("show") or not str(a.get("text") or "").strip():
        return ""
    btn = ""
    if a.get("button_text") and a.get("button_link"):
        link = a["button_link"].strip()
        ext = ' target="_blank" rel="noopener"' if link.startswith("http") else ""
        btn = f'<a class="announce-btn" href="{esc(link)}"{ext}>{esc(a["button_text"])}</a>'
    key = hashlib.md5(str(a.get("text")).encode()).hexdigest()[:8]  # a new message shows again even if the old one was closed
    return (f'<div class="announce" role="region" aria-label="Announcement" data-key="{key}" hidden><p>{md(a["text"])}</p>{btn}'
            '<button class="announce-x" type="button" aria-label="Close announcement">&times;</button></div>')


# ---------- Hero ----------
def collage():
    folder = ROOT / "assets/img/collage"
    tiles = sorted(f for f in folder.iterdir() if f.suffix.lower() in (".webp", ".jpg", ".jpeg", ".png"))
    # photos Sanj adds are resized; the original tiles are already small WebPs
    srcs = [img(f"assets/img/collage/{t.name}", 360, force=t.suffix.lower() != ".webp" or t.stat().st_size > 200_000) for t in tiles]
    rows, per = 5, (len(tiles) + 4) // 5
    out = []
    for r in range(rows):
        chunk = srcs[r * per:(r + 1) * per]
        imgs = "".join(f'<img src="{esc(t)}" alt="" width="144" height="180" decoding="async">' for t in chunk)
        # duplicated once so the loop is seamless
        out.append(f'<div class="c-row"><div class="c-track">{imgs}{imgs}</div></div>')
    return "\n".join(out)


def hero_headline():
    return esc(setting("hero", "headline", default="Built for players who chase excellence."))


def hero_subtitle():
    return esc(setting("hero", "subtitle"))


def hero_stats():
    stats = [s for s in setting("hero", "stats", default=[]) if isinstance(s, dict) and s.get("number")]
    return "\n".join(
        f'      <div><dt>{esc(s.get("label"))}</dt><dd><span>{esc(s["number"])}</span></dd></div>' for s in stats
    )


def success_stats():
    stats = [s for s in setting("success_stats", default=[]) if isinstance(s, dict) and s.get("number")]
    return "\n".join(
        f'    <div class="stat"><b>{esc(s["number"])}</b><span>{esc(s.get("label"))}</span></div>' for s in stats
    )


# ---------- Sponsors ----------
def load_sponsors():
    return items("sponsors.json", ("name", "logo"))


def sponsor_li(s, hidden=False):
    cls = "logo invert" if s.get("light_logo") else "logo"
    alt = "" if hidden else esc(s["name"])
    aria = ' aria-hidden="true"' if hidden else ""
    hid = 'aria-hidden="true" ' if hidden else ""
    return f'<li{aria} class="{cls}"><img src="{esc(img(s["logo"], 480))}" {hid}alt="{alt}" loading="lazy"></li>'


def sponsors():
    sp = load_sponsors()
    return f'<ul class="marquee-track">{"".join(sponsor_li(s) for s in sp)}{"".join(sponsor_li(s, True) for s in sp)}</ul>'


def sponsor_grid():
    sp = load_sponsors()
    return (
        f'<details class="sponsor-all"><summary>See all {len(sp)} supporters</summary>'
        f'<ul class="logo-grid">{"".join(sponsor_li(s) for s in sp)}</ul></details>'
    )


# ---------- Carousels ----------
ARROW = '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def carousel(label, slides, cls="", track_cls=""):
    """Swipeable row: native scroll-snap, with prev/next buttons added by main.js."""
    return (
        f'<div class="carousel {cls}" data-carousel>'
        f'<div class="carousel-track{(" " + track_cls) if track_cls else ""}" role="region" aria-label="{esc(label)}" tabindex="0">{"".join(slides)}</div>'
        '<div class="carousel-ctrl">'
        f'<button class="car-btn prev" type="button" data-dir="-1" aria-label="Previous">{ARROW}</button>'
        '<span class="car-count" aria-live="polite"></span>'
        f'<button class="car-btn" type="button" data-dir="1" aria-label="Next">{ARROW}</button>'
        "</div></div>"
    )


# ---------- Season calendar ----------
MONTHS = ["September", "October", "November", "December", "January", "February",
          "March", "April", "May", "June", "July", "August"]
COLOURS = {"Green": "c-green", "Blue": "c-blue", "Yellow": "c-yellow", "White": "c-white", "Red": "c-red"}


def season_calendar():
    """One 12-month strip (season year Sep-Aug) showing when each program runs. main.js marks the current month."""
    head = "".join(f'<span data-i="{i + 1}"><span class="m-l">{m[:3]}</span><span class="m-s">{m[0]}</span></span>'
                   for i, m in enumerate(MONTHS))
    rows = []
    for d in items("season.json", ("name", "starts", "ends")):
        try:
            a, b = MONTHS.index(d["starts"]) + 1, MONTHS.index(d["ends"]) + 1
        except ValueError:
            warn(f"season.json: {d['name']} has an unknown month")
            continue
        if b < a:  # runs past August: show it to the end of the season year
            b = 12
        full = a == 1 and b == 12
        mid = bool(d.get("ends_mid_month"))
        dates = "" if full else f'{MONTHS[a - 1][:3]} – {"mid-" if mid else ""}{MONTHS[b - 1][:3]}'
        note = (d.get("note") or "").strip()
        long_txt = ", ".join(x for x in (dates, note) if x)
        short = d.get("short_name") or d["name"]
        cls = ["cal-lane", COLOURS.get(d.get("colour"), "c-green")]
        if b - a < 2:
            cls.append("is-short")  # too narrow for text: label sits beside the bar
        if mid:
            cls.append("mid-end")
        label = (f'<span class="cal-label"><span class="c-l"><b>{esc(d["name"])}</b>{" <i>" + esc(long_txt) + "</i>" if long_txt else ""}</span>'
                 f'<span class="c-s" aria-hidden="true"><b>{esc(short)}</b>{" <i>" + esc(note) + "</i>" if note else ""}</span></span>')
        rows.append(f'<li class="{" ".join(cls)}" style="--s:{a};--e:{b + 1}" data-name="{esc(d["name"])}"'
                    f'{" data-all" if full else ""}><span class="cal-bar"></span>{label}</li>')
    return (
        '<div class="season-cal" data-season-cal>'
        '<div class="cal-top"><p class="cal-now"><span class="cal-dot" aria-hidden="true"></span>'
        '<span data-cal-now>Players can join in any month.</span></p>'
        '<span class="cal-note">The season runs September to August</span></div>'
        '<div class="cal-grid">'
        f'<div class="cal-months" aria-hidden="true">{head}</div>'
        f'<ul class="cal-lanes">{"".join(rows)}</ul>'
        "</div></div>"
    )


def programs_table():
    return "\n".join(
        f'          <tr><td><b>{esc(p["program"])}</b><small>{esc(p.get("stage"))}</small></td><td>{esc(p.get("ages"))}</td>'
        f'<td>{esc(p.get("birth_years"))}</td><td>{esc(p.get("teams"))}</td><td>{esc(p.get("schedule"))}</td></tr>'
        for p in items("programs.json", ("program",))
    )


# ---------- Coaches ----------
def load_coaches():
    return items("coaches.json", ("name", "role", "photo"))


def coach_count():
    return str(len(load_coaches()))


def coach_carousel():
    slides = [
        f'<a class="slide coach-card" href="coaches.html#{slugify(c["name"])}">'
        f'<img src="{esc(img(c["photo"], 720))}" alt="" loading="lazy" width="480" height="600">'
        f'<div><h3>{esc(c["name"])}</h3><p class="role">{esc(c["role"])}</p><p class="sum">{esc(c.get("summary"))}</p></div></a>'
        for c in load_coaches()
    ]
    return carousel("Coaching staff", slides, "coach-carousel")


def staff_carousel():
    email = setting("contact", "email")
    slides = []
    for c in load_coaches():
        ticks = "".join(f"<li>{md(t)}</li>" for t in c.get("credentials") or [] if str(t).strip())
        extra = (
            f'<p class="staff-mail"><a class="link-arrow" href="mailto:{esc(email)}">{esc(email)}</a></p>'
            if c.get("show_email") and email else ""
        )
        slides.append(
            f'<article class="slide staff-card" id="{slugify(c["name"])}">'
            f'<img src="{esc(img(c["photo"], 720))}" alt="{esc(c.get("photo_alt") or c["name"])}" loading="lazy" width="480" height="600">'
            f'<div><h2>{esc(c["name"])}</h2><p class="role">{esc(c["role"])}</p><ul class="ticks">{ticks}</ul>{extra}</div></article>'
        )
    return carousel("Coaching staff, swipe for more", slides, "staff-carousel")


# ---------- Legends & success ----------
def load_legends():
    return items("legends.json", ("name", "photo"))


def legend_img(d, extra=""):
    pos = ' class="pos-left"' if d.get("photo_focus") == "Left" else ""
    style = focus_style(d) if d.get("photo_focus") not in ("Left", "Center", None, "") else ""
    return f'<img{pos}{style} src="{esc(img(d["photo"], 900))}" alt="{esc(d.get("photo_alt") or d["name"])}" loading="lazy"{extra}>'


def legends_home():
    slides = [
        f'<a class="slide legend-card" href="success.html#{slugify(d["name"])}">{legend_img(d, " width=\"600\" height=\"600\"")}'
        f'<div><h3>{esc(d["name"])}</h3><p class="now">{esc(d.get("headline"))}</p></div></a>'
        for d in load_legends() if d.get("show_on_home", True)
    ]
    return carousel("Futuro legends", slides, "legend-carousel")


def legends_grid():
    out = []
    for d in load_legends():
        style = d.get("style") or "Standard"
        cls = "legend" + (" feature" if style.startswith("Featured") else " next" if style == "Next wave" else "")
        lis = "".join(f"              <li>{md(h)}</li>\n" for h in d.get("highlights") or [] if str(h).strip())
        out.append(
            f'        <article class="{cls}" id="{slugify(d["name"])}">\n'
            f'          {legend_img(d)}\n'
            f'          <div class="legend-body">\n'
            f'            <h3>{esc(d["name"])}</h3>\n'
            f'            <span class="now">{esc(d.get("headline"))}</span>\n'
            f'            <ul>\n{lis}            </ul>\n'
            f'          </div>\n'
            f'        </article>\n'
        )
    return "\n".join(out)


PATHWAYS = {"Pro & pro academy": "pro", "National team": "national", "University": "university"}


def initials(name):
    words = [w for w in re.split(r"[\s&]+", name) if w[:1].isalpha()]
    return "".join(w[0] for w in words[:2]).upper()


def alum_card(name, tag, details, photo=None, cat=None):
    if photo:
        pic = f'<div class="alum-pic"><img src="{esc(img(photo, 480))}" alt="" loading="lazy" width="288" height="360"></div>'
    else:  # no photo yet: a branded placeholder with their initials
        pic = (f'<div class="alum-pic alum-mono" aria-hidden="true"><span>{esc(initials(name))}</span>'
               '<img src="assets/img/crest-sm.png" alt="" width="48" height="60" loading="lazy"></div>')
    data = f' data-cat="{cat}"' if cat else ""
    return (f'<div class="alum"{data}>{pic}<div class="alum-body"><span class="tag">{esc(tag)}</span>'
            f'<strong>{esc(name)}</strong><small>{esc(details)}</small></div></div>')


def alumni_wall():
    return "\n".join(
        "        " + alum_card(a["name"], a.get("label") or a.get("pathway"), a.get("details"), a.get("photo"),
                               PATHWAYS.get(a.get("pathway"), "pro"))
        for a in items("alumni.json", ("name",))
    )


def load_classes():
    classes = [c for c in items("commitments.json", ("year",))]
    return sorted(classes, key=lambda c: -int(str(c["year"])[:4]) if str(c["year"])[:4].isdigit() else 0)


def commitments():
    out = []
    for c in load_classes():
        players = [p for p in c.get("players") or [] if isinstance(p, dict) and p.get("name")]
        lis = "".join(f"            <li><b>{esc(p['name'])}</b>, {esc(p.get('school'))}</li>\n" for p in players)
        out.append(f"        <details>\n          <summary>Class of {esc(c['year'])}</summary>\n          <ul>\n{lis}          </ul>\n        </details>")
    return "\n".join(out)


def latest_class_year():
    c = load_classes()
    return esc(c[0]["year"]) if c else ""


def latest_class():
    """Graduates page: every player in the newest class, with a photo if the wall has one."""
    c = load_classes()
    if not c:
        return ""
    photos = {a["name"]: a.get("photo") for a in items("alumni.json", ("name",)) if a.get("photo")}
    players = [p for p in c[0].get("players") or [] if isinstance(p, dict) and p.get("name")]
    return "\n".join("      " + alum_card(p["name"], p.get("level") or "University", p.get("school"), photos.get(p["name"]))
                     for p in players)


def commitment_total():
    return str(sum(len(c.get("players") or []) for c in load_classes()))


# ---------- Home: reels and gallery ----------
def reels():
    slides = []
    for v in items("videos.json", ("title", "video")):
        src, auto_poster = video(v["video"])
        poster = img(v["poster"], 540) if v.get("poster") else auto_poster
        label = esc(v.get("description") or v["title"])
        slides.append(
            '<figure class="reel slide"><div class="reel-frame">'
            f'<video src="{esc(src)}"{" poster=" + chr(34) + esc(poster) + chr(34) if poster else ""} muted loop playsinline preload="none" '
            f'disablepictureinpicture width="540" height="960" aria-label="Training clip: {label}"></video>'
            f'</div><figcaption><b>{esc(v["title"])}</b><span>{esc(v.get("caption"))}</span></figcaption></figure>'
        )
    return carousel("Training clips from Coach Parmar", slides, "reel-carousel", "reels")


def _pack(n, cols, tall):
    """Place n tiles in a grid (tile 0 wide, tile 1 tall when `tall`); return the last tile's column span
    so it fills out its row and the mosaic never has a hole."""
    grid, spans = {}, []
    for i in range(n):
        w, h = (2, 1) if i == 0 else ((1, 2) if (i == 1 and tall) else (1, 1))
        r = 0
        while True:
            c = next((c for c in range(cols - w + 1) if all((r + y, c + x) not in grid for x in range(w) for y in range(h))), None)
            if c is not None:
                break
            r += 1
        if i == n - 1:  # stretch the last tile to the end of its row
            while c + w < cols and (r, c + w) not in grid:
                w += 1
        for x in range(w):
            for y in range(h):
                grid[(r + y, c + x)] = i
        spans.append(w)
    rows = max((r for r, _ in grid), default=-1) + 1
    holes = rows * cols - len(grid)
    return (spans[-1] if spans else 1), holes


def gallery():
    photos = items("gallery.json", ("photo",))
    n = len(photos)
    last_sm, _ = _pack(n, 2, False)
    last_lg, holes = _pack(n, 4, True)
    tall = holes == 0
    if not tall:  # the tall tile would leave a gap with this many photos: lay them out flat instead
        last_lg, _ = _pack(n, 4, False)
    out = []
    for i, g in enumerate(photos):
        cls = "m-wide" if i == 0 else "m-tall" if (i == 1 and tall) else ""
        style = ""
        if i == n - 1 and i > 0:
            style = f' style="--sm:{last_sm};--lg:{last_lg}"'
            cls = (cls + (" m-wide" if last_sm == 2 and "m-wide" not in cls else "") + " m-last").strip()
        cap = f"<figcaption>{esc(g['caption'])}</figcaption>" if g.get("caption") else ""
        out.append(
            f'      <figure{" class=" + chr(34) + cls + chr(34) if cls else ""}{style}>'
            f'<img{focus_style(g)} src="{esc(img(g["photo"], 1400))}" alt="{esc(g.get("photo_alt") or g.get("caption"))}" loading="lazy">{cap}</figure>'
        )
    return "\n".join(out)


# ---------- Graduates board ----------
def yt_id(url):
    m = re.search(r"(?:youtu\.be/|v=|embed/|shorts/)([\w-]{11})", url or "")
    return m.group(1) if m else None


def load_grads():
    return items("graduates.json", ("name",))


def grads_home():
    """Home page: the newest approved graduates, or the latest class's commitments while the board is empty."""
    grads = load_grads()
    if grads:
        return grad_cards(grads[:3])
    classes = load_classes()
    if not classes:
        return ""
    c = classes[0]
    players = [p for p in c.get("players") or [] if isinstance(p, dict) and p.get("name")][:4]
    lis = "".join(
        f"<li><strong>{esc(p['name'])}</strong><span>{esc(p.get('school'))}</span>"
        f"{'<small>' + esc(p['level']) + '</small>' if p.get('level') else ''}</li>" for p in players
    )
    return f'<p class="mini-label">Class of {esc(c["year"])} commitments</p><ul class="commit-list">{lis}</ul>'


def graduates():
    grads = load_grads()
    if not grads:
        return (
            '<div class="empty-board">'
            "<h3>The first highlight tapes are being reviewed.</h3>"
            "<p>Approved players will appear here with their highlight video, position and graduating class. "
            'New graduates are added by Coach Parmar, so check back soon.</p></div>'
        )
    return grad_cards(grads)


def grad_cards(grads):
    email = setting("contact", "email")
    cards = []
    for g in grads:
        vid = yt_id(g.get("youtube"))
        subject = f"Scout inquiry: {g['name']} (Class of {g.get('grad_year', '')})"
        vid_html = (
            f'<button class="video" data-yt="{vid}"><img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy">'
            f'<span>{esc(g["name"])} highlights</span></button>' if vid else ""
        )
        cards.append(
            f'<article class="grad-card">{vid_html}<div class="grad-body">'
            f'<span class="tag">Class of {esc(g.get("grad_year"))}</span><h3>{esc(g["name"])}</h3>'
            f'<p class="meta">{esc(g.get("position"))}{", " + esc(g["team"]) if g.get("team") else ""}</p>'
            f'{"<p>" + esc(g["note"]) + "</p>" if g.get("note") else ""}'
            f'<a class="btn btn-small btn-ghost" href="mailto:{esc(email)}?subject={esc(subject).replace(" ", "%20")}">Contact through the academy</a>'
            "</div></article>"
        )
    return '<div class="grad-grid">' + "".join(cards) + "</div>"


# ---------- Policies ----------
URL_RE = re.compile(r"(https?://[^\s<]+)")


def linkify(s):
    return URL_RE.sub(lambda m: f'<a href="{m.group(1)}" rel="noopener" target="_blank">{m.group(1)}</a>', s)


def parse_frontmatter(text):
    meta, body = {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if m:
        try:
            import yaml
            meta = yaml.safe_load(m.group(1)) or {}
        except ImportError:
            for line in m.group(1).splitlines():
                k, _, v = line.partition(":")
                v = v.strip()
                if k.strip() and v:
                    try:
                        meta[k.strip()] = json.loads(v)
                    except ValueError:
                        meta[k.strip()] = v.strip("'\"")
        except Exception as e:
            warn(f"policy header could not be read: {e}")
        body = m.group(2)
    return (meta if isinstance(meta, dict) else {}), body


def render_policy(text):
    """Plain text -> HTML. Blank lines separate paragraphs; lines starting with -, • or 1. become lists;
    a short line ending in ':' (or in CAPITALS) becomes a heading; **bold** works anywhere."""
    lines = [l.strip() for l in text.replace("\r", "").splitlines() if l.strip()]
    out, in_list = [], False
    for l in lines:
        bullet = re.match(r"^(?:•|-|\*)\s+(.+)", l) or re.match(r"^•\s*(.+)", l)
        numbered = re.match(r"^(\d+|[a-z])\.\s+(.+)", l)
        if bullet or numbered:
            if not in_list:
                out.append('<ul class="plain">' if numbered else "<ul>")
                in_list = True
            body = md(bullet.group(1)) if bullet else f"<b>{numbered.group(1)}.</b> {md(numbered.group(2))}"
            out.append(f"<li>{linkify(body)}</li>")
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        if len(l) < 70 and (l.endswith(":") or (l.isupper() and len(l) > 3)):
            out.append(f"<h4>{esc(l.rstrip(':'))}</h4>")
        else:
            out.append(f"<p>{linkify(md(l))}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def load_policies():
    pols = []
    for f in sorted((CONTENT / "policies").glob("*.md")):
        meta, body = parse_frontmatter(f.read_text())
        if not meta.get("title"):
            warn(f"policy {f.name} skipped, it has no title")
            continue
        if meta.get("hidden"):
            continue
        pols.append({"slug": f.stem, "title": str(meta["title"]), "section": meta.get("section") or "Club operations",
                     "order": meta.get("order") if isinstance(meta.get("order"), (int, float)) else 999,
                     "download": meta.get("download"), "download_label": meta.get("download_label"), "body": body})
    return sorted(pols, key=lambda p: (p["order"], p["title"]))


def policies():
    groups = {s: [] for s in POLICY_SECTIONS}
    for p in load_policies():
        body = render_policy(p["body"])
        if p["download"]:
            body += f'\n<p><a class="btn btn-small" href="{esc(path_of(p["download"]))}" download>{esc(p["download_label"] or "Download (PDF)")}</a></p>'
        groups.setdefault(p["section"], []).append(
            f'<details class="policy" id="{p["slug"]}" data-title="{esc(p["title"].lower())}">'
            f'<summary>{esc(p["title"])}</summary><div class="policy-body">{body}</div></details>'
        )
    return "\n".join(
        f'<section class="policy-group" aria-labelledby="g-{i}"><h2 id="g-{i}" class="group-title">{esc(g)}</h2>{"".join(its)}</section>'
        for i, (g, its) in enumerate((g, its) for g, its in groups.items() if its)
    )


def policy_nav():
    groups = {s: [] for s in POLICY_SECTIONS}
    for p in load_policies():
        groups.setdefault(p["section"], []).append(p)
    return "".join(f'<a href="#g-{i}">{esc(g)}</a>' for i, g in enumerate(g for g, its in groups.items() if its))


# ---------- Policy acknowledgement on the registration form ----------
def policy_ack():
    su = load("signup.json", {})
    pols = {p["slug"]: p for p in load_policies()}
    cards = []
    for i, c in enumerate([c for c in su.get("cards") or [] if isinstance(c, dict) and c.get("heading")], 1):
        head = c["heading"]
        full = "".join(
            f'<details class="ack-doc" data-policy="{esc(pols[s]["title"])}"><summary>{esc(pols[s]["title"])}</summary>'
            f'<div class="ack-doc-body">{render_policy(pols[s]["body"])}</div></details>'
            for s in c.get("policies") or [] if s in pols
        )
        points = "".join(f"<li>{md(p)}</li>" for p in c.get("points") or [] if str(p).strip())
        cards.append(
            f'<div class="ack-card"><h3><span class="ack-n">{i}</span>{esc(head)}</h3>'
            f'<ul class="ack-points">{points}</ul>'
            + (f'<p class="ack-read">Read the full text:</p><div class="ack-docs">{full}</div>' if full else "")
            + f'<label class="check ack-check"><input type="checkbox" name="Agreed: {esc(head)}" value="Yes" required> '
            f'I have read the {esc(head.lower())} and agree to them.</label></div>'
        )
    return (
        f'<input type="hidden" name="Policy version" value="{esc(su.get("policy_version", ""))}">'
        '<input type="hidden" name="Agreed at" value="" data-ack-time>'
        '<input type="hidden" name="Full policies opened" value="None" data-ack-opened>'
        + "".join(cards)
    )


# ---------- Layout: contact and socials ----------
SOCIAL_ICONS = {
    "instagram": ("Instagram", '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.5" cy="6.5" r="1.3" fill="currentColor"/></svg>'),
    "facebook": ("Facebook", '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path fill="currentColor" d="M13.5 21v-7.5h2.6l.4-3h-3V8.6c0-.9.3-1.5 1.5-1.5h1.6V4.4c-.3 0-1.2-.1-2.3-.1-2.3 0-3.9 1.4-3.9 4v2.2H7.8v3h2.6V21h3.1z"/></svg>'),
    "youtube": ("YouTube", '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path fill="currentColor" d="M21.6 7.2a2.5 2.5 0 0 0-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4A2.5 2.5 0 0 0 2.4 7.2 26 26 0 0 0 2 12a26 26 0 0 0 .4 4.8 2.5 2.5 0 0 0 1.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4a2.5 2.5 0 0 0 1.8-1.8A26 26 0 0 0 22 12a26 26 0 0 0-.4-4.8zM10 15V9l5.2 3-5.2 3z"/></svg>'),
    "x": ("X", '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M17.8 3h3.1l-6.8 7.7 8 10.3h-6.2l-4.9-6.3L5.4 21H2.3l7.2-8.2L1.8 3h6.4l4.4 5.8L17.8 3zm-1.1 16.2h1.7L7.4 4.7H5.5l11.2 14.5z"/></svg>'),
    "tiktok": ("TikTok", '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path fill="currentColor" d="M16.6 3c.4 2.2 1.8 3.7 4 4v3.1c-1.5 0-2.9-.4-4-1.2v6.3a5.8 5.8 0 1 1-5.8-5.8c.3 0 .6 0 .9.1v3.2a2.7 2.7 0 1 0 1.9 2.6V3h3z"/></svg>'),
}


def socials():
    s = setting("socials", default={})
    lis = "".join(
        f'\n          <li><a href="{esc(s[k])}" target="_blank" rel="noopener" aria-label="Futuro on {label}">{svg}</a></li>'
        for k, (label, svg) in SOCIAL_ICONS.items() if isinstance(s, dict) and str(s.get(k) or "").strip()
    )
    return f'<ul class="socials" aria-label="Follow Futuro">{lis}\n        </ul>'


def x_handle():
    x = str(setting("socials", "x", default="https://x.com/parmarsports"))
    return "@" + x.rstrip("/").rsplit("/", 1)[-1]


def tel():
    return "+1" + re.sub(r"\D", "", setting("contact", "phone"))[-10:]


# ---------- Page assembly ----------
def nav(current):
    cur = ' aria-current="page"'
    links = "".join(
        f'<a href="{href}"{cur if href == current else ""}>{label}</a>' for href, label in NAV
    )
    return links + '<a class="btn btn-primary" href="register.html">Register for Tryouts</a>'


def main():
    SETTINGS.update(load("settings.json", {}))
    email = setting("contact", "email", default="sanjeev@parmarsportstraining.com")
    layout = (SRC / "layout.html").read_text()
    # cache-busting: browsers refetch CSS/JS whenever their contents change
    for key, f in (("v_css", "styles.css"), ("v_js", "main.js")):
        layout = layout.replace("{{" + key + "}}", hashlib.md5((ROOT / f).read_bytes()).hexdigest()[:8])
    parts = {
        "announcement": announcement, "collage": collage, "hero_headline": hero_headline, "hero_subtitle": hero_subtitle,
        "hero_stats": hero_stats, "success_stats": success_stats, "sponsors": sponsors, "sponsor_grid": sponsor_grid,
        "policies": policies, "policy_nav": policy_nav, "graduates": graduates, "grads_home": grads_home,
        "coach_carousel": coach_carousel, "staff_carousel": staff_carousel, "coach_count": coach_count,
        "season_calendar": season_calendar, "programs_table": programs_table, "policy_ack": policy_ack,
        "legends_home": legends_home, "legends_grid": legends_grid, "alumni_wall": alumni_wall,
        "commitments": commitments, "commitment_total": commitment_total,
        "latest_class": latest_class, "latest_class_year": latest_class_year, "reels": reels, "gallery": gallery,
        "socials": socials, "x_handle": x_handle, "tel": tel,
        "x_url": lambda: esc(setting("socials", "x", default="https://x.com/parmarsports")),
        "phone": lambda: esc(setting("contact", "phone")),
        "contact_name": lambda: esc(setting("contact", "name")),
    }
    cache = {}
    for page in sorted((SRC / "pages").glob("*.html")):
        raw = page.read_text()
        meta = dict(re.findall(r"^<!--\s*(\w+):\s*(.*?)\s*-->", raw, re.M))
        body = re.sub(r"^<!--\s*\w+:.*?-->\n", "", raw, flags=re.M)
        out = (
            layout.replace("{{title}}", esc(meta.get("title", "Futuro Soccer Academy")))
            .replace("{{description}}", esc(meta.get("description", "")))
            .replace("{{body_class}}", meta.get("body_class", ""))
            .replace("{{nav}}", nav(page.name))
            .replace("{{body}}", body)
        )
        for key, fn in parts.items():
            if "{{" + key + "}}" in out:
                if key not in cache:
                    cache[key] = fn()
                out = out.replace("{{" + key + "}}", cache[key])
        out = (
            out.replace("{{form_endpoint}}", f"https://formsubmit.co/{email}")
            .replace("{{site_url}}", SITE_URL)
            .replace("{{email}}", esc(email))
        )
        left = re.findall(r"\{\{\s*\w+\s*\}\}", out)
        if left:
            warn(f"{page.name}: unknown placeholders {sorted(set(left))}")
        (ROOT / page.name).write_text(out)
        print("built", page.name)
    if WARNINGS:
        print(f"\n{len(WARNINGS)} warning(s): the site was built, but check the entries above.", file=sys.stderr)


if __name__ == "__main__":
    main()
