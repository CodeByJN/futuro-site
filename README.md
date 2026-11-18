# Futuro Site

A redesign of the Futuro Soccer Academy website (Ottawa). The current site is at https://www.futurosoccer.com.

Live preview: https://codebyjn.github.io/futuro-site/

## Pages

| Page | What it's for |
|---|---|
| `index.html` | Home: hero with the looping player collage and headline numbers, sponsors, legends and the scouting showcase, philosophy and training videos, coaches and coach recruiting, the photo mosaic, the program, the season calendar and policies |
| `about.html` | Mission, vision, Joga Bonito philosophy, the 7 pillars, and results against English pro academies (with videos) |
| `success.html` | Futuro Legends, then every achievement year by year (filter by pro, national team or university) |
| `coaches.html` | Swipeable carousel of all 10 staff with photos and credentials |
| `program.html` | A typical week, the standard, the U8–U18 pathway and the summer camp |
| `apply.html` | How to join, season phases, age groups by birth year, financial assistance |
| `register.html` | Tryout registration form |
| `graduates.html` | Showcase board for scouts (highlight tapes added by the academy) and the latest class's commitments |
| `policies.html` | All 23 policies on one searchable page |

## Editing

### For the academy: Pages CMS

The academy updates the site in **Pages CMS** (https://app.pagescms.org). It's a free editor with plain forms and photo uploads, and no code. Each save goes live in about a minute. The editor's sections are defined in `.pages.yml`:

| Section | Edits | File |
|---|---|---|
| Site settings | Announcement banner, home headline and numbers, Success page numbers, contact details, social links | `content/settings.json` |
| Graduates board | Graduating players and their YouTube highlight links | `content/graduates.json` |
| Futuro legends | The big player stories (Success page, and the home carousel) | `content/legends.json` |
| Achievements | Every pro, national-team and university achievement with its year. It becomes the year-by-year timeline on the Success page, with filters. University entries also feed the home and graduates pages. | `content/achievements.json` |
| Coaches | Staff cards (home carousel and Coaches page) | `content/coaches.json` |
| Training videos | The vertical clips on the home page | `content/videos.json` |
| Home page photos | "The Futuro experience" mosaic (it lays itself out for any number of photos) | `content/gallery.json` |
| Sponsors | Logos in the sponsor strip | `content/sponsors.json` |
| Programs and age groups | The table on the apply page (update birth years each season) | `content/programs.json` |
| Season calendar | The Sept–Aug calendar bars | `content/season.json` |
| Sign-up agreement | The rules parents agree to on the tryout form | `content/signup.json` |
| Policies | One plain-text page per policy | `content/policies/*.md` |

The "Home page photo wall" media folder (`assets/img/collage/`) feeds the moving collage behind the home headline.

Uploads go to `assets/uploads/`. At build time, photos (including iPhone .heic) are resized to WebP, and videos (including .mov) are compressed to 540px-wide silent MP4s with a cover frame. The results go in `assets/opt/`, which isn't committed.

**Setup (one time):** sign in at app.pagescms.org with the GitHub account that owns this repo, and install the Pages CMS GitHub App on the repo. Then open the repo, go to **Collaborators** and invite the academy's email. Collaborators don't need a GitHub account.

### Preview, then publish

The editor saves to the `preview` branch, which is the repo's default branch, so Pages CMS opens it automatically. Each save rebuilds the site, and the preview copy appears at https://codebyjn.github.io/futuro-site/preview/ with a yellow "Preview" bar. Google is told not to index it.

On the editor's **Actions** page there are two buttons:
- **Publish to the live site** (`publish.yml`) merges `preview` into `main` and republishes.
- **Undo all unpublished changes** (`discard.yml`) resets `preview` to match `main`.

Design changes pushed to `main` are merged into `preview` automatically on the next build.

### How it publishes

`.github/workflows/deploy.yml` runs on every push to `main` or `preview`, and builds both: `main` at the site root and `preview` at `/preview/`. It installs Pillow and ffmpeg, runs `python build.py`, and publishes to GitHub Pages. The generated `*.html` files are not committed.

If an entry is missing a required field, the build skips it with a warning in the Actions log. The rest of the site still publishes. If a build fails completely, the previous version stays live.

### For developers

- `src/layout.html` is the shared header and footer. `src/pages/*.html` are the page templates. `{{placeholders}}` are filled from `content/` by `build.py`.
- Run `python3 build.py` to build locally, then `python3 -m http.server 8000` to preview.
- CSS and JS links get a `?v=` content hash at build time, so visitors always load the latest version.
- Inner pages set their header photo with `style="--hero-img:url(...)"` on `.page-hero.has-photo`.

## Forms

The tryout and coach inquiry forms send to the academy inbox through [FormSubmit](https://formsubmit.co). This needs no account and no server code.

- **The first time someone submits a form, FormSubmit emails the inbox an activation link. Click it once, or later submissions won't be delivered.**
- After submitting, people land on `thanks.html`.
- The tryout form ends with a **Standards & policies** step. Parents must tick three summary cards (player standards, parent standards, safety & refunds), agree to all club policies, and type their name to sign. The full policy text expands inline. The emailed registration records each agreement, the policy version, the time they agreed and which full policies they opened, so keep those emails. The summaries and the policy version are in the "Sign-up agreement" section of the editor (`content/signup.json`). Update them whenever a policy changes.
- The inbox is the contact email in Site settings.

## Data notes

- All facts come from the current futurosoccer.com pages and the academy's announcement posters, as of November 2026.
- The headline counts were tallied from that content. Have the academy confirm them before launch:
  - 100+ achievements (108 documented in `content/achievements.json`, by 87 players)
  - 24 pro or pro-academy signings
  - 13 national-team call-ups
  - 60+ university commitments
- The university-recruitment page on the current site publishes minors' emails and birthdates. This redesign leaves them out.
