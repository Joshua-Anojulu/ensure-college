/* Landing-page journey teaser, painting-first: the overlook plate is the
   guaranteed visual (hydrated by app.js with the other world plates); the
   live miniature island is a progressive enhancement that loads three.js on
   idle once the section approaches the viewport, then fades in over the
   painting inside the same box so nothing painted ever moves. Reduced
   motion, Save-Data, and low-end devices keep the painting.

   The live island is the overlook in miniature, so the swap reads as the
   painting coming alive rather than a different picture: the same four
   landmarks (cabin, desk under the round tree, stone tower, flag hill) on
   the same gold Trail, in the plate's palette and light, framed where the
   painting puts them, over the same sky and scrim (style.css, "Journey and
   Teaser paint"). */
(() => {
  const canvas = document.getElementById("journey-teaser-canvas");
  const section = document.querySelector(".journey-teaser");
  if (!canvas || !section) return;

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  // Dual channel, matching app.js: the JS API and the server-stamped class
  // (the Save-Data header can arrive without navigator.connection).
  const saveData =
    !!(navigator.connection && navigator.connection.saveData) ||
    document.documentElement.classList.contains("save-data");
  const lowEnd =
    (navigator.hardwareConcurrency || 4) <= 2 ||
    (navigator.deviceMemory || 4) <= 2;
  const webgl = (() => {
    try {
      const c = document.createElement("canvas");
      return !!(c.getContext("webgl2") || c.getContext("webgl"));
    } catch (e) {
      return false;
    }
  })();
  if (reduceMotion || saveData || lowEnd || !webgl) {
    // The painting is the experience; under Save-Data even the plate stays
    // unfetched (app.js suppresses all world hydration) and the section
    // rests on its brand wash.
    section.classList.add("teaser-static");
    return;
  }

  let started = false;

  // Idle gate: the swap is an enhancement, so it must never compete with
  // load-critical work. requestIdleCallback with a bounded timeout keeps it
  // deterministic on browsers without idle callbacks.
  let idle = false;
  const markIdle = () => {
    idle = true;
  };
  if ("requestIdleCallback" in window) {
    window.requestIdleCallback(markIdle, { timeout: 4000 });
  } else {
    window.setTimeout(markIdle, 2500);
  }

  // Proximity gate: a cheap bounded poll, cleared the moment it fires.
  // (IntersectionObserver proved unreliable on this section, and a scroll
  // listener is banned; visibility for the render loop is measured per frame.)
  const nearViewport = () => {
    const r = section.getBoundingClientRect();
    return r.top < window.innerHeight + 500 && r.bottom > -500;
  };
  const gate = window.setInterval(() => {
    if (started) {
      window.clearInterval(gate);
      return;
    }
    if (idle && nearViewport()) {
      started = true;
      window.clearInterval(gate);
      loadThree(init);
    }
  }, 250);

  function loadThree(cb) {
    if (window.THREE) {
      cb();
      return;
    }
    const s = document.createElement("script");
    s.src = "/static/js/vendor/three.min.js?v=20261017-2";
    s.onload = cb;
    document.head.appendChild(s);
  }

  function init() {
    const T = window.THREE;

    // Palette: the overlook plate, sampled (the same tones as journey.js).
    const PAPER = 0xf8f7f0;       // paper (overlook f8f9f3 / f8f4e5)
    const HILL_MIST = 0xc9d1bf;   // far hills in the mist (overlook c1ccb8 / d8dfd0)
    const MIST = 0xeaece2;        // horizon mist, the fog (overlook eaece3)
    const GLOW = 0xfbf0d8;        // sky above the far hills (overlook fbf2df)
    const FOREST_DEEP = 0x2e4a3b; // pine washes (overlook 2e4b3b ... c1ccb8)
    const FOREST = 0x5a7260;
    const SAGE = 0x839580;
    const SAGE_COOL = 0x96aa94;
    const SAGE_LIGHT = 0xa5b39d;
    const SAGE_PALE = 0xc1cbb7;
    const MEADOW = 0xaebc9f;      // valley floor (overlook a6b49e, clearing bec9ab)
    const MEADOW_TONES = [SAGE_LIGHT, 0xbec9ab, 0xa0ac85, SAGE_PALE];
    const OLIVE = 0xa0ac85;       // the round tree (overlook a6b487, clearing a0ac85)
    const OLIVE_DEEP = 0x708768;
    const WOOD = 0x8a7c5f;        // cabin logs, desk (overlook 8e886d / 827557)
    const WOOD_DEEP = 0x574b34;
    const WOOD_LIGHT = 0xb1a586;
    const STONE = 0x8e927c;       // the tower (overlook 8e927c / 76735d)
    const STONE_DEEP = 0x76735d;
    const CLIFF = 0xa3a385;       // island walls (overlook cliff top a8aa83)
    const EARTH = 0x8c8a74;       // island keel (overlook cliff 757d6a)
    const INK = 0x2b3a31;         // birds, windows (dusk-treeline 21372a)
    const GOLD = 0xc9a453;        // trail dots, the flag (overlook c4a24f)
    const GOLD_DEEP = 0xaf923f;

    const css = window.getComputedStyle(document.documentElement);
    const mistToken = css.getPropertyValue("--paint-mist").trim();
    const fogColor = new T.Color(/^#[0-9a-f]{6}$/i.test(mistToken) ? mistToken : MIST);

    const renderer = new T.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setClearColor(0x000000, 0);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));

    const scene = new T.Scene();
    scene.fog = new T.Fog(fogColor, 30, 80);
    canvas.dataset.fog = "#" + scene.fog.color.getHexString();
    const camera = new T.PerspectiveCamera(30, 1, 0.1, 200);

    // Paper-toned light with a low golden key, as on the Journey.
    scene.add(new T.HemisphereLight(0xfcfbf5, 0xc4cbb4, 2.35));
    const key = new T.DirectionalLight(0xffe8c4, 0.95);
    key.position.set(12, 16, 10);
    scene.add(key);

    const bands = new Uint8Array([128, 128, 128, 255, 199, 199, 199, 255, 255, 255, 255, 255]);
    const gradientMap = new T.DataTexture(bands, 3, 1, T.RGBAFormat);
    gradientMap.minFilter = T.NearestFilter;
    gradientMap.magFilter = T.NearestFilter;
    gradientMap.generateMipmaps = false;
    gradientMap.needsUpdate = true;

    const materials = new Map();
    const mat = (color) => {
      let m = materials.get(color);
      if (!m) {
        m = new T.MeshToonMaterial({ color, gradientMap });
        materials.set(color, m);
      }
      return m;
    };

    // A radial wash, painted once, for the pooled shadows.
    const wash = (() => {
      const c = document.createElement("canvas");
      c.width = 64;
      c.height = 64;
      const g = c.getContext("2d");
      const grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
      grad.addColorStop(0, "rgba(255, 255, 255, 1)");
      grad.addColorStop(0.55, "rgba(255, 255, 255, 0.6)");
      grad.addColorStop(1, "rgba(255, 255, 255, 0)");
      g.fillStyle = grad;
      g.fillRect(0, 0, 64, 64);
      return new T.CanvasTexture(c);
    })();

    const world = new T.Group();
    scene.add(world);

    let seed = 5;
    const rnd = () => {
      seed = (seed * 16807) % 2147483647;
      return (seed - 1) / 2147483646;
    };

    function place(mesh, x, y, z, ry, parent) {
      mesh.position.set(x, y, z);
      if (ry) mesh.rotation.y = ry;
      (parent || world).add(mesh);
      return mesh;
    }
    const box = (w, h, d, color, x, y, z, ry, parent) =>
      place(new T.Mesh(new T.BoxGeometry(w, h, d), mat(color)), x, y, z, ry, parent);
    const cyl = (rt, rb, h, color, x, y, z, seg, parent) =>
      place(new T.Mesh(new T.CylinderGeometry(rt, rb, h, seg || 12), mat(color)), x, y, z, 0, parent);
    const cone = (r, h, color, x, y, z, seg, ry, parent) =>
      place(new T.Mesh(new T.ConeGeometry(r, h, seg || 7), mat(color)), x, y, z, ry, parent);
    const blob = (r, color, x, y, z, sx, sy, sz) => {
      const m = place(new T.Mesh(new T.IcosahedronGeometry(r, 1), mat(color)), x, y, z);
      m.scale.set(sx || 1, sy || 1, sz || 1);
      m.rotation.set(rnd() * 3, rnd() * 3, rnd() * 3);
      return m;
    };
    const pool = (r, x, z, opacity) => {
      const m = new T.Mesh(
        new T.CircleGeometry(r, 20),
        new T.MeshBasicMaterial({ color: FOREST, transparent: true, opacity, alphaMap: wash, depthWrite: false })
      );
      m.rotation.x = -Math.PI / 2;
      return place(m, x, 0.03, z);
    };

    // The island: a noisy coastline plateau over a keel that sinks into the
    // valley mist below.
    const geo = new T.CylinderGeometry(7, 6.4, 1.6, 30, 2);
    const pos = geo.attributes.position;
    for (let i = 0; i < pos.count; i += 1) {
      const x = pos.getX(i);
      const z = pos.getZ(i);
      const r = Math.sqrt(x * x + z * z);
      if (r > 0.001) {
        const a = Math.atan2(z, x);
        const s = 1 + 0.08 * Math.sin(3 * a + 1.2) + 0.05 * Math.sin(7 * a);
        pos.setX(i, x * s);
        pos.setZ(i, z * s);
      }
    }
    geo.computeVertexNormals();
    // Walls and keel dissolve into the valley mist going down, as on the
    // Journey (per-vertex multipliers on the material colour).
    const mistFade = (g, base, yTop, yBottom, k0, k1) => {
      const b = new T.Color(base);
      const target = new T.Color(MIST).multiplyScalar(1 / 0.78);
      const pos2 = g.attributes.position;
      const colors = new Float32Array(pos2.count * 3);
      for (let i = 0; i < pos2.count; i += 1) {
        const u = Math.min(1, Math.max(0, (yTop - pos2.getY(i)) / (yTop - yBottom)));
        const k = k0 + (k1 - k0) * u * u * (3 - 2 * u);
        colors[i * 3] = 1 + (target.r / b.r - 1) * k;
        colors[i * 3 + 1] = 1 + (target.g / b.g - 1) * k;
        colors[i * 3 + 2] = 1 + (target.b / b.b - 1) * k;
      }
      g.setAttribute("color", new T.BufferAttribute(colors, 3));
    };
    mistFade(geo, CLIFF, 0.8, -0.8, 0, 0.5);
    const keelMat = new T.MeshToonMaterial({ color: EARTH, gradientMap, vertexColors: true });
    const cliffMat = new T.MeshToonMaterial({ color: CLIFF, gradientMap, vertexColors: true });
    place(new T.Mesh(geo, [cliffMat, mat(MEADOW), keelMat]), 0, -0.8, 0);
    const keelGeo = new T.ConeGeometry(5.2, 4.4, 12);
    mistFade(keelGeo, EARTH, -2.2, 2.2, 0.5, 1);
    const keel = place(new T.Mesh(keelGeo, keelMat), 0, -3.8, 0);
    keel.rotation.x = Math.PI;
    for (let i = 0; i < 5; i += 1) {
      const pr = 0.9 + rnd() * 1.3;
      const pa = rnd() * 6.28;
      const pd = rnd() * 4.2;
      const patch = new T.Mesh(new T.CircleGeometry(pr, 9), mat(MEADOW_TONES[i % MEADOW_TONES.length]));
      patch.rotation.x = -Math.PI / 2;
      patch.scale.x = 1.3;
      place(patch, Math.cos(pa) * pd, 0.012 + i * 0.003, Math.sin(pa) * pd);
    }

    // The layout is the overlook's, solved backwards: each landmark sits
    // where the reference camera below sees the plate's own landmark, so the
    // live island lines up with the painting it replaces.

    // Pines: the overlook's layered washes, dark core to misty tip. Dark
    // ones frame the right edge as in the plate; paler ones stand back.
    const pine = (x, z, k, tiers) => {
      const t = tiers || [FOREST_DEEP, FOREST, SAGE];
      cyl(0.08 * k, 0.12 * k, 0.6 * k, WOOD_DEEP, x, 0.3 * k, z, 6);
      cone(0.62 * k, 1.1 * k, t[0], x, 1.05 * k, z);
      cone(0.48 * k, 0.95 * k, t[1], x, 1.6 * k, z);
      cone(0.32 * k, 0.8 * k, t[2], x, 2.15 * k, z);
      pool(0.8 * k, x, z, 0.14);
    };
    // Props are at the plate's scale, small in a wide valley; only the
    // foreground pines at the right edge stand tall, as in the plate.
    const MISTY = [SAGE, SAGE_COOL, SAGE_PALE];
    const MIDDLE = [FOREST, SAGE, SAGE_LIGHT];
    pine(3.3, 5.5, 1.45);
    pine(5.4, 3.8, 1.3);
    pine(2.0, 6.0, 0.95);
    pine(-3.6, -2.2, 0.75);
    pine(-2.6, -3.0, 0.6, MIDDLE);
    pine(-1.4, -2.4, 0.5);
    pine(-0.4, -4.1, 0.7, MISTY);
    pine(1.0, -3.6, 0.55, MIDDLE);
    pine(1.9, -4.4, 0.6, MISTY);
    pine(3.3, -3.4, 0.5, MIDDLE);
    pine(2.9, -0.4, 0.45);
    pine(-0.9, 0.9, 0.5, MIDDLE);

    // A landmark is built in its own group so its parts turn together.
    const PROP = 0.58;
    const spot = (x, z, ry) => {
      const g = new T.Group();
      g.position.set(x, 0, z);
      g.rotation.y = ry || 0;
      g.scale.setScalar(PROP);
      world.add(g);
      return g;
    };

    // Profile: the log cabin, shingle roof, stone chimney, a lit window.
    {
      const g = spot(-2.66, 0.75, 0.5);
      box(1.9, 1.05, 1.4, WOOD, 0, 0.52, 0, 0, g);
      cone(1.5, 0.85, WOOD_LIGHT, 0, 1.45, 0, 4, Math.PI / 4, g);
      box(0.22, 0.55, 0.22, STONE_DEEP, 0.45, 1.75, -0.2, 0, g);
      box(0.36, 0.62, 0.05, WOOD_DEEP, 0.2, 0.31, 0.71, 0, g);
      box(0.32, 0.26, 0.05, GLOW, -0.45, 0.62, 0.71, 0, g);
      pool(0.8, -2.66, 0.75, 0.16);
    }

    // Essays: the desk and chair under the round tree.
    {
      const g = spot(0.63, -0.44, -0.3);
      box(1.0, 0.07, 0.55, WOOD_DEEP, 0, 0.62, 0, 0, g);
      [[-0.42, -0.2], [0.42, -0.2], [-0.42, 0.2], [0.42, 0.2]].forEach((p) => {
        box(0.06, 0.6, 0.06, WOOD_DEEP, p[0], 0.3, p[1], 0, g);
      });
      box(0.5, 0.02, 0.36, PAPER, -0.08, 0.67, 0.02, 0.18, g);
      box(0.4, 0.06, 0.4, WOOD, 0.1, 0.38, 0.5, 0, g);
      box(0.4, 0.5, 0.06, WOOD, 0.1, 0.62, 0.69, 0, g);
      // The round tree, in its own group at the same scale
      const t = spot(1.3, -0.35, 0);
      const trunk = cyl(0.1, 0.16, 1.6, WOOD_DEEP, 0, 0.8, 0, 7, t);
      trunk.rotation.z = -0.18;
      const crown = (r, color, x, y, z, sx, sy, sz) => {
        const m = place(new T.Mesh(new T.IcosahedronGeometry(r, 1), mat(color)), x, y, z, 0, t);
        m.scale.set(sx, sy, sz);
        m.rotation.set(rnd() * 3, rnd() * 3, rnd() * 3);
      };
      crown(0.85, OLIVE, 0.3, 1.85, -0.15, 1.4, 0.75, 1.1);
      crown(0.6, OLIVE_DEEP, -0.25, 1.7, -0.4, 1.3, 0.7, 1.0);
      crown(0.5, SAGE_LIGHT, 0.75, 2.1, 0.0, 1.2, 0.7, 1.0);
      pool(0.9, 1.0, -0.4, 0.16);
    }

    // Deadlines: the stone bell tower.
    {
      const g = spot(4.4, -1.76, 0.2);
      box(0.82, 2.0, 0.82, STONE, 0, 1.0, 0, 0, g);
      box(0.95, 0.12, 0.95, STONE_DEEP, 0, 2.02, 0, 0, g);
      box(0.3, 0.42, 0.06, INK, 0.08, 1.55, 0.42, 0, g);
      box(0.24, 0.5, 0.06, INK, 0.08, 0.25, 0.42, 0, g);
      cone(0.68, 0.7, STONE_DEEP, 0, 2.43, 0, 4, Math.PI / 4, g);
      pool(0.55, 4.4, -1.76, 0.16);
    }

    // Award: the flag on its hill at the back right, where the light is.
    const HILL = { x: 5.4, y: -0.35, z: -3.7, rx: 1.8, ry: 1.65, rz: 1.45, turn: 0.4 };
    const hill = place(
      new T.Mesh(new T.IcosahedronGeometry(1, 2), mat(HILL_MIST)),
      HILL.x, HILL.y, HILL.z, HILL.turn
    );
    hill.scale.set(HILL.rx, HILL.ry, HILL.rz);
    const hillTop = (x, z) => {
      const dx = x - HILL.x;
      const dz = z - HILL.z;
      const c = Math.cos(HILL.turn);
      const s = Math.sin(HILL.turn);
      const lx = dx * c - dz * s;
      const lz = dx * s + dz * c;
      const q = 1 - (lx / HILL.rx) ** 2 - (lz / HILL.rz) ** 2;
      return q > 0 ? HILL.y + HILL.ry * Math.sqrt(q) : 0;
    };
    const poleY = hillTop(HILL.x, HILL.z) - 0.05;
    cyl(0.025, 0.025, 1.2, INK, HILL.x, poleY + 0.6, HILL.z, 6);
    const flagGeo = new T.BoxGeometry(0.42, 0.25, 0.02);
    flagGeo.translate(0.21, 0, 0);
    const flag = place(new T.Mesh(flagGeo, mat(GOLD)), HILL.x + 0.03, poleY + 1.06, HILL.z);

    // The Trail: gold dots from the cliff edge past every landmark and up
    // the hill to the flag, like the plate's path.
    const trail = new T.CatmullRomCurve3([
      new T.Vector3(-4.6, 0, 5.4),
      new T.Vector3(-3.1, 0, 3.7),
      new T.Vector3(-1.3, 0, 2.6),
      new T.Vector3(0.2, 0, 1.5),
      new T.Vector3(0.9, 0, 0.45),
      new T.Vector3(2.3, 0, -0.1),
      new T.Vector3(3.6, 0, -0.8),
      new T.Vector3(4.9, 0, -1.3),
      new T.Vector3(5.9, 0, -2.4),
      new T.Vector3(5.5, 0, -3.3),
    ]);
    const steps = Math.round(trail.getLength() / 0.38);
    const dotPoint = new T.Vector3();
    for (let i = 0; i <= steps; i += 1) {
      trail.getPointAt(i / steps, dotPoint);
      const r = 0.075 + (i % 3) * 0.018;
      const dot = new T.Mesh(new T.CylinderGeometry(r, r + 0.015, 0.04, 8), mat(i % 4 === 3 ? GOLD_DEEP : GOLD));
      const dx = dotPoint.x + (i % 2 ? 0.08 : -0.06);
      place(dot, dx, Math.max(0, hillTop(dx, dotPoint.z)) + 0.03, dotPoint.z);
    }

    // Mist pooling in the valley, soft washes over the meadow as in the
    // plate (transparent, no depth write, so props stand out of it).
    const soft = (() => {
      const c = document.createElement("canvas");
      c.width = 64;
      c.height = 64;
      const g = c.getContext("2d");
      const grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
      grad.addColorStop(0, "rgba(255, 255, 255, 0.9)");
      grad.addColorStop(0.45, "rgba(255, 255, 255, 0.45)");
      grad.addColorStop(1, "rgba(255, 255, 255, 0)");
      g.fillStyle = grad;
      g.fillRect(0, 0, 64, 64);
      return new T.CanvasTexture(c);
    })();
    const mistWash = new T.MeshBasicMaterial({ color: MIST, transparent: true, opacity: 0.36, alphaMap: soft, depthWrite: false });
    [[-1.0, 3.4, 3.4], [1.8, 2.2, 2.9], [-3.4, -0.6, 2.6], [3.0, 1.0, 2.3], [0.2, -2.0, 2.9], [-4.6, 3.0, 2.3]].forEach((m) => {
      const disc = new T.Mesh(new T.CircleGeometry(m[2], 24), mistWash);
      disc.rotation.x = -Math.PI / 2;
      place(disc, m[0], 0.05, m[1]);
    });

    // Cliff-edge rocks, bushes and tufts, as at the plate's overlook.
    blob(0.45, STONE_DEEP, -4.4, 0.12, 4.9, 1.3, 0.6, 1.0);
    blob(0.34, STONE, -3.4, 0.08, 5.7, 1.2, 0.6, 1.0);
    blob(0.28, SAGE, 2.6, 0.14, 2.6, 1.3, 0.7, 1.1);
    blob(0.25, SAGE_LIGHT, -0.9, 0.12, 3.7, 1.3, 0.7, 1.1);
    for (let i = 0; i < 12; i += 1) {
      const a = rnd() * 6.28;
      const d = 2.4 + rnd() * 3.6;
      const tuft = new T.Mesh(new T.ConeGeometry(0.06, 0.22, 5), mat(MEADOW_TONES[i % MEADOW_TONES.length]));
      place(tuft, Math.cos(a) * d, 0.1, Math.sin(a) * d);
    }

    // A few birds over the valley, as in the plate.
    const birds = [];
    for (let i = 0; i < 3; i += 1) {
      const b = new T.Group();
      const wingMat = mat(INK);
      const l = new T.Mesh(new T.BoxGeometry(0.22, 0.02, 0.06), wingMat);
      const rr = new T.Mesh(new T.BoxGeometry(0.22, 0.02, 0.06), wingMat);
      l.position.x = -0.1;
      rr.position.x = 0.1;
      b.add(l);
      b.add(rr);
      scene.add(b);
      birds.push({ g: b, l, r: rr, phase: i * 2.1, radius: 3 + i * 1.2, height: 5.0 + i * 0.6 });
    }

    // Framing: the painting is shown with object-fit: cover at
    // object-position 62% 38% (style.css), so the camera takes the same crop.
    // A reference camera frames the plate's own 1376x768 picture, aimed from
    // the overlook's side (front left, a little above) with the island's
    // landmarks on the plate's; setViewOffset then cuts the canvas out of
    // that picture exactly as cover cuts the box out of the plate. The island
    // lines up with the painting at every width, the phone band included.
    const PLATE_W = 1376;
    const PLATE_H = 768;
    const FOCUS = new T.Vector3(0.6, 0.6, -0.6);
    const AIM = { u: 0.66, v: 0.58 };
    const az = (-14 * Math.PI) / 180;
    const el = (20 * Math.PI) / 180;
    const DIST = 24;
    camera.position.set(
      FOCUS.x + Math.sin(az) * Math.cos(el) * DIST,
      FOCUS.y + Math.sin(el) * DIST,
      FOCUS.z + Math.cos(az) * Math.cos(el) * DIST
    );
    camera.lookAt(FOCUS);
    scene.fog.near = DIST - 4;
    scene.fog.far = DIST + 40;

    function resize() {
      const w = canvas.clientWidth || section.clientWidth;
      const h = canvas.clientHeight || 420;
      renderer.setSize(w, h, false);
      const s = Math.max(w / PLATE_W, h / PLATE_H);
      const fullW = PLATE_W * s;
      const fullH = PLATE_H * s;
      const left = (fullW - w) * 0.62;
      const top = (fullH - h) * 0.38;
      camera.setViewOffset(
        fullW, fullH,
        left - (AIM.u - 0.5) * fullW,
        top - (AIM.v - 0.5) * fullH,
        w, h
      );
    }
    window.addEventListener("resize", resize);
    resize();

    function onScreen() {
      const r = section.getBoundingClientRect();
      return r.top < window.innerHeight && r.bottom > 0;
    }

    const SWAY = 0.12;
    function pose(now) {
      world.rotation.y = SWAY * Math.sin(now * 0.23);
      world.position.y = Math.sin(now * 0.5) * 0.12;
      flag.rotation.y = Math.sin(now * 2.2) * 0.22;
      for (const b of birds) {
        const a = now * 0.32 + b.phase;
        b.g.position.set(0.5 + Math.cos(a) * b.radius, b.height + Math.sin(now * 0.8 + b.phase) * 0.3, -3.5 + Math.sin(a) * b.radius * 0.5);
        b.g.rotation.y = -a;
        const flap = Math.sin(now * 7 + b.phase) * 0.5;
        b.l.rotation.z = flap;
        b.r.rotation.z = -flap;
      }
    }

    // Paint once immediately so real pixels exist behind the fade, but
    // reveal only after the visitor has dwelt on the painting: the labeled
    // overlook is the message and the live island is the reward, and
    // swapping the moment pixels exist reads as the teaser vanishing.
    // Bounded poll, same pattern as the proximity gate (scroll listeners
    // are banned); the timer resets whenever the section leaves view.
    pose(0);
    renderer.render(scene, camera);
    const DWELL_MS = 4000;
    let dwellStart = null;
    const dwell = window.setInterval(() => {
      const r = section.getBoundingClientRect();
      const visible = Math.min(r.bottom, window.innerHeight) - Math.max(r.top, 0);
      const ratio = r.height > 0 ? visible / r.height : 0;
      if (ratio >= 0.85 && !document.hidden) {
        if (dwellStart === null) dwellStart = performance.now();
        if (performance.now() - dwellStart >= DWELL_MS) {
          window.clearInterval(dwell);
          section.classList.add("teaser-live");
        }
      } else {
        dwellStart = null;
      }
    }, 250);

    function frame(nowMs) {
      if (!document.hidden && onScreen()) {
        pose(nowMs * 0.001);
        renderer.render(scene, camera);
      }
      window.requestAnimationFrame(frame);
    }
    window.requestAnimationFrame(frame);
  }
})();
