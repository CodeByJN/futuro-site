# Futuro Site

A redesign of the Futuro Soccer Academy website (Ottawa). The current site is at https://www.futurosoccer.com.

The current site spreads its best content across 55+ pages: 11 separate "Achievements" and "University Grads" pages, most of it locked inside poster images, plus 25 policy pages in the main menu. This version is a single focused page, ordered the way a parent decides:

1. **Hero + numbers**: 24 pro and pro-academy signings, 13 national-team call-ups, 60+ university commitments, 2 CPL champions
2. **Futuro Legends**: Noah Abatneh, Sadie Sider-Echenberg, Antoine Coupland, Maya Hindson, Elage Bah, Tyr Duhaney-Walker, Eric Lajeunesse, Molly Hale, Michael Peres
3. **Where they are now**: a filterable wall (Pro / National team / University) and every university commitment by graduating class
4. **Proof on the pitch**: UK tour results vs. English pro academies, plus YouTube highlights
5. **The Futuro Standard**: what parents should expect (high intensity, elite technical skill, education standards)
6. **Coaches**, **Programs pathway**, **Tryout CTA**
7. Policies and parent resources go in the footer and link to the existing pages

## Run locally

Plain static HTML/CSS/JS with no build step.

```sh
python3 -m http.server 8000
# open http://localhost:8000
```

Deploy anywhere that serves static files (GitHub Pages, Netlify, Cloudflare Pages).

## Data notes

- All facts come from the current futurosoccer.com pages and the academy's own announcement posters, as of November 2026.
- The headline counts were tallied from that content. Have the academy confirm them before launch.
- The university-recruitment page on the current site publishes minors' emails and birthdates. This redesign deliberately leaves them out.
