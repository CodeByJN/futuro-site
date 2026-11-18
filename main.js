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

// Training reels: preload and play all of them while the section is near the screen, so swiping
// is seamless. One shared sound setting: unmuting any reel unmutes them all (reels you can see).
(() => {
  const vids = [...document.querySelectorAll('.reel video')];
  if (!vids.length) return;
  const track = vids[0].closest('.carousel-track') || vids[0].closest('.reels');
  const btns = vids.map(v => v.parentElement.querySelector('.reel-sound'));
  const held = new Set();
  const inView = new Set();
  let near = false, soundOn = false;
  const start = v => { const p = v.play(); if (p) p.catch(() => {}); };
  vids.forEach(v => { v.muted = true; v.defaultMuted = true; });
  // Start loading every reel once the section is getting close (not on page load)
  const warm = () => vids.forEach(v => { if (v.preload !== 'auto') { v.preload = 'auto'; v.load(); } });
  const applySound = () => {
    vids.forEach(v => { v.muted = !(soundOn && inView.has(v)); });
    btns.forEach(b => { b.setAttribute('aria-pressed', soundOn); b.setAttribute('aria-label', soundOn ? 'Turn sound off' : 'Turn sound on'); });
  };
  const playAll = () => { if (near) vids.forEach(v => { if (!held.has(v) && v.paused) start(v); }); };
  vids.forEach((v, i) => {
    v.addEventListener('click', () => {
      if (v.paused) { held.delete(v); start(v); } else { held.add(v); v.pause(); }
    });
    btns[i].addEventListener('click', () => {
      soundOn = !soundOn; held.delete(v); applySound(); playAll();
    });
    v.addEventListener('canplay', () => { if (near && !held.has(v) && v.paused) start(v); });
  });
  if ('IntersectionObserver' in window) {
    // Section near the screen: load + play everything; far away: pause to save battery
    new IntersectionObserver(([e]) => {
      near = e.isIntersecting;
      if (near) { warm(); playAll(); }
      else { vids.forEach(v => v.pause()); if (soundOn) { soundOn = false; applySound(); } }
    }, { rootMargin: '1200px 0px' }).observe(track);
    // Which reels are actually showing in the strip (sound only comes from those)
    const seen = new IntersectionObserver(entries => {
      entries.forEach(e => e.isIntersecting ? inView.add(e.target) : inView.delete(e.target));
      applySound();
    }, { root: track, threshold: 0.6 });
    vids.forEach(v => seen.observe(v));
  } else { near = true; vids.forEach(v => inView.add(v)); playAll(); }
  // Some phones (e.g. iPhone Low Power Mode) block autoplay until the first touch anywhere
  ['touchstart', 'pointerdown', 'scroll'].forEach(ev => window.addEventListener(ev, playAll, { passive: true }));
})();
