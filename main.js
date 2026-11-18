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

// Scroll reveal + count-up
const countUp = (el) => {
  const target = Number(el.dataset.count);
  const suffix = el.dataset.suffix || '';
  if (reduce) { el.textContent = target + suffix; return; }
  const start = performance.now();
  const step = (t) => {
    const p = Math.min(1, (t - start) / 1200);
    el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3))) + suffix;
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
};

if ('IntersectionObserver' in window) {
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      e.target.classList.add('in');
      if (e.target.dataset.count) countUp(e.target);
      io.unobserve(e.target);
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('.reveal, [data-count]').forEach((el) => io.observe(el));
} else {
  document.querySelectorAll('.reveal').forEach((el) => el.classList.add('in'));
}
