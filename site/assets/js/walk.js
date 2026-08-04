/* Studio Walk — horizontaler Rundgang, Zonen-Karte, Datenblatt-Schublade, Präsentation. */
(function () {
  'use strict';
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var stacked = function () { return reduce || matchMedia('(max-width: 900px)').matches; };

  var walk = document.getElementById('walk');
  var track = walk && walk.querySelector('.track');
  var zones = Array.prototype.slice.call(document.querySelectorAll('.zone'));
  var dots = Array.prototype.slice.call(document.querySelectorAll('.map button'));
  var Z = zones.length;

  /* ---------- horizontaler Walk (Desktop) ---------- */
  var maxX = 0;
  function measure() {
    if (!track) return;
    maxX = Math.max(0, track.scrollWidth - innerWidth);
  }
  function progress() {
    var r = walk.getBoundingClientRect();
    var total = walk.offsetHeight - innerHeight;
    return Math.max(0, Math.min(1, -r.top / total));
  }
  var activeZ = -1;
  function setActive(i) {
    if (i === activeZ) return;
    activeZ = i;
    zones.forEach(function (z, k) { z.classList.toggle('on', k === i); });
    dots.forEach(function (d, k) { d.classList.toggle('on', k === i); });
    zones.forEach(function (z, k) {
      z.querySelectorAll('video').forEach(function (v) {
        if (reduce) return;
        if (k === i) { v.play().then(function () { v.closest('.item').classList.add('playing'); }).catch(function () {}); }
        else { v.pause(); var it = v.closest('.item'); if (it) it.classList.remove('playing'); }
      });
    });
  }
  var tick = null;
  function onScroll() {
    if (tick) return;
    tick = requestAnimationFrame(function () {
      tick = null;
      if (!walk) return;
      var r = walk.getBoundingClientRect();
      var inwalk = r.top < innerHeight * 0.5 && r.bottom > innerHeight * 0.5;
      document.body.classList.toggle('inwalk', inwalk);
      if (stacked()) {
        if (!inwalk) return;
        var y = scrollY + innerHeight * 0.5, best = 0;
        zones.forEach(function (z, k) { if (z.getBoundingClientRect().top + scrollY <= y) best = k; });
        setActive(best);
        return;
      }
      var p = progress();
      track.style.transform = 'translateX(' + (-p * maxX) + 'px)';
      zones.forEach(function (z) {
        var w = z.querySelector('.wall');
        if (w) w.style.transform = 'translateX(calc(-50% + ' + (p * maxX * 0.06) + 'px))';
      });
      if (inwalk) setActive(Math.min(Z - 1, Math.floor(p * Z + 0.0001)));
    });
  }
  addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', function () { measure(); onScroll(); });
  measure(); onScroll();

  function scrollToZone(i) {
    i = Math.max(0, Math.min(Z - 1, i));
    if (stacked()) { zones[i].scrollIntoView({ behavior: reduce ? 'auto' : 'smooth' }); return; }
    var total = walk.offsetHeight - innerHeight;
    var y = walk.offsetTop + total * ((i + 0.5) / Z);
    scrollTo({ top: y, behavior: reduce ? 'auto' : 'smooth' });
  }
  dots.forEach(function (d) {
    d.addEventListener('click', function () { scrollToZone(parseInt(d.dataset.go, 10)); });
  });

  /* ---------- Datenblatt-Schublade ---------- */
  var drawer = document.getElementById('drawer');
  var dbody = document.getElementById('d-body');
  var lastFocus = null;
  function openSheet(sid, trigger) {
    var tpl = document.getElementById('sheet-' + sid);
    if (!tpl || !drawer) return;
    dbody.innerHTML = '';
    dbody.appendChild(tpl.content.cloneNode(true));
    drawer.classList.add('open');
    drawer.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    lastFocus = trigger || document.activeElement;
    var c = drawer.querySelector('.d-close');
    if (c) c.focus();
  }
  function closeSheet() {
    if (!drawer.classList.contains('open')) return;
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-sheet]');
    if (t) { openSheet(t.dataset.sheet, t); return; }
    if (e.target.closest('[data-close]')) closeSheet();
  });

  /* ---------- Tastatur & Präsentation ---------- */
  var wake = null, idleT = null;
  function requestWake() {
    if (navigator.wakeLock) navigator.wakeLock.request('screen').then(function (w) { wake = w; }).catch(function () {});
  }
  function present(on) {
    document.body.classList.toggle('presenting', on);
    if (on) {
      if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen({ navigationUI: 'hide' }).catch(function () {});
      requestWake();
      scrollToZone(Math.max(0, activeZ));
    } else {
      if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen().catch(function () {});
      if (wake) { wake.release().catch(function () {}); wake = null; }
      document.body.classList.remove('black', 'idle');
    }
  }
  document.addEventListener('fullscreenchange', function () {
    if (!document.fullscreenElement && document.body.classList.contains('presenting')) present(false);
  });
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden && document.body.classList.contains('presenting')) requestWake();
  });
  var pbtn = document.getElementById('present');
  if (pbtn) pbtn.addEventListener('click', function () { present(true); });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeSheet(); if (document.body.classList.contains('presenting')) present(false); return; }
    if (drawer && drawer.classList.contains('open')) return;
    var p = document.body.classList.contains('presenting');
    if ((e.key === 'f' || e.key === 'F') && !e.metaKey && !e.ctrlKey) { if (!p) { e.preventDefault(); present(true); } return; }
    if (!p && !document.body.classList.contains('inwalk')) return;
    switch (e.key) {
      case 'ArrowRight': case 'PageDown': e.preventDefault(); scrollToZone(activeZ + 1); break;
      case 'ArrowLeft': case 'PageUp': e.preventDefault(); scrollToZone(activeZ - 1); break;
      case 'Home': if (p) { e.preventDefault(); scrollToZone(0); } break;
      case 'End': if (p) { e.preventDefault(); scrollToZone(Z - 1); } break;
      case '.': if (p) { e.preventDefault(); document.body.classList.toggle('black'); } break;
    }
  });
  document.addEventListener('mousemove', function () {
    if (!document.body.classList.contains('presenting')) return;
    document.body.classList.remove('idle');
    clearTimeout(idleT);
    idleT = setTimeout(function () { document.body.classList.add('idle'); }, 3000);
  });

  /* Fallback: gestapelte Videos spielen im Sichtfeld */
  if (stacked() && !reduce && 'IntersectionObserver' in window) {
    var vio = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        var v = e.target;
        if (e.isIntersecting && e.intersectionRatio > 0.5) v.play().catch(function () {});
        else v.pause();
      });
    }, { threshold: [0, 0.5] });
    document.querySelectorAll('.zone video').forEach(function (v) { vio.observe(v); });
  }
})();
