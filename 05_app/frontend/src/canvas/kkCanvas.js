// The interactive SVG canvas: two scenes (plant floor, Impact Web) with pan / zoom / drag / click.
// Framework-free on purpose: React mounts it (SceneCanvas.tsx) and passes a callback for clicks.

const NS = 'http://www.w3.org/2000/svg';
const ST = window.__kkCanvas = window.__kkCanvas || {};
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const COLORS = {critical:'#D62839', warning:'#F2A541', watch:'#F2A541', high:'#F2A541', ok:'#2A9D8F', none:'#8FA3BF'};
const GLYPH = {CNC_MACHINING_CENTER:'⚙', CNC_MILL:'⚙', CNC_LATHE:'◉', GEAR_HOBBER:'✲', PRESS_FIT:'⬇', ASSEMBLY_CELL:'✦',
  TEST_STAND:'✓', PACKAGING:'▣', DEBURR_CELL:'✧', WASH_STATION:'≈', CMM_INSPECTION:'◎', HEAT_TREAT_FURNACE:'♨',
  QUENCH_TANK:'◒', HARDNESS_TESTER:'◆', SAW_CELL:'⟋', ROBOTIC_WELDER:'⚡', PAINT_BOOTH:'◐', SHOT_BLAST:'⁂',
  LEAK_TESTER:'○', CURE_OVEN:'♨', WIRE_CUTTER:'✂', CRIMP_PRESS:'⧗', PULL_TESTER:'⇕', CONTINUITY_TESTER:'∿',
  SMT_PLACER:'⌗', REFLOW_OVEN:'♨', AOI_INSPECTION:'◎', WIRE_DRAWER:'∿', COLD_HEADER:'⬢', THREAD_ROLLER:'⟳',
  OPTICAL_SORTER:'◎', COIL_FEEDER:'◍', STAMPING_PRESS:'⬇', PLATING_TANK:'◒'};

function el(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}

// ---------- camera: viewBox animation, drag-to-pan, wheel zoom ----------
function camera(svg, state, full) {
  const set = (vb) => { state.vb = vb; svg.setAttribute('viewBox', vb.map(v => v.toFixed(1)).join(' ')); };
  const fly = (to, ms = 700) => {
    const from = state.vb || full, t0 = performance.now();
    const ease = (t) => t < .5 ? 4*t*t*t : 1 - Math.pow(-2*t + 2, 3)/2;
    const step = (now) => {
      const t = Math.min(1, (now - t0) / ms), e = ease(t);
      set(from.map((v, i) => v + (to[i] - v) * e));
      if (t < 1) state.raf = requestAnimationFrame(step);
    };
    cancelAnimationFrame(state.raf); state.raf = requestAnimationFrame(step);
  };
  let drag = null;
  svg.addEventListener('pointerdown', (ev) => {
    if (ev.target.closest('.node, .bay-hit, .wnode')) return;
    drag = {x: ev.clientX, y: ev.clientY, vb: [...state.vb]}; svg.classList.add('dragging'); state.moved = true;
    svg.setPointerCapture(ev.pointerId);
  });
  svg.addEventListener('pointermove', (ev) => {
    if (!drag) return;
    const r = svg.getBoundingClientRect(), k = drag.vb[2] / r.width;
    set([drag.vb[0] - (ev.clientX - drag.x) * k, drag.vb[1] - (ev.clientY - drag.y) * k, drag.vb[2], drag.vb[3]]);
  });
  const end = () => { drag = null; svg.classList.remove('dragging'); };
  svg.addEventListener('pointerup', end); svg.addEventListener('pointerleave', end);
  const zoom = (f, cx = .5, cy = .5) => {
    state.moved = true;
    const [x, y, w, h] = state.vb, nw = Math.min(full[2] * 1.6, Math.max(full[2] / 8, w * f)), nh = nw * h / w;
    fly([x + (w - nw) * cx, y + (h - nh) * cy, nw, nh], 220);
  };
  svg.addEventListener('wheel', (ev) => {
    // a plain wheel scrolls the PAGE (the canvas spans the page — hijacking it would trap the user above it);
    // Ctrl/⌘ + wheel, or a trackpad pinch (which browsers report as ctrlKey), zooms the canvas
    if (!(ev.ctrlKey || ev.metaKey)) return;
    ev.preventDefault();
    const r = svg.getBoundingClientRect();
    zoom(ev.deltaY > 0 ? 1.15 : 0.87, (ev.clientX - r.left) / r.width, (ev.clientY - r.top) / r.height);
  }, {passive: false});
  return {set, fly, zoom};
}

function tooltip(root) {
  const tip = document.createElement('div'); tip.className = 'tip'; root.appendChild(tip);
  return {
    show(ev, html, color) {
      tip.innerHTML = html; tip.style.borderTopColor = color || '#0A1F44'; tip.classList.add('show');
      const r = root.getBoundingClientRect();
      let x = ev.clientX - r.left + 16, y = ev.clientY - r.top + 12;
      if (x + 290 > r.width) x -= 310;
      if (y + 160 > r.height) y -= 170;
      tip.style.left = x + 'px'; tip.style.top = y + 'px';
    },
    hide() { tip.classList.remove('show'); },
  };
}

function chrome(root, d) {
  root.insertAdjacentHTML('beforeend',
    `${d.title ? `<div class="hud">${d.eyebrow ? esc(d.eyebrow) + ' ' : ''}<b>${esc(d.title)}</b></div>` : ''}
     <div class="help">${esc(d.help || '')}</div>
     <div class="legend"><span><i style="background:#2A9D8F"></i>Healthy</span><span><i style="background:#F2A541"></i>Watch</span>
       <span><i style="background:#D62839"></i>Critical</span>${d.legendExtra || ''}</div>
     <div class="zoombar"><button data-z="in">+</button><button data-z="out">−</button><button data-z="fit">⤢</button></div>`);
}

// =====================================================================================
// SCENE 1 — PLANT FLOOR
// =====================================================================================
function floor(root, d, setTriggerValue) {
  const W = 1400, BAY_H = 205, TOP = 104, lines = d.lines || [];
  const H = TOP + lines.length * BAY_H + 56;
  const full = [0, 0, W, H];
  const state = ST[d.sceneId] = ST[d.sceneId] || {vb: full};
  const svg = el('svg', {viewBox: state.vb.join(' '), preserveAspectRatio: 'xMidYMid meet'}, root);
  const tip = tooltip(root);
  const defs = el('defs', {}, svg);
  defs.innerHTML = `<filter id="sh" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="6" stdDeviation="7" flood-color="#000" flood-opacity=".35"/></filter>
    <linearGradient id="belt" x1="0" x2="1"><stop offset="0" stop-color="#2A4A82"/><stop offset="1" stop-color="#3B5E9C"/></linearGradient>`;
  const g = el('g', {class: 'grid'}, svg);
  for (let x = 0; x <= W; x += 40) el('line', {x1: x, y1: 0, x2: x, y2: H}, g);
  for (let y = 0; y <= H; y += 40) el('line', {x1: 0, y1: y, x2: W, y2: y}, g);

  // building outline
  el('rect', {x: 150, y: TOP - 34, width: W - 300, height: H - TOP + 14, rx: 18, fill: 'none', stroke: 'rgba(255,255,255,.25)', 'stroke-width': 2, 'stroke-dasharray': '10 6'}, svg);
  const t = el('text', {x: 172, y: TOP - 12, fill: '#B9C6DA', 'font-size': 13, 'font-weight': 700, 'letter-spacing': 2}, svg);
  t.textContent = (d.plantName || '').toUpperCase();

  // docks
  const dock = (x, label, items, side) => {
    const gd = el('g', {class: 'dock'}, svg);
    el('rect', {x, y: TOP - 34, width: 130, height: H - TOP + 14, rx: 14}, gd);
    const tl = el('text', {x: x + 65, y: TOP - 12, fill: '#B9C6DA', 'font-size': 11, 'font-weight': 700, 'text-anchor': 'middle', 'letter-spacing': 1.5}, gd);
    tl.textContent = label;
    const ys = [];
    items.forEach((it, i) => {
      const y = TOP + 20 + i * Math.min(70, (H - TOP - 40) / Math.max(1, items.length));
      ys.push(y + 20);
      const n = el('g', {class: 'node', transform: `translate(${x + 10},${y})`}, gd);
      const c = COLORS[it.status] || COLORS.none;
      if (it.status === 'critical') el('rect', {class: 'pulse', x: 0, y: 0, width: 110, height: 44, rx: 10, fill: 'none', stroke: c, 'stroke-width': 3}, n);
      el('rect', {class: 'card', x: 0, y: 0, width: 110, height: 44, rx: 10, filter: 'url(#sh)'}, n);
      el('rect', {x: 0, y: 0, width: 5, height: 44, rx: 2, fill: c}, n);
      const a = el('text', {x: 12, y: 18, fill: '#0A1F44', 'font-size': 11, 'font-weight': 700}, n); a.textContent = it.label.length > 16 ? it.label.slice(0, 15) + '…' : it.label;
      const b = el('text', {x: 12, y: 33, fill: '#5B6B82', 'font-size': 9.5}, n); b.textContent = (it.sub || '').length > 19 ? it.sub.slice(0, 18) + '…' : (it.sub || '');
      n.addEventListener('mousemove', (ev) => tip.show(ev, `<h5>${esc(it.label)}</h5><div class="k">${esc(it.tip || it.sub || '')}</div>${it.issue ? `<div class="issue">${esc(it.issue)}</div>` : ''}`, c));
      n.addEventListener('mouseleave', () => tip.hide());
      n.addEventListener('click', () => setTriggerValue('select', {kind: it.kind, id: it.id}));
    });
    return ys;
  };
  const inY = dock(10, 'RECEIVING', d.inbound || [], 'in');
  const outY = dock(W - 140, 'SHIPPING', d.outbound || [], 'out');

  lines.forEach((ln, li) => {
    const y0 = TOP + li * BAY_H, cy = y0 + 112;
    const bay = el('g', {class: 'bay' + (d.focusLine === ln.id ? ' focus' : '')}, svg);
    el('rect', {class: 'bg bay-hit', x: 168, y: y0 + 4, width: W - 336, height: BAY_H - 16, rx: 16}, bay);
    const lc = COLORS[ln.status] || COLORS.ok;
    el('rect', {x: 168, y: y0 + 4, width: 6, height: BAY_H - 16, rx: 3, fill: lc}, bay);
    const h1 = el('text', {x: 188, y: y0 + 30, fill: '#FFFFFF', 'font-size': 16, 'font-weight': 800}, bay);
    h1.textContent = `${ln.id}  ·  ${ln.name}`;
    const h2 = el('text', {x: 188, y: y0 + 48, fill: '#B9C6DA', 'font-size': 11.5}, bay);
    h2.textContent = ln.kpis || '';
    if (ln.badge) {
      const bw = 12 + ln.badge.length * 6.4;
      el('rect', {x: W - 176 - bw, y: y0 + 16, width: bw, height: 22, rx: 11, fill: lc}, bay);
      const bt = el('text', {x: W - 176 - bw / 2, y: y0 + 31, fill: '#fff', 'font-size': 11, 'font-weight': 700, 'text-anchor': 'middle'}, bay);
      bt.textContent = ln.badge;
    }
    bay.addEventListener('click', (ev) => { if (!ev.target.closest('.node')) setTriggerValue('select', {kind: 'line', id: ln.id}); });

    // conveyor + nodes
    const n = ln.nodes.length, x0 = 250, x1 = W - 260, NW = 132, NH = 92;
    const xs = ln.nodes.map((_, i) => x0 + (n === 1 ? 0 : i * (x1 - x0) / (n - 1)));
    const path = `M ${x0 - 70} ${cy + 16} L ${x1 + 70} ${cy + 16}`;
    el('path', {class: 'conv', d: path, stroke: 'url(#belt)', 'stroke-width': 14}, bay);
    const speed = Math.max(1.2, 6 - 4 * (ln.flowRate ?? 0.8));
    el('path', {class: 'flow', d: path, stroke: ln.starved ? '#D62839' : '#9CC3FF', 'stroke-width': 5,
                style: `animation-duration:${speed}s`}, bay);
    // material from receiving dock and to shipping dock
    if (inY.length) el('path', {class: 'conv', d: `M 140 ${inY[li % inY.length]} C 175 ${inY[li % inY.length]}, 150 ${cy + 16}, ${x0 - 70} ${cy + 16}`,
                               stroke: ln.starved ? 'rgba(214,40,57,.7)' : 'rgba(156,195,255,.35)', 'stroke-width': 2, 'stroke-dasharray': '4 5'}, bay);
    if (outY.length) el('path', {class: 'conv', d: `M ${x1 + 70} ${cy + 16} C ${W - 150} ${cy + 16}, ${W - 175} ${outY[li % outY.length]}, ${W - 140} ${outY[li % outY.length]}`,
                                stroke: 'rgba(156,195,255,.35)', 'stroke-width': 2, 'stroke-dasharray': '4 5'}, bay);

    ln.nodes.forEach((m, i) => {
      const c = COLORS[m.status] || COLORS.ok;
      const gx = xs[i] - NW / 2, gy = cy - NH / 2 - 6;
      const nd = el('g', {class: 'node' + (d.selected === m.id ? ' sel' : ''), transform: `translate(${gx},${gy})`}, bay);
      if (m.status === 'critical') el('rect', {class: 'pulse', x: -2, y: -2, width: NW + 4, height: NH + 4, rx: 14, fill: 'none', stroke: c, 'stroke-width': 4}, nd);
      el('rect', {class: 'ring', x: -3, y: -3, width: NW + 6, height: NH + 6, rx: 15, fill: 'none', stroke: 'transparent'}, nd);
      el('rect', {class: 'card', x: 0, y: 0, width: NW, height: NH, rx: 12, filter: 'url(#sh)'}, nd);
      el('rect', {x: 0, y: 0, width: NW, height: 6, rx: 3, fill: c}, nd);
      const gl = el('text', {x: 14, y: 34, fill: '#16346B', 'font-size': 20}, nd); gl.textContent = GLYPH[m.type] || '■';
      const id = el('text', {x: 40, y: 24, fill: '#5B6B82', 'font-size': 10, 'font-weight': 700, 'letter-spacing': .6}, nd); id.textContent = m.id.split('-').pop();
      const nm = el('text', {x: 40, y: 38, fill: '#0A1F44', 'font-size': 11.5, 'font-weight': 700}, nd); nm.textContent = (m.short || '').slice(0, 15);
      const mt = el('text', {x: 14, y: 62, fill: m.status === 'critical' ? '#D62839' : '#0A1F44', 'font-size': 13, 'font-weight': 800}, nd); mt.textContent = m.metric || '';
      const ms = el('text', {x: 14, y: 78, fill: '#5B6B82', 'font-size': 9.5}, nd); ms.textContent = m.metricSub || '';
      // criticality badge
      el('circle', {cx: NW - 16, cy: 22, r: 10, fill: m.crit === 'A' ? '#0A1F44' : '#DCE3EE'}, nd);
      const cb = el('text', {x: NW - 16, y: 26, fill: m.crit === 'A' ? '#fff' : '#0A1F44', 'font-size': 10.5, 'font-weight': 800, 'text-anchor': 'middle'}, nd); cb.textContent = m.crit;
      // step number on the belt
      const sn = el('text', {x: NW / 2, y: NH + 24, fill: '#9FB0CB', 'font-size': 10, 'font-weight': 700, 'text-anchor': 'middle'}, nd); sn.textContent = `STEP ${i + 1}`;
      nd.addEventListener('mousemove', (ev) => tip.show(ev,
        `<h5>${esc(m.id)} · ${esc(m.name)}</h5><div class="k">${esc(m.oem || '')} · criticality ${esc(m.crit)}</div>
         <div>${(m.tipLines || []).map(esc).join('<br>')}</div>${m.issue ? `<div class="issue">⚠ ${esc(m.issue)}</div>` : ''}`, c));
      nd.addEventListener('mouseleave', () => tip.hide());
      nd.addEventListener('click', (ev) => { ev.stopPropagation(); setTriggerValue('select', {kind: 'machine', id: m.id, line: ln.id}); });
    });
  });

  chrome(root, d);
  const cam = camera(svg, state, full);
  const bayBox = (id) => { const i = lines.findIndex(l => l.id === id); return i < 0 ? full : [150, TOP + i * BAY_H - 20, W - 300, BAY_H + 20]; };
  const fit = (box) => { // keep aspect of the element
    const r = root.getBoundingClientRect(), ar = r.width / r.height;
    let [x, y, w, h] = box;
    if (w / h > ar) { const nh = w / ar; y -= (nh - h) / 2; h = nh; } else { const nw = h * ar; x -= (nw - w) / 2; w = nw; }
    return [x, y, w, h];
  };
  const target = fit(d.focusLine ? bayBox(d.focusLine) : full);
  if (state.lastFocus !== (d.focusLine || '') || !state.vb) { cam.fly(target, 850); state.lastFocus = d.focusLine || ''; }
  else cam.set(state.vb);
  svg.addEventListener('dblclick', (ev) => { if (!ev.target.closest('.node')) { cam.fly(fit(full)); setTriggerValue('select', {kind: 'plant', id: d.plantId}); } });
  root.querySelector('.zoombar').addEventListener('click', (ev) => {
    const z = ev.target.dataset.z; if (!z) return;
    if (z === 'fit') cam.fly(fit(full)); else cam.zoom(z === 'in' ? .75 : 1.33);
  });
}

// =====================================================================================
// SCENE 2 — IMPACT WEB (force-directed, kind-anchored columns, draggable)
// =====================================================================================
function web(root, d, setTriggerValue) {
  const H = d.virtualHeight || 760, box = root.getBoundingClientRect();
  const W = Math.max(1400, Math.round(H * (box.width || 1400) / (box.height || H)));   // fill the container's width
  const full = [0, 0, W, H];
  const state = ST[d.sceneId] = ST[d.sceneId] || {vb: full, pos: {}};
  if (state.W !== W) { state.W = W; state.vb = full; state.moved = false; }        // layout changed: start fitted
  const svg = el('svg', {viewBox: full.join(' '), preserveAspectRatio: 'xMidYMid meet'}, root);
  const tip = tooltip(root);
  const defs = el('defs', {}, svg);
  defs.innerHTML = `<filter id="glow"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>`;
  const cols = d.columns, colX = {};
  cols.forEach((c, i) => { colX[c.kind] = 110 + i * (W - 300) / (cols.length - 1); });   // room for right-column labels
  const gcol = el('g', {}, svg);
  cols.forEach((c) => {
    el('line', {x1: colX[c.kind], y1: 86, x2: colX[c.kind], y2: H - 50, stroke: 'rgba(255,255,255,.07)', 'stroke-width': 1}, gcol);
    const t = el('text', {x: colX[c.kind], y: 72, fill: '#9FB0CB', 'font-size': 11, 'font-weight': 700, 'text-anchor': 'middle', 'letter-spacing': 1.6}, gcol);
    t.textContent = c.label.toUpperCase();
  });
  const colIdx = Object.fromEntries(cols.map((c, i) => [c.kind, i]));
  const perCol = {};
  d.nodes.forEach(n => { (perCol[n.kind] = perCol[n.kind] || []).push(n.id); });
  const nodes = d.nodes.map((n) => {
    const list = perCol[n.kind], k = list.indexOf(n.id);
    const p = state.pos[n.id] || {x: colX[n.kind], y: 110 + (k + .5) * (H - 180) / list.length};
    return {...n, x: p.x, y: p.y, vx: 0, vy: 0, r: n.r || 9, col: colIdx[n.kind]};
  });
  const byId = Object.fromEntries(nodes.map(n => [n.id, n]));
  const edges = d.edges.filter(e => byId[e.s] && byId[e.t]).map(e => ({...e, a: byId[e.s], b: byId[e.t]}));
  const adj = {}; edges.forEach(e => { (adj[e.s] = adj[e.s] || []).push(e.t); (adj[e.t] = adj[e.t] || []).push(e.s); });

  const ge = el('g', {}, svg), gn = el('g', {}, svg);
  edges.forEach(e => {
    e.el = el('path', {class: 'wedge', stroke: e.status === 'critical' ? 'rgba(214,40,57,.75)' : 'rgba(156,195,255,.28)',
                       'stroke-width': Math.max(1, Math.min(6, e.w || 1.5))}, ge);
    if (e.status === 'critical') {
      e.flow = el('path', {class: 'flow', stroke: '#FF8A95', 'stroke-width': 2.5, style: 'animation-duration:2.4s'}, ge);
    }
  });
  nodes.forEach(n => {
    const c = COLORS[n.status] || COLORS.none;
    n.g = el('g', {class: 'wnode'}, gn);
    if (n.status === 'critical') el('circle', {class: 'pulse', r: n.r + 4, fill: 'none', stroke: c, 'stroke-width': 3}, n.g);
    el('circle', {r: n.r, fill: n.status === 'ok' || !n.status ? '#FFFFFF' : c, stroke: c, 'stroke-width': 3}, n.g);
    const lb = el('text', {x: n.r + 6, y: 4, fill: '#FFFFFF', 'font-size': n.r > 11 ? 12.5 : 11, 'font-weight': n.r > 11 ? 700 : 500}, n.g);
    lb.textContent = n.label;
    n.g.addEventListener('mousemove', (ev) => tip.show(ev, `<h5>${esc(n.label)}</h5><div class="k">${esc(n.kindLabel || n.kind)}</div><div>${esc(n.tip || '')}</div>`, c));
    n.g.addEventListener('mouseleave', () => tip.hide());
    // drag a node (pins it), click to trace its chain
    n.g.addEventListener('pointerdown', (ev) => {
      ev.stopPropagation(); const pt = svg.createSVGPoint(); let moved = false;
      const mv = (e2) => { pt.x = e2.clientX; pt.y = e2.clientY; const p = pt.matrixTransform(svg.getScreenCTM().inverse());
                           n.x = p.x; n.y = p.y; n.fixed = true; moved = true; kick(.3); };
      const up = () => { window.removeEventListener('pointermove', mv); window.removeEventListener('pointerup', up);
                         if (!moved) setTriggerValue('select', {kind: n.kind, id: n.id}); };
      window.addEventListener('pointermove', mv); window.addEventListener('pointerup', up);
    });
  });

  // highlight the selected node's connected chain (BFS through the graph)
  const highlight = (id) => {
    if (!id || !byId[id]) { nodes.forEach(n => n.g.classList.remove('dim')); edges.forEach(e => { e.el.classList.remove('dim'); e.flow && e.flow.classList.remove('dim'); }); return; }
    // trace the causal chain: walk left (upstream causes) and right (downstream effects) separately,
    // so a supplier lights its materials → plants → lines → defects → CAPAs, not the whole connected graph
    const seen = new Set([id]);
    for (const dir of [-1, 1]) {
      const q = [id];
      while (q.length) {
        const c = q.shift();
        (adj[c] || []).forEach(x => {
          if (!seen.has(x) && (byId[x].col - byId[c].col) * dir > 0) { seen.add(x); q.push(x); }
        });
      }
    }
    nodes.forEach(n => n.g.classList.toggle('dim', !seen.has(n.id)));
    edges.forEach(e => { const on = seen.has(e.s) && seen.has(e.t); e.el.classList.toggle('dim', !on); e.flow && e.flow.classList.toggle('dim', !on); });
    byId[id].g.querySelector('circle:not(.pulse)').setAttribute('filter', 'url(#glow)');
  };

  // a tiny force simulation: repulsion + springs + pull toward the node's column
  let alpha = 1;
  const kick = (a) => { alpha = Math.max(alpha, a); if (!state.running) { state.running = true; requestAnimationFrame(tick); } };
  const tick = () => {
    for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
      const a = nodes[i], b = nodes[j];
      if (Math.abs(a.x - b.x) > 70) continue;               // only neighbours in the same column push apart
      const dy = b.y - a.y || (Math.random() - .5), gap = a.r + b.r + 24;
      if (Math.abs(dy) > gap * 2.4) continue;
      const f = (gap * 2.4 - Math.abs(dy)) * .06 * Math.sign(dy);
      a.vy -= f; b.vy += f;
    }
    edges.forEach(e => { const dy = e.b.y - e.a.y, f = dy * .0016 * Math.min(2, e.w || 1);
      e.a.vy += f; e.b.vy -= f; });                          // edges pull connected nodes level with each other
    nodes.forEach(n => {
      if (n.fixed) { n.vx = n.vy = 0; return; }
      n.vx += (colX[n.kind] - n.x) * .2; n.vy += (H / 2 - n.y) * .0003;
      n.vx *= .7; n.vy *= .8; n.x += n.vx * alpha; n.y += n.vy * alpha;
      n.y = Math.max(104, Math.min(H - 60, n.y));
    });
    draw(); alpha *= .985;
    if (alpha > .02) requestAnimationFrame(tick); else state.running = false;
  };
  const draw = () => {
    edges.forEach(e => { const mx = (e.a.x + e.b.x) / 2;
      const p = `M ${e.a.x} ${e.a.y} C ${mx} ${e.a.y}, ${mx} ${e.b.y}, ${e.b.x} ${e.b.y}`;
      e.el.setAttribute('d', p); e.flow && e.flow.setAttribute('d', p); });
    nodes.forEach(n => { n.g.setAttribute('transform', `translate(${n.x},${n.y})`); state.pos[n.id] = {x: n.x, y: n.y}; });
  };
  draw(); highlight(d.selected);
  kick(Object.keys(state.pos).length ? .25 : 1);

  chrome(root, d);
  const cam = camera(svg, state, full); cam.set(state.moved ? state.vb : full);
  svg.addEventListener('dblclick', () => { state.moved = false; highlight(null); cam.fly(full); setTriggerValue('select', {kind: 'none', id: ''}); });
  root.querySelector('.zoombar').addEventListener('click', (ev) => {
    const z = ev.target.dataset.z; if (!z) return;
    if (z === 'fit') { state.moved = false; cam.fly(full); } else cam.zoom(z === 'in' ? .75 : 1.33);
  });
}

export function mountCanvas(component) {
  const { data, parentElement, setTriggerValue } = component;
  parentElement.querySelectorAll('.kkc').forEach(n => n.remove());
  const root = document.createElement('div');
  root.className = 'kkc'; root.style.height = (data.height || 620) + 'px';
  parentElement.appendChild(root);
  if (data.type === 'floor') floor(root, data, setTriggerValue);
  else if (data.type === 'web') web(root, data, setTriggerValue);
}
