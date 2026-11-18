# Futuro Site

A redesign of the Futuro Soccer Academy website (Ottawa). The current site is at https://www.futurosoccer.com.

Live preview: https://codebyjn.github.io/futuro-site/

## Pages

| Page | What it's for |
|---|---|
| `index.html` | Home: hero with the looping player collage and headline numbers, sponsor carousel (with a "see all" grid), success stories and current graduates, philosophy, coaches carousel, "The Futuro experience" photo mosaic, the program, when to apply and policies |
| `about.html` | Mission, vision, Joga Bonito philosophy, the 7 pillars, and results against English pro academies (with videos) |
| `success.html` | Futuro Legends, the filterable "where they are now" wall, and every university commitment by class |
| `coaches.html` | Swipeable carousel of all 10 staff with photos and credentials |
| `program.html` | A typical week, the standard, the U8–U18 pathway and the summer camp |
| `apply.html` | How to join, season phases, age groups by birth year, financial assistance |
| `register.html` | Tryout registration form |
| `graduates.html` | Showcase board for scouts and the highlight-tape submission form |
| `policies.html` | All 23 policies on one searchable page |

## Editing

The pages are generated. **Edit the files in `src/`, then run:**

```sh
python3 build.py
```

- `src/layout.html` is the shared header and footer.
- `src/pages/*.html` holds each page's content.
- `src/policies/*.txt` holds the policy text, taken from the current site.
- `src/coaches.json` holds the coaches, in display order. It feeds the home page carousel and the coaches page.
- `src/graduates.json` holds the players on the graduates board.
- `assets/video/reel-N.mp4` (+ `.webp` posters) are Coach Parmar's training clips from X, shown as a reel carousel in the home philosophy section. To add one, encode it to 540x960 and copy a `<figure class="reel slide">` block in `src/pages/index.html`.
- The coach inquiry form ("Coach with Futuro") is at `coaches.html#coach-with-us` and sends to the same inbox as the tryout form.
- CSS and JS links get a `?v=` content hash at build time, so visitors always load the latest version.
- `assets/img/action/` holds the training and match photos (from the current futurosoccer.com). Inner pages set their header photo with `style="--hero-img:url(...)"` on `.page-hero.has-photo`.
- Sponsors, the nav and the form inbox are set at the top of `build.py`.

Preview locally:

```sh
python3 -m http.server 8000
# open http://localhost:8000
```

### Adding a player to the graduates board

After Coach Parmar approves a submission, add an entry to `src/graduates.json` and rebuild:

```json
[
  {
    "name": "Jane Doe",
    "grad_year": 2026,
    "position": "Centre-back",
    "team": "Women's Competitive 1",
    "youtube": "https://youtu.be/VIDEO_ID",
    "note": "Left-footed, strong in the air"
  }
]
```

Only these fields are published. Scouts contact the academy through the button on each card.

## Forms

The tryout and highlight-tape forms send to the academy inbox through [FormSubmit](https://formsubmit.co). This needs no account and no server code.

- **The first time someone submits a form, FormSubmit emails the inbox an activation link. Click it once, or later submissions won't be delivered.**
- After submitting, people land on `thanks.html`.
- To use a different service, such as Formspree or a Google Form, change `FORM_ENDPOINT` in `build.py`.

## Data notes

- All facts come from the current futurosoccer.com pages and the academy's announcement posters, as of November 2026.
- The headline counts were tallied from that content. Have the academy confirm them before launch:
  - 85+ success stories (unique players)
  - 24 pro or pro-academy signings
  - 13 national-team call-ups
  - 60+ university commitments
- The university-recruitment page on the current site publishes minors' emails and birthdates. This redesign leaves them out.
