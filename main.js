const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Header: transparent at the top, frosted once the page scrolls
const nav = document.getElementById('nav');
const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 24);
onScroll();
window.addEventListener('scroll', onScroll, { passive: true });

// Mobile menu
const toggle = document.querySelector('.nav-toggle');
const links = document.getElementById('nav-links');
const setMenu = (open) => {
  links.classList.toggle('open', open);
  nav.classList.toggle('menu-open', open);
  toggle.setAttribute('aria-expanded', String(open));
};
toggle.addEventListener('click', () => setMenu(!links.classList.contains('open')));
links.addEventListener('click', (e) => { if (e.target.closest('a')) setMenu(false); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setMenu(false); });

// Carousels: swipe natively; buttons step one card, the counter tracks position
document.querySelectorAll('[data-carousel]').forEach((car) => {
  const track = car.querySelector('.carousel-track');
  const slides = [...track.children];
  const [prev, next] = car.querySelectorAll('.car-btn');
  const count = car.querySelector('.car-count');
  const step = () => slides[1] ? slides[1].offsetLeft - slides[0].offsetLeft : track.clientWidth;
  const update = () => {
    const i = Math.round(track.scrollLeft / step());
    const visible = Math.max(1, Math.round(track.clientWidth / step()));
    const last = Math.min(slides.length, i + visible);
    count.textContent = visible > 1 ? `${i + 1}–${last} / ${slides.length}` : `${i + 1} / ${slides.length}`;
    prev.disabled = track.scrollLeft < 4;
    next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 4;
  };
  [prev, next].forEach((b) => b.addEventListener('click', () => {
    track.scrollBy({ left: Number(b.dataset.dir) * step(), behavior: reduce ? 'auto' : 'smooth' });
  }));
  track.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      e.preventDefault();
      (e.key === 'ArrowRight' ? next : prev).click();
    }
  });
  let raf;
  track.addEventListener('scroll', () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(update); }, { passive: true });
  window.addEventListener('resize', update);
  update();
  // coaches.html#name: bring that coach's card into view
  let target = null;
  try { target = location.hash && track.querySelector(location.hash); } catch (e) { /* not a valid selector */ }
  if (target) {
    track.scrollLeft = target.offsetLeft - slides[0].offsetLeft;
    car.scrollIntoView({ block: 'start' });
  }
});

// Success stories filter
const filterButtons = document.querySelectorAll('.filters button');
if (filterButtons.length) {
  const alumni = document.querySelectorAll('#alumni-grid .alum');
  const uniClasses = document.querySelector('.uni-classes');
  filterButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const f = btn.dataset.filter;
      filterButtons.forEach((b) => b.setAttribute('aria-pressed', String(b === btn)));
      alumni.forEach((a) => { a.hidden = f !== 'all' && a.dataset.cat !== f; });
      if (uniClasses) uniClasses.hidden = !(f === 'all' || f === 'university');
    });
  });
}

// Click-to-load YouTube (keeps pages fast)
document.querySelectorAll('.video[data-yt]').forEach((v) => {
  v.addEventListener('click', () => {
    if (v.classList.contains('playing')) return;
    const iframe = document.createElement('iframe');
    iframe.src = `https://www.youtube-nocookie.com/embed/${v.dataset.yt}?autoplay=1&rel=0`;
    iframe.title = v.textContent.trim() || 'YouTube video';
    iframe.allow = 'autoplay; encrypted-media; picture-in-picture';
    iframe.allowFullscreen = true;
    v.classList.add('playing');
    v.appendChild(iframe);
  });
});

// Policies: search + open the policy named in the URL hash
const search = document.getElementById('policy-search');
if (search) {
  const items = document.querySelectorAll('.policy');
  const groups = document.querySelectorAll('.policy-group');
  const empty = document.getElementById('no-results');
  search.addEventListener('input', () => {
    const q = search.value.trim().toLowerCase();
    let shown = 0;
    items.forEach((d) => {
      const hit = !q || d.dataset.title.includes(q) || d.textContent.toLowerCase().includes(q);
      d.hidden = !hit;
      if (hit) shown++;
    });
    groups.forEach((g) => { g.hidden = !g.querySelector('.policy:not([hidden])'); });
    empty.hidden = shown > 0;
  });
  const openFromHash = () => {
    const el = location.hash && document.getElementById(location.hash.slice(1));
    if (el && el.tagName === 'DETAILS') { el.open = true; el.scrollIntoView({ block: 'start' }); }
  };
  openFromHash();
  window.addEventListener('hashchange', openFromHash);
}

// Training reels (always muted): load and play all of them while the section is near the screen,
// so swiping is seamless; pause when far away. Tap a reel to pause or resume it.
(() => {
  const vids = [...document.querySelectorAll('.reel video')];
  if (!vids.length) return;
  const track = vids[0].closest('.carousel-track') || vids[0].closest('.reels');
  const held = new Set();
  let near = false;
  const start = v => { v.muted = true; const p = v.play(); if (p) p.catch(() => {}); };
  const warm = () => vids.forEach(v => { if (v.preload !== 'auto') { v.preload = 'auto'; v.load(); } });
  const playAll = () => { if (near) vids.forEach(v => { if (!held.has(v) && v.paused) start(v); }); };
  vids.forEach(v => {
    v.muted = true; v.defaultMuted = true;
    v.addEventListener('click', () => {
      if (v.paused) { held.delete(v); start(v); } else { held.add(v); v.pause(); }
    });
    v.addEventListener('canplay', () => { if (near && !held.has(v) && v.paused) start(v); });
  });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(([e]) => {
      near = e.isIntersecting;
      if (near) { warm(); playAll(); } else vids.forEach(v => v.pause());
    }, { rootMargin: '1200px 0px' }).observe(track);
  } else { near = true; warm(); playAll(); }
  // Some phones (e.g. iPhone Low Power Mode) block autoplay until the first touch anywhere
  ['touchstart', 'pointerdown', 'scroll'].forEach(ev => window.addEventListener(ev, playAll, { passive: true }));
})();

// Season calendar: highlight this month and say what's on now.
document.querySelectorAll('[data-season-cal]').forEach(cal => {
  const m = new Date().getMonth();             // 0 = Jan
  const i = (m - 8 + 12) % 12 + 1;              // column, season starts in Sep
  const name = new Date(2000, m, 1).toLocaleString('en-CA', { month: 'long' });
  const phase = i <= 6 ? 'the Fall / Winter phase' : 'the Spring / Summer phase';
  const camp = (m === 6 || m === 7) ? ' and summer camp are' : ' is';
  cal.style.setProperty('--now', i);
  cal.classList.add('has-now');
  const cell = cal.querySelector(`.cal-months [data-i="${i}"]`);
  if (cell) cell.classList.add('is-now');
  const txt = cal.querySelector('[data-cal-now]');
  if (txt) txt.textContent = `It's ${name}: ${phase}${camp} on, and players can join now.`;
});

// Registration policy acknowledgement: typed signature must match the guardian name;
// record when they agreed and which full policies they opened (sent with the form).
document.querySelectorAll('form').forEach(form => {
  const sign = form.querySelector('[data-sign-for]');
  if (!sign) return;
  const nameEl = form.querySelector('#' + sign.dataset.signFor);
  const norm = s => s.trim().replace(/\s+/g, ' ').toLowerCase();
  const check = () => sign.setCustomValidity(sign.value && nameEl && norm(sign.value) !== norm(nameEl.value) ? 'Type the same full name you entered above.' : '');
  sign.addEventListener('input', check); if (nameEl) nameEl.addEventListener('input', check);
  const opened = new Set();
  form.querySelectorAll('details[data-policy]').forEach(d => d.addEventListener('toggle', () => { if (d.open) opened.add(d.dataset.policy); }));
  form.addEventListener('submit', () => {
    check();
    const t = form.querySelector('[data-ack-time]'); if (t) t.value = new Date().toString();
    const o = form.querySelector('[data-ack-opened]'); if (o) o.value = opened.size ? [...opened].join(', ') : 'None';
  });
});
