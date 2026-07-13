/* /journey: a real-time scroll-driven camera flight through four Forest Light
   dioramas. No video, no network assets: every scene is built from primitives
   in the site palette. Scroll position maps to a point on one continuous
   forward camera spline, so the "seams" between scenes cannot exist. */
(() => {
  const root = document.documentElement;
  const track = document.getElementById("journey-track");
  const canvas = document.getElementById("journey-canvas");

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const webgl = (() => {
    try {
      const c = document.createElement("canvas");
      return !!(c.getContext("webgl2") || c.getContext("webgl"));
    } catch (e) {
      return false;
    }
  })();

  if (!track || !canvas || !window.THREE || reduceMotion || !webgl) {
    root.classList.add("journey-static");
    return;
  }

  const T = window.THREE;

  // ---- Palette (style.css tokens, hex-locked) ----
  const CANVAS = 0xf1f2ee;
  const ISLAND = 0xdfe8e2;
  const ISLAND_EDGE = 0xc3cdc0;
  const FOREST = 0x1e4034;
  const FOREST_DEEP = 0x132d24;
  const BONE = 0xfbfcfa;
  const INK = 0x16211b;
  const AMBER = 0xc98d2c;
  const AMBER_DEEP = 0x8a5e14;
  const SAGE = 0x8fb98a;

  const renderer = new T.WebGLRenderer({ canvas, antialias: true });
  renderer.setClearColor(CANVAS, 1);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));

  const scene = new T.Scene();
  scene.fog = new T.Fog(CANVAS, 46, 130);

  const camera = new T.PerspectiveCamera(42, 1, 0.1, 400);

  scene.add(new T.HemisphereLight(0xffffff, 0xdfe8e2, 0.95));
  const key = new T.DirectionalLight(0xffe9c4, 1.15);
  key.position.set(28, 46, 24);
  scene.add(key);

  // ---- Primitive helpers ----
  const mat = (color, opts) => new T.MeshLambertMaterial(Object.assign({ color }, opts || {}));

  function box(parent, w, h, d, color, x, y, z, ry) {
    const m = new T.Mesh(new T.BoxGeometry(w, h, d), mat(color));
    m.position.set(x, y, z);
    if (ry) m.rotation.y = ry;
    parent.add(m);
    return m;
  }

  function cyl(parent, rt, rb, h, color, x, y, z, seg) {
    const m = new T.Mesh(new T.CylinderGeometry(rt, rb, h, seg || 14), mat(color));
    m.position.set(x, y, z);
    parent.add(m);
    return m;
  }

  function cone(parent, r, h, color, x, y, z) {
    const m = new T.Mesh(new T.ConeGeometry(r, h, 8), mat(color));
    m.position.set(x, y, z);
    parent.add(m);
    return m;
  }

  function shadow(parent, r, x, z, opacity) {
    const m = new T.Mesh(
      new T.CircleGeometry(r, 24),
      new T.MeshBasicMaterial({ color: FOREST_DEEP, transparent: true, opacity: opacity || 0.07 })
    );
    m.rotation.x = -Math.PI / 2;
    m.position.set(x, 0.02, z);
    parent.add(m);
    return m;
  }

  function island(z, radius) {
    const g = new T.Group();
    const top = cyl(g, radius, radius * 0.94, 1.6, ISLAND, 0, -0.8, 0, 26);
    top.position.y = -0.8;
    cyl(g, radius * 0.94, radius * 0.55, 2.6, ISLAND_EDGE, 0, -2.8, 0, 26);
    g.position.z = z;
    scene.add(g);
    return g;
  }

  function tree(parent, x, z, s) {
    const k = s || 1;
    cyl(parent, 0.14 * k, 0.18 * k, 0.7 * k, AMBER_DEEP, x, 0.35 * k, z, 6);
    cone(parent, 0.75 * k, 1.5 * k, FOREST, x, 1.4 * k, z);
    cone(parent, 0.55 * k, 1.1 * k, SAGE, x, 2.1 * k, z);
    shadow(parent, 0.9 * k, x, z);
  }

  // ---- Scene 1 (z = 0): the profile desk ----
  {
    const g = island(0, 12);
    // Desk
    box(g, 5.2, 0.35, 2.6, AMBER_DEEP, 0, 1.5, 0);
    box(g, 0.3, 1.4, 0.3, FOREST_DEEP, -2.3, 0.7, -1.0);
    box(g, 0.3, 1.4, 0.3, FOREST_DEEP, 2.3, 0.7, -1.0);
    box(g, 0.3, 1.4, 0.3, FOREST_DEEP, -2.3, 0.7, 1.0);
    box(g, 0.3, 1.4, 0.3, FOREST_DEEP, 2.3, 0.7, 1.0);
    shadow(g, 3.4, 0, 0, 0.09);
    // The one glowing form
    const form = new T.Mesh(
      new T.PlaneGeometry(1.5, 2.0),
      new T.MeshLambertMaterial({ color: BONE, emissive: 0x3a3a30 })
    );
    form.rotation.x = -Math.PI / 2 + 0.35;
    form.position.set(0, 1.78, 0.35);
    g.add(form);
    for (let i = 0; i < 4; i += 1) {
      box(g, 1.0, 0.02, 0.1, ISLAND_EDGE, 0, 1.8, 0.02 + i * 0.42 - 0.55);
    }
    // Lamp with an amber head
    cyl(g, 0.09, 0.14, 1.5, INK, -1.8, 2.4, -0.7, 8);
    cone(g, 0.45, 0.6, AMBER, -1.55, 3.15, -0.55);
    const glow = new T.PointLight(0xffc65e, 8, 9);
    glow.position.set(-1.4, 2.7, -0.2);
    g.add(glow);
    // Books + chair
    box(g, 0.9, 0.22, 0.62, FOREST, 1.7, 1.79, -0.6, 0.3);
    box(g, 0.8, 0.2, 0.58, AMBER, 1.62, 2.0, -0.58, 0.12);
    box(g, 1.2, 0.18, 1.2, FOREST, 0, 0.95, 2.2);
    box(g, 1.2, 1.3, 0.18, FOREST, 0, 1.6, 2.8);
    shadow(g, 1.0, 0, 2.3);
    tree(g, -6.5, 3.5, 1.2);
    tree(g, 6.8, -3.8, 0.9);
  }

  // ---- Scene 2 (z = -70): three lanes, three districts ----
  {
    const g = island(-70, 17);
    // Converging paths
    const path = (x, ry) => {
      const p = box(g, 2.2, 0.08, 12, BONE, x, 0.06, 3.5, ry);
      p.material.color.setHex(0xe8ece6);
      return p;
    };
    path(-6, 0.5);
    path(0, 0);
    path(6, -0.5);
    // Scholarship hall (left): columned front
    const hall = new T.Group();
    box(hall, 6.4, 2.6, 4.4, BONE, 0, 1.3, 0);
    box(hall, 7.0, 0.5, 5.0, FOREST, 0, 2.85, 0);
    cone(hall, 3.6, 1.8, FOREST_DEEP, 0, 4.0, 0);
    for (let i = -2; i <= 2; i += 1) {
      cyl(hall, 0.16, 0.16, 2.3, BONE, i * 1.25, 1.15, 2.45, 8);
    }
    box(hall, 1.0, 1.4, 0.1, FOREST_DEEP, 0, 0.7, 2.26);
    hall.position.set(-8.5, 0, -3.5);
    hall.rotation.y = 0.5;
    g.add(hall);
    shadow(g, 4.4, -8.5, -3.5, 0.09);
    // Summer campus (right): cabins + trees
    const camp = new T.Group();
    const cabin = (x, z, ry) => {
      box(camp, 1.7, 1.1, 1.4, AMBER_DEEP, x, 0.55, z, ry);
      cone(camp, 1.25, 0.9, FOREST, x, 1.55, z);
    };
    cabin(0, 0, 0.2);
    cabin(2.4, 1.6, -0.4);
    cabin(-1.9, 1.9, 0.7);
    tree(camp, 1.2, -1.8, 1);
    tree(camp, -2.6, -0.6, 0.8);
    tree(camp, 3.6, -0.4, 0.9);
    camp.position.set(9.0, 0, -3.0);
    g.add(camp);
    // Competition arena (back): ring with flags
    const arena = new T.Group();
    cyl(arena, 3.4, 3.7, 1.3, BONE, 0, 0.65, 0, 20);
    cyl(arena, 2.5, 2.5, 1.35, SAGE, 0, 0.7, 0, 20);
    for (let i = 0; i < 6; i += 1) {
      const a = (i / 6) * Math.PI * 2;
      const fx = Math.cos(a) * 3.4;
      const fz = Math.sin(a) * 3.4;
      cyl(arena, 0.05, 0.05, 1.6, INK, fx, 2.0, fz, 6);
      box(arena, 0.55, 0.34, 0.04, AMBER, fx + 0.28, 2.6, fz);
    }
    arena.position.set(0, 0, -9.5);
    g.add(arena);
    shadow(g, 4.2, 0, -9.5, 0.09);
    tree(g, -13, 4, 1.1);
    tree(g, 13.4, 3.2, 1.3);
    tree(g, -4, 8.5, 0.9);
  }

  // ---- Scene 3 (z = -140): the plan war-room ----
  {
    const g = island(-140, 13);
    // The board
    box(g, 8.6, 4.6, 0.4, FOREST, 0, 3.1, -3.2);
    box(g, 9.2, 5.2, 0.2, AMBER_DEEP, 0, 3.1, -3.42);
    const pins = [];
    const card = (x, y, tone) => {
      box(g, 1.35, 0.9, 0.06, tone, x, y, -2.95);
      const pin = new T.Mesh(new T.SphereGeometry(0.09, 8, 8), mat(AMBER));
      pin.position.set(x, y + 0.38, -2.9);
      g.add(pin);
      pins.push(pin.position.clone());
    };
    card(-3.1, 4.2, BONE);
    card(-1.0, 3.1, 0xe8ece6);
    card(1.4, 4.4, BONE);
    card(3.0, 2.6, 0xe8ece6);
    card(-2.6, 1.9, BONE);
    card(0.6, 1.7, BONE);
    // Threads between pins
    const threadMat = new T.LineBasicMaterial({ color: AMBER });
    for (let i = 0; i < pins.length - 1; i += 1) {
      const geo = new T.BufferGeometry().setFromPoints([pins[i], pins[i + 1]]);
      g.add(new T.Line(geo, threadMat));
    }
    // Work table with laptop
    box(g, 4.4, 0.3, 2.0, AMBER_DEEP, 0, 1.15, 1.6);
    box(g, 0.24, 1.0, 0.24, FOREST_DEEP, -1.9, 0.5, 1.0);
    box(g, 0.24, 1.0, 0.24, FOREST_DEEP, 1.9, 0.5, 1.0);
    box(g, 0.24, 1.0, 0.24, FOREST_DEEP, -1.9, 0.5, 2.2);
    box(g, 0.24, 1.0, 0.24, FOREST_DEEP, 1.9, 0.5, 2.2);
    box(g, 1.2, 0.08, 0.85, INK, -0.6, 1.34, 1.6);
    const lid = box(g, 1.2, 0.8, 0.06, INK, -0.6, 1.72, 1.2);
    lid.rotation.x = -0.35;
    shadow(g, 3.0, 0, 1.4, 0.09);
    tree(g, 7.4, 4.2, 1);
    tree(g, -7.8, 2.4, 1.1);
  }

  // ---- Scene 4 (z = -210): the gate at dawn ----
  {
    const g = island(-210, 15);
    // Path to the arch
    const p = box(g, 2.6, 0.08, 16, 0xe8ece6, 0, 0.06, 3);
    p.material.color.setHex(0xe8ece6);
    // Campus arch
    box(g, 1.3, 6.2, 1.3, BONE, -3.1, 3.1, -3);
    box(g, 1.3, 6.2, 1.3, BONE, 3.1, 3.1, -3);
    box(g, 8.6, 1.3, 1.5, BONE, 0, 6.4, -3);
    box(g, 8.9, 0.5, 1.7, FOREST, 0, 7.2, -3);
    box(g, 1.6, 0.5, 0.2, AMBER, 0, 5.6, -2.3);
    shadow(g, 4.6, 0, -3, 0.08);
    // The award envelope, oversized, leaning on the arch
    const env = new T.Group();
    box(env, 2.6, 1.7, 0.14, BONE, 0, 0.85, 0);
    const flap = new T.Mesh(new T.ConeGeometry(1.32, 0.9, 4), mat(0xe8ece6));
    flap.rotation.z = Math.PI;
    flap.rotation.y = Math.PI / 4;
    flap.position.set(0, 1.35, 0.02);
    env.add(flap);
    const seal = new T.Mesh(new T.CylinderGeometry(0.22, 0.22, 0.08, 12), mat(AMBER));
    seal.rotation.x = Math.PI / 2;
    seal.position.set(0, 0.8, 0.12);
    env.add(seal);
    env.position.set(1.9, 0, -1.4);
    env.rotation.y = -0.4;
    env.rotation.z = -0.06;
    g.add(env);
    shadow(g, 1.6, 1.9, -1.3);
    // Dawn sun disk behind the arch
    const sun = new T.Mesh(
      new T.CircleGeometry(7, 40),
      new T.MeshBasicMaterial({ color: 0xf3d9a4, transparent: true, opacity: 0.85 })
    );
    sun.position.set(0, 7.5, -22);
    g.add(sun);
    const dawn = new T.PointLight(0xffd98a, 20, 40);
    dawn.position.set(0, 6, -10);
    g.add(dawn);
    tree(g, -8.2, 1.2, 1.2);
    tree(g, 8.6, 2.6, 1.0);
    tree(g, -5.6, -6.5, 0.9);
    tree(g, 6.2, -7.0, 1.1);
  }

  // ---- The one continuous camera flight (never reverses in z) ----
  const camPath = new T.CatmullRomCurve3([
    new T.Vector3(0.0, 8.5, 26),
    new T.Vector3(0.0, 5.0, 10),
    new T.Vector3(-2.5, 4.2, 4),      // low over the desk
    new T.Vector3(5.5, 7.0, -18),
    new T.Vector3(15.0, 9.0, -48),    // swing wide right into scene 2
    new T.Vector3(2.0, 10.5, -62),    // over the arena, looking across districts
    new T.Vector3(-13.0, 8.0, -84),   // exit wide left
    new T.Vector3(-7.0, 6.0, -118),
    new T.Vector3(0.5, 4.6, -134),    // push toward the board
    new T.Vector3(-6.0, 6.5, -166),
    new T.Vector3(0.0, 3.8, -196),    // low approach to the gate
    new T.Vector3(0.0, 5.2, -209),    // through the arch
    new T.Vector3(0.0, 11.0, -224),   // crane up at dawn
  ]);

  const lookPath = new T.CatmullRomCurve3([
    new T.Vector3(0.0, 2.0, 4),
    new T.Vector3(0.0, 1.8, 0),
    new T.Vector3(0.0, 1.8, -1),      // the form on the desk
    new T.Vector3(0.0, 2.5, -55),
    new T.Vector3(-4.0, 2.0, -72),    // the hall
    new T.Vector3(0.0, 2.0, -80),     // the arena
    new T.Vector3(2.0, 2.5, -100),
    new T.Vector3(0.0, 3.0, -140),
    new T.Vector3(0.0, 3.1, -143),    // the board
    new T.Vector3(0.0, 3.0, -185),
    new T.Vector3(0.0, 4.5, -210),    // the arch
    new T.Vector3(0.0, 6.0, -222),
    new T.Vector3(0.0, 8.0, -240),    // the dawn
  ]);

  // ---- Scroll plumbing: track height defines flight length; progress is
  // read inside rAF (no scroll listeners), then damped for glide. ----
  root.classList.add("journey-live");
  track.style.minHeight = "620vh";

  const cards = Array.from(document.querySelectorAll(".journey-card")).map((el) => {
    const band = (el.dataset.band || "0,1").split(",").map(Number);
    return { el, start: band[0], end: band[1] };
  });
  const dots = Array.from(document.querySelectorAll(".journey-rail span"));

  let target = 0;
  let t = 0;
  const camPos = new T.Vector3();
  const lookPos = new T.Vector3();

  function resize() {
    const w = window.innerWidth;
    const h = window.innerHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  window.addEventListener("resize", resize);
  resize();

  function frame() {
    const max = track.offsetHeight - window.innerHeight;
    target = max > 0 ? Math.min(1, Math.max(0, (window.scrollY - track.offsetTop) / max)) : 0;
    t += (target - t) * 0.07; // damped glide

    camPath.getPointAt(t, camPos);
    lookPath.getPointAt(t, lookPos);
    camera.position.copy(camPos);
    camera.lookAt(lookPos);

    for (let i = 0; i < cards.length; i += 1) {
      const c = cards[i];
      const span = c.end - c.start;
      const fadeIn = Math.min(1, Math.max(0, (t - c.start) / (span * 0.25)));
      const fadeOut = Math.min(1, Math.max(0, (c.end - t) / (span * 0.25)));
      const o = Math.min(fadeIn, fadeOut);
      c.el.style.opacity = o.toFixed(3);
      c.el.style.transform = "translateY(" + ((1 - o) * 18).toFixed(1) + "px)";
      c.el.classList.toggle("is-active", o > 0.5);
      if (dots[i]) dots[i].classList.toggle("is-active", t >= c.start && t <= c.end);
    }

    // The rail bows out with the flight so it never floats over the footer.
    const rail = dots.length ? dots[0].parentElement : null;
    if (rail) rail.style.opacity = t > 0.97 ? String(Math.max(0, (1 - t) / 0.03)) : "1";

    renderer.render(scene, camera);
    if (!document.hidden) window.requestAnimationFrame(frame);
  }

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) window.requestAnimationFrame(frame);
  });

  window.requestAnimationFrame(frame);
})();
