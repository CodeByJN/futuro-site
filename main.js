// Mobile nav
const toggle = document.querySelector('.nav-toggle');
const links = document.getElementById('nav-links');
toggle.addEventListener('click', () => {
  const open = links.classList.toggle('open');
  toggle.setAttribute('aria-expanded', String(open));
});
links.addEventListener('click', (e) => {
  if (e.target.closest('a')) {
    links.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
  }
});

// Alumni filter
const filterButtons = document.querySelectorAll('.filters button');
const alumni = document.querySelectorAll('#alumni-grid .alum');
const uniClasses = document.querySelector('.uni-classes');
filterButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    const f = btn.dataset.filter;
    filterButtons.forEach((b) => b.setAttribute('aria-pressed', String(b === btn)));
    alumni.forEach((a) => { a.hidden = f !== 'all' && a.dataset.cat !== f; });
    uniClasses.hidden = !(f === 'all' || f === 'university');
  });
});

// Click-to-load YouTube (keeps the page fast)
document.querySelectorAll('.video').forEach((v) => {
  v.addEventListener('click', () => {
    if (v.classList.contains('playing')) return;
    const iframe = document.createElement('iframe');
    iframe.src = `https://www.youtube-nocookie.com/embed/${v.dataset.yt}?autoplay=1&rel=0`;
    iframe.title = v.textContent.trim();
    iframe.allow = 'autoplay; encrypted-media; picture-in-picture';
    iframe.allowFullscreen = true;
    v.classList.add('playing');
    v.appendChild(iframe);
  });
});

// Scroll reveal + stat count-up
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const countUp = (el) => {
  const target = Number(el.dataset.count);
  const suffix = el.dataset.suffix || '';
  if (reduce) { el.textContent = target + suffix; return; }
  const start = performance.now();
  const dur = 1100;
  const step = (t) => {
    const p = Math.min(1, (t - start) / dur);
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
  }, { threshold: 0.15 });
  document.querySelectorAll('.reveal, [data-count]').forEach((el) => io.observe(el));
} else {
  document.querySelectorAll('.reveal').forEach((el) => el.classList.add('in'));
}
