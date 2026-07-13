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
  const ISLAND_DARK = 0xb9c6bb;
  const FOREST = 0x1e4034;
  const FOREST_DEEP = 0x132d24;
  const BONE = 0xfbfcfa;
  const PAPER = 0xe8ece6;
  const INK = 0x16211b;
  const AMBER = 0xc98d2c;
  const AMBER_DEEP = 0x8a5e14;
  const SAGE = 0x8fb98a;
  const SAGE_LIGHT = 0xb5d0af;

  const renderer = new T.WebGLRenderer({ canvas, antialias: true });
  renderer.setClearColor(CANVAS, 1);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = T.PCFSoftShadowMap;

  const scene = new T.Scene();
  scene.fog = new T.Fog(CANVAS, 48, 135);

  const camera = new T.PerspectiveCamera(42, 1, 0.1, 400);

  scene.add(new T.HemisphereLight(0xfffdf6, 0xd7e2d8, 0.85));
  const key = new T.DirectionalLight(0xffe9c4, 1.35);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.camera.left = -32;
  key.shadow.camera.right = 32;
  key.shadow.camera.top = 32;
  key.shadow.camera.bottom = -32;
  key.shadow.camera.near = 1;
  key.shadow.camera.far = 140;
  key.shadow.bias = -0.0006;
  scene.add(key);
  scene.add(key.target);

  // ---- Registries for idle life ----
  const bobbers = [];    // {obj, amp, speed, phase}
  const wavers = [];     // {obj, axis, amp, speed, phase}
  const drifters = [];   // {obj, speed, minX, maxX}
  const orbiters = [];   // {obj, center, radius, speed, phase, height}
  const flappers = [];   // wing pairs {left, right, speed, phase}

  let seedState = 7;
  const rnd = () => {
    seedState = (seedState * 16807) % 2147483647;
    return (seedState - 1) / 2147483646;
  };
  const jitter = (base, spread) => base + (rnd() - 0.5) * spread;

  // ---- Primitive helpers (all shadow-aware) ----
  const mat = (color, opts) => new T.MeshLambertMaterial(Object.assign({ color }, opts || {}));

  function add(parent, mesh, cast, receive) {
    mesh.castShadow = cast !== false;
    mesh.receiveShadow = receive === true;
    parent.add(mesh);
    return mesh;
  }

  function box(parent, w, h, d, color, x, y, z, ry) {
    const m = new T.Mesh(new T.BoxGeometry(w, h, d), mat(color));
    m.position.set(x, y, z);
    if (ry) m.rotation.y = ry;
    return add(parent, m);
  }

  function cyl(parent, rt, rb, h, color, x, y, z, seg) {
    const m = new T.Mesh(new T.CylinderGeometry(rt, rb, h, seg || 14), mat(color));
    m.position.set(x, y, z);
    return add(parent, m);
  }

  function cone(parent, r, h, color, x, y, z, seg) {
    const m = new T.Mesh(new T.ConeGeometry(r, h, seg || 8), mat(color));
    m.position.set(x, y, z);
    return add(parent, m);
  }

  function blob(parent, r, color, x, y, z, sx, sy, sz) {
    const m = new T.Mesh(new T.IcosahedronGeometry(r, 1), mat(color));
    m.position.set(x, y, z);
    m.scale.set(sx || 1, sy || 1, sz || 1);
    m.rotation.set(rnd() * 3, rnd() * 3, rnd() * 3);
    return add(parent, m);
  }

  function shadowDisc(parent, r, x, z, opacity) {
    const m = new T.Mesh(
      new T.CircleGeometry(r, 24),
      new T.MeshBasicMaterial({ color: FOREST_DEEP, transparent: true, opacity: opacity || 0.05 })
    );
    m.rotation.x = -Math.PI / 2;
    m.position.set(x, 0.03, z);
    parent.add(m);
    return m;
  }

  // Organic island: a noisy-coastline plateau with a tapered rock base.
  function island(z, radius, phase) {
    const g = new T.Group();
    const geo = new T.CylinderGeometry(radius, radius * 0.9, 2.6, 34, 2);
    const pos = geo.attributes.position;
    for (let i = 0; i < pos.count; i += 1) {
      const x = pos.getX(i);
      const zz = pos.getZ(i);
      const r = Math.sqrt(x * x + zz * zz);
      if (r > 0.001) {
        const a = Math.atan2(zz, x);
        const s = 1 + 0.075 * Math.sin(3 * a + phase) + 0.05 * Math.sin(7 * a + phase * 2.3);
        pos.setX(i, x * s);
        pos.setZ(i, zz * s);
      }
    }
    geo.computeVertexNormals();
    const top = new T.Mesh(geo, mat(ISLAND));
    top.position.y = -1.3;
    top.receiveShadow = true;
    g.add(top);

    const base = new T.Mesh(
      new T.ConeGeometry(radius * 0.86, radius * 0.62, 12),
      mat(ISLAND_DARK)
    );
    base.rotation.x = Math.PI;
    base.position.y = -2.6 - radius * 0.31;
    g.add(base);

    g.position.z = z;
    scene.add(g);
    bobbers.push({ obj: g, amp: 0.22, speed: jitter(0.4, 0.15), phase: phase * 2 });
    return g;
  }

  function tree(parent, x, z, s) {
    const k = (s || 1) * jitter(1, 0.25);
    const lean = (rnd() - 0.5) * 0.12;
    const grp = new T.Group();
    cyl(grp, 0.12 * k, 0.17 * k, 0.8 * k, AMBER_DEEP, 0, 0.4 * k, 0, 6);
    cone(grp, 0.8 * k, 1.4 * k, FOREST, 0, 1.35 * k, 0, 7);
    cone(grp, 0.62 * k, 1.15 * k, jitter(0.5, 1) > 0.5 ? SAGE : FOREST, 0, 2.05 * k, 0, 7);
    cone(grp, 0.4 * k, 0.85 * k, SAGE_LIGHT, 0, 2.7 * k, 0, 7);
    grp.position.set(x, 0, z);
    grp.rotation.z = lean;
    parent.add(grp);
    shadowDisc(parent, 0.9 * k, x, z);
    return grp;
  }

  function bush(parent, x, z, s) {
    const k = (s || 1) * jitter(1, 0.3);
    blob(parent, 0.5 * k, rnd() > 0.5 ? SAGE : SAGE_LIGHT, x, 0.35 * k, z, 1.3, 0.8, 1.1);
    shadowDisc(parent, 0.55 * k, x, z);
  }

  function rock(parent, x, z, s) {
    const k = (s || 1) * jitter(1, 0.4);
    blob(parent, 0.32 * k, ISLAND_DARK, x, 0.2 * k, z, 1.2, 0.7, 1);
  }

  function lantern(parent, x, z) {
    cyl(parent, 0.05, 0.07, 1.7, INK, x, 0.85, z, 6);
    const bulb = new T.Mesh(
      new T.SphereGeometry(0.16, 10, 8),
      new T.MeshLambertMaterial({ color: AMBER, emissive: 0x8a5e14 })
    );
    bulb.position.set(x, 1.78, z);
    parent.add(bulb);
    box(parent, 0.22, 0.06, 0.22, FOREST_DEEP, x, 1.95, z);
  }

  function cloud(x, y, z, s) {
    const g = new T.Group();
    const m = new T.MeshLambertMaterial({ color: BONE, transparent: true, opacity: 0.92 });
    const puffs = 3 + Math.floor(rnd() * 3);
    for (let i = 0; i < puffs; i += 1) {
      const p = new T.Mesh(new T.SphereGeometry(jitter(1.1, 0.6), 8, 6), m);
      p.position.set(i * jitter(1.2, 0.5) - puffs * 0.5, jitter(0, 0.4), jitter(0, 0.6));
      p.scale.y = 0.62;
      g.add(p);
    }
    g.scale.setScalar(s || 1);
    g.position.set(x, y, z);
    scene.add(g);
    drifters.push({ obj: g, speed: jitter(0.25, 0.15), minX: x - 14, maxX: x + 14 });
    return g;
  }

  function bird(cx, cy, cz, radius, speed) {
    const g = new T.Group();
    const body = mat(INK);
    const left = new T.Mesh(new T.BoxGeometry(0.55, 0.03, 0.16), body);
    const right = new T.Mesh(new T.BoxGeometry(0.55, 0.03, 0.16), body);
    left.position.x = -0.26;
    right.position.x = 0.26;
    g.add(left);
    g.add(right);
    scene.add(g);
    orbiters.push({ obj: g, center: new T.Vector3(cx, cy, cz), radius, speed, phase: rnd() * 6.28 });
    flappers.push({ left, right, speed: jitter(9, 3), phase: rnd() * 6.28 });
  }

  // =======================================================================
  // Scene 1 (z = 0): the profile desk
  // =======================================================================
  {
    const g = island(0, 12, 1.7);
    // Rug
    const rug = new T.Mesh(new T.CircleGeometry(3.6, 28), mat(0xd3ddd2));
    rug.rotation.x = -Math.PI / 2;
    rug.position.y = 0.02;
    rug.receiveShadow = true;
    g.add(rug);
    // Desk
    box(g, 5.2, 0.35, 2.6, AMBER_DEEP, 0, 1.5, 0);
    box(g, 5.0, 0.08, 2.4, 0x9c6b1f, 0, 1.71, 0);
    [[-2.3, -1.0], [2.3, -1.0], [-2.3, 1.0], [2.3, 1.0]].forEach((p) => {
      box(g, 0.28, 1.35, 0.28, FOREST_DEEP, p[0], 0.68, p[1]);
    });
    box(g, 1.4, 1.1, 2.2, FOREST, 1.4, 0.9, 0); // drawer block
    cyl(g, 0.05, 0.05, 0.3, AMBER, 1.4, 1.1, 1.12, 6);
    // The one glowing form
    const form = new T.Mesh(
      new T.PlaneGeometry(1.5, 2.0),
      new T.MeshLambertMaterial({ color: BONE, emissive: 0x3c3c30 })
    );
    form.rotation.x = -Math.PI / 2 + 0.35;
    form.position.set(-0.3, 1.82, 0.35);
    g.add(form);
    for (let i = 0; i < 4; i += 1) {
      box(g, 1.0, 0.02, 0.1, PAPER, -0.3, 1.86, 0.02 + i * 0.42 - 0.55);
    }
    // Lamp + glow + dust motes
    cyl(g, 0.1, 0.16, 1.5, INK, -1.9, 2.4, -0.7, 8);
    cone(g, 0.5, 0.62, AMBER, -1.62, 3.15, -0.55, 10);
    const glow = new T.PointLight(0xffc65e, 9, 10);
    glow.position.set(-1.4, 2.75, -0.2);
    g.add(glow);
    const moteGeo = new T.BufferGeometry();
    const motePos = new Float32Array(36);
    for (let i = 0; i < 12; i += 1) {
      motePos[i * 3] = jitter(-1.4, 1.6);
      motePos[i * 3 + 1] = jitter(2.4, 1.2);
      motePos[i * 3 + 2] = jitter(-0.2, 1.4);
    }
    moteGeo.setAttribute("position", new T.BufferAttribute(motePos, 3));
    const motes = new T.Points(
      moteGeo,
      new T.PointsMaterial({ color: 0xe8c987, size: 0.07, transparent: true, opacity: 0.8 })
    );
    g.add(motes);
    wavers.push({ obj: motes, axis: "y", amp: 0.18, speed: 0.6, phase: 0 });
    // Books, mug, chair
    box(g, 0.9, 0.2, 0.62, FOREST, 1.55, 1.86, -0.62, 0.3);
    box(g, 0.8, 0.18, 0.56, AMBER, 1.48, 2.05, -0.6, 0.12);
    box(g, 0.72, 0.16, 0.5, SAGE, 1.52, 2.22, -0.58, 0.45);
    cyl(g, 0.14, 0.12, 0.24, PAPER, -1.15, 1.87, 0.85, 10);
    const seat = new T.Group();
    box(seat, 1.15, 0.16, 1.15, FOREST, 0, 0.95, 0);
    box(seat, 1.15, 1.25, 0.16, FOREST, 0, 1.62, 0.55);
    [[-0.45, -0.45], [0.45, -0.45], [-0.45, 0.45], [0.45, 0.45]].forEach((p) => {
      cyl(seat, 0.05, 0.05, 0.9, FOREST_DEEP, p[0], 0.45, p[1], 6);
    });
    seat.position.set(-0.2, 0, 2.3);
    seat.rotation.y = 0.2;
    g.add(seat);
    shadowDisc(g, 3.4, 0, 0, 0.08);
    // Grounds
    tree(g, -6.8, 3.2, 1.25);
    tree(g, -5.4, -4.6, 0.9);
    tree(g, 6.9, -3.6, 1.0);
    tree(g, 7.6, 2.6, 0.7);
    bush(g, -4.2, 5.6, 1);
    bush(g, 5.2, 4.8, 1.2);
    bush(g, -7.9, -1.2, 0.8);
    rock(g, 3.9, -5.8, 1.3);
    rock(g, -2.5, -6.9, 1);
    lantern(g, 3.2, 3.4);
  }

  // =======================================================================
  // Scene 2 (z = -70): three lanes, three districts
  // =======================================================================
  {
    const g = island(-70, 17, 4.1);
    // Central plaza + converging paths
    const plaza = new T.Mesh(new T.CircleGeometry(3.2, 26), mat(PAPER));
    plaza.rotation.x = -Math.PI / 2;
    plaza.position.set(0, 0.03, 3);
    plaza.receiveShadow = true;
    g.add(plaza);
    cyl(g, 0.55, 0.75, 0.5, ISLAND_DARK, 0, 0.25, 3, 12);
    cyl(g, 0.32, 0.4, 0.7, BONE, 0, 0.75, 3, 10);
    blob(g, 0.28, SAGE_LIGHT, 0, 1.2, 3, 1, 1, 1);
    const path = (x, z, len, ry) => {
      const p = new T.Mesh(new T.BoxGeometry(1.7, 0.07, len), mat(PAPER));
      p.position.set(x, 0.05, z);
      p.rotation.y = ry;
      p.receiveShadow = true;
      g.add(p);
    };
    path(-4.6, -0.4, 10, 0.65);
    path(0, -2.5, 9, 0);
    path(4.8, -0.2, 10, -0.7);
    // Scholarship hall (left) with steps and pediment
    const hall = new T.Group();
    box(hall, 6.6, 2.7, 4.6, BONE, 0, 1.65, 0);
    box(hall, 7.2, 0.5, 5.2, FOREST, 0, 3.25, 0);
    cone(hall, 3.9, 1.9, FOREST_DEEP, 0, 4.4, 0, 4);
    for (let i = -2; i <= 2; i += 1) {
      cyl(hall, 0.17, 0.17, 2.4, BONE, i * 1.3, 1.5, 2.55, 8);
    }
    box(hall, 7.0, 0.3, 5.4, PAPER, 0, 0.15, 0.4);
    box(hall, 6.2, 0.3, 1.2, PAPER, 0, 0.45, 2.9);
    box(hall, 1.1, 1.5, 0.12, FOREST_DEEP, 0, 1.05, 2.32);
    box(hall, 1.5, 0.35, 0.1, AMBER, 0, 2.6, 2.36);
    hall.position.set(-9.0, 0, -4.0);
    hall.rotation.y = 0.55;
    g.add(hall);
    shadowDisc(g, 4.6, -9.0, -4.0, 0.08);
    // Summer campus (right): cabins with chimneys
    const camp = new T.Group();
    const cabin = (x, z, ry, s) => {
      const k = s || 1;
      box(camp, 1.8 * k, 1.15 * k, 1.5 * k, AMBER_DEEP, x, 0.58 * k, z, ry);
      cone(camp, 1.35 * k, 0.95 * k, FOREST, x, 1.62 * k, z, 4);
      box(camp, 0.22 * k, 0.6 * k, 0.22 * k, BONE, x + 0.5 * k, 1.75 * k, z);
      box(camp, 0.4 * k, 0.55 * k, 0.06 * k, 0x5e4312, x, 0.5 * k, z + 0.76 * k, ry);
    };
    cabin(0, 0, 0.2, 1.1);
    cabin(2.6, 1.7, -0.4, 0.9);
    cabin(-2.0, 2.0, 0.7, 0.85);
    tree(camp, 1.3, -2.0, 1.05);
    tree(camp, -2.8, -0.7, 0.85);
    tree(camp, 3.8, -0.5, 0.95);
    bush(camp, 0.6, 3.2, 1);
    camp.position.set(9.4, 0, -3.4);
    g.add(camp);
    // Competition arena (back): tiered ring, pennants
    const arena = new T.Group();
    cyl(arena, 3.9, 4.2, 0.9, BONE, 0, 0.45, 0, 22);
    cyl(arena, 3.3, 3.6, 0.9, PAPER, 0, 0.9, 0, 22);
    cyl(arena, 2.5, 2.5, 1.0, SAGE, 0, 1.15, 0, 22);
    cyl(arena, 0.12, 0.12, 2.6, BONE, 0, 2.4, 0, 8);
    const flag = new T.Mesh(new T.BoxGeometry(1.0, 0.55, 0.04), mat(AMBER));
    flag.position.set(0.55, 3.4, 0);
    arena.add(flag);
    wavers.push({ obj: flag, axis: "z", amp: 0.18, speed: 2.4, phase: 0 });
    for (let i = 0; i < 7; i += 1) {
      const a = (i / 7) * Math.PI * 2;
      const fx = Math.cos(a) * 3.8;
      const fz = Math.sin(a) * 3.8;
      cyl(arena, 0.05, 0.05, 1.7, INK, fx, 2.1, fz, 6);
      const pennant = new T.Mesh(new T.ConeGeometry(0.16, 0.55, 4), mat(i % 2 ? AMBER : SAGE));
      pennant.rotation.z = Math.PI / 2;
      pennant.position.set(fx + 0.3, 2.78, fz);
      arena.add(pennant);
      wavers.push({ obj: pennant, axis: "x", amp: 0.22, speed: jitter(2.6, 1), phase: i });
    }
    arena.position.set(0, 0, -10.2);
    g.add(arena);
    shadowDisc(g, 4.6, 0, -10.2, 0.08);
    // Grounds
    tree(g, -14, 4.4, 1.15);
    tree(g, 14.2, 3.6, 1.35);
    tree(g, -4.4, 9.2, 0.95);
    tree(g, 5.8, 8.6, 0.8);
    bush(g, -11.5, -0.5, 1.1);
    bush(g, 12.6, -1.4, 0.9);
    rock(g, -6.8, 6.8, 1.2);
    lantern(g, -2.4, 4.6);
    lantern(g, 2.6, 4.8);
    bird(0, 9.5, -70, 9, 0.35);
    bird(0, 11, -70, 12, -0.28);
  }

  // =======================================================================
  // Scene 3 (z = -140): the plan war-room
  // =======================================================================
  {
    const g = island(-140, 13, 8.9);
    const rug = new T.Mesh(new T.CircleGeometry(4.4, 28), mat(0xd3ddd2));
    rug.rotation.x = -Math.PI / 2;
    rug.position.set(0, 0.02, 0.4);
    rug.receiveShadow = true;
    g.add(rug);
    // The board on legs
    box(g, 9.4, 5.4, 0.22, AMBER_DEEP, 0, 3.2, -3.45);
    box(g, 8.8, 4.8, 0.3, FOREST, 0, 3.2, -3.28);
    cyl(g, 0.09, 0.11, 1.2, INK, -4.2, 0.6, -3.4, 6);
    cyl(g, 0.09, 0.11, 1.2, INK, 4.2, 0.6, -3.4, 6);
    const pins = [];
    const card = (x, y, tone, tag) => {
      box(g, 1.4, 0.95, 0.07, tone, x, y, -3.1);
      if (tag) box(g, 0.5, 0.16, 0.09, tag, x - 0.3, y + 0.28, -3.06);
      const pin = new T.Mesh(new T.SphereGeometry(0.09, 8, 8), mat(AMBER));
      pin.position.set(x, y + 0.4, -3.05);
      g.add(pin);
      pins.push(pin.position.clone());
    };
    card(-3.2, 4.4, BONE, AMBER);
    card(-1.0, 3.2, PAPER, SAGE);
    card(1.5, 4.6, BONE, null);
    card(3.1, 2.7, PAPER, AMBER);
    card(-2.7, 2.0, BONE, SAGE);
    card(0.7, 1.8, BONE, AMBER);
    // sticky notes
    box(g, 0.34, 0.34, 0.06, AMBER, 2.2, 3.6, -3.1, 0.1);
    box(g, 0.34, 0.34, 0.06, SAGE_LIGHT, -0.1, 4.7, -3.1, -0.12);
    box(g, 0.34, 0.34, 0.06, AMBER, -3.9, 3.3, -3.1, 0.2);
    const threadMat = new T.LineBasicMaterial({ color: AMBER });
    for (let i = 0; i < pins.length - 1; i += 1) {
      const geo = new T.BufferGeometry().setFromPoints([pins[i], pins[i + 1]]);
      g.add(new T.Line(geo, threadMat));
    }
    // Work table with laptop, mug, papers
    box(g, 4.6, 0.3, 2.1, AMBER_DEEP, 0, 1.15, 1.7);
    [[-2.0, 1.05], [2.0, 1.05], [-2.0, 2.35], [2.0, 2.35]].forEach((p) => {
      box(g, 0.24, 1.0, 0.24, FOREST_DEEP, p[0], 0.5, p[1]);
    });
    box(g, 1.2, 0.08, 0.85, INK, -0.7, 1.36, 1.7);
    const lid = box(g, 1.2, 0.8, 0.06, INK, -0.7, 1.74, 1.3);
    lid.rotation.x = -0.35;
    box(g, 0.9, 0.03, 0.65, BONE, 0.9, 1.33, 1.55, 0.25);
    box(g, 0.85, 0.03, 0.6, PAPER, 1.05, 1.36, 1.75, -0.15);
    cyl(g, 0.13, 0.11, 0.22, AMBER, 1.9, 1.42, 1.3, 10);
    // Filing cabinet
    box(g, 1.0, 1.6, 0.9, FOREST, 3.6, 0.8, 0.4);
    box(g, 0.5, 0.06, 0.08, AMBER, 3.6, 1.15, 0.86);
    box(g, 0.5, 0.06, 0.08, AMBER, 3.6, 0.65, 0.86);
    shadowDisc(g, 3.2, 0, 1.4, 0.08);
    // Grounds
    tree(g, 7.8, 4.4, 1.05);
    tree(g, -8.2, 2.6, 1.2);
    tree(g, -6.4, -5.2, 0.8);
    bush(g, 6.2, -4.4, 1);
    bush(g, -3.8, 6.4, 0.9);
    rock(g, 8.6, 0.2, 1.1);
    lantern(g, -5.2, 4.6);
  }

  // =======================================================================
  // Scene 4 (z = -210): the gate at dawn
  // =======================================================================
  {
    const g = island(-210, 15, 12.3);
    // Path through the arch
    const p = new T.Mesh(new T.BoxGeometry(2.8, 0.07, 17), mat(PAPER));
    p.position.set(0, 0.05, 3);
    p.receiveShadow = true;
    g.add(p);
    // Campus arch with molding + amber plaque
    const arch = new T.Group();
    box(arch, 1.5, 0.5, 1.5, PAPER, -3.1, 0.25, 0);
    box(arch, 1.5, 0.5, 1.5, PAPER, 3.1, 0.25, 0);
    box(arch, 1.25, 5.8, 1.25, BONE, -3.1, 3.3, 0);
    box(arch, 1.25, 5.8, 1.25, BONE, 3.1, 3.3, 0);
    box(arch, 1.45, 0.4, 1.45, PAPER, -3.1, 6.3, 0);
    box(arch, 1.45, 0.4, 1.45, PAPER, 3.1, 6.3, 0);
    box(arch, 8.8, 1.2, 1.5, BONE, 0, 7.1, 0);
    box(arch, 9.2, 0.5, 1.7, FOREST, 0, 7.95, 0);
    box(arch, 1.7, 0.55, 0.2, AMBER, 0, 6.1, 0.78);
    // ivy
    for (let i = 0; i < 5; i += 1) {
      blob(arch, jitter(0.4, 0.2), i % 2 ? SAGE : FOREST, jitter(-3.1, 0.9), jitter(2.4, 2.6), 0.65, 1.1, 0.9, 0.5);
      blob(arch, jitter(0.4, 0.2), i % 2 ? SAGE_LIGHT : SAGE, jitter(3.1, 0.9), jitter(3.2, 2.8), 0.65, 1.1, 0.9, 0.5);
    }
    arch.position.z = -3;
    g.add(arch);
    shadowDisc(g, 5.0, 0, -3, 0.08);
    // The award envelope
    const env = new T.Group();
    box(env, 2.6, 1.7, 0.16, BONE, 0, 0.85, 0);
    const flap = new T.Mesh(new T.ConeGeometry(1.34, 0.92, 4), mat(PAPER));
    flap.rotation.z = Math.PI;
    flap.rotation.y = Math.PI / 4;
    flap.position.set(0, 1.36, 0.03);
    env.add(flap);
    const seal = new T.Mesh(new T.CylinderGeometry(0.24, 0.24, 0.09, 14), mat(AMBER));
    seal.rotation.x = Math.PI / 2;
    seal.position.set(0, 0.78, 0.14);
    env.add(seal);
    env.position.set(2.1, 0, -0.9);
    env.rotation.y = -0.45;
    env.rotation.z = -0.05;
    g.add(env);
    shadowDisc(g, 1.7, 2.1, -0.8, 0.07);
    // Dawn: layered sun halo + warm light
    const sunCore = new T.Mesh(
      new T.CircleGeometry(6.2, 40),
      new T.MeshBasicMaterial({ color: 0xf3d9a4, transparent: true, opacity: 0.9 })
    );
    sunCore.position.set(0, 7.5, -23);
    g.add(sunCore);
    const sunHalo = new T.Mesh(
      new T.CircleGeometry(9.5, 40),
      new T.MeshBasicMaterial({ color: 0xf3e3c0, transparent: true, opacity: 0.45 })
    );
    sunHalo.position.set(0, 7.5, -23.5);
    g.add(sunHalo);
    const dawn = new T.PointLight(0xffd98a, 26, 46);
    dawn.position.set(0, 6.5, -11);
    g.add(dawn);
    // Lantern-lined approach
    lantern(g, -1.9, 5.5);
    lantern(g, 1.9, 7.5);
    lantern(g, -1.9, 9.5);
    // Grounds
    tree(g, -8.6, 1.4, 1.25);
    tree(g, 9.0, 2.8, 1.05);
    tree(g, -6.0, -6.8, 0.95);
    tree(g, 6.4, -7.2, 1.15);
    tree(g, -10.2, -3.0, 0.8);
    bush(g, -4.6, 3.8, 1.1);
    bush(g, 5.0, 5.2, 0.9);
    bush(g, 8.2, -3.6, 1);
    rock(g, -3.2, 8.6, 1.2);
    bird(0, 10, -210, 10, 0.3);
    bird(0, 12, -212, 14, -0.22);
  }

  // ---- Sky dressing between the islands ----
  cloud(-16, 14, -30, 1.2);
  cloud(18, 17, -55, 1.5);
  cloud(-20, 12, -100, 1.1);
  cloud(15, 16, -122, 1.3);
  cloud(-14, 15, -175, 1.4);
  cloud(19, 13, -195, 1);

  // ---- The one continuous camera flight (never reverses in z) ----
  const camPath = new T.CatmullRomCurve3([
    new T.Vector3(0.0, 8.5, 26),
    new T.Vector3(0.0, 5.0, 10),
    new T.Vector3(-2.5, 4.2, 4),
    new T.Vector3(5.5, 7.0, -18),
    new T.Vector3(15.0, 9.0, -48),
    new T.Vector3(2.0, 10.5, -62),
    new T.Vector3(-13.0, 8.0, -84),
    new T.Vector3(-7.0, 6.0, -118),
    new T.Vector3(0.5, 4.6, -134),
    new T.Vector3(-6.0, 6.5, -166),
    new T.Vector3(0.0, 3.8, -196),
    new T.Vector3(0.0, 5.2, -209),
    new T.Vector3(0.0, 11.0, -224),
  ]);

  const lookPath = new T.CatmullRomCurve3([
    new T.Vector3(0.0, 2.0, 4),
    new T.Vector3(0.0, 1.8, 0),
    new T.Vector3(0.0, 1.8, -1),
    new T.Vector3(0.0, 2.5, -55),
    new T.Vector3(-4.0, 2.0, -72),
    new T.Vector3(0.0, 2.0, -80),
    new T.Vector3(2.0, 2.5, -100),
    new T.Vector3(0.0, 3.0, -140),
    new T.Vector3(0.0, 3.1, -143),
    new T.Vector3(0.0, 3.0, -185),
    new T.Vector3(0.0, 4.5, -210),
    new T.Vector3(0.0, 6.0, -222),
    new T.Vector3(0.0, 8.0, -240),
  ]);

  // ---- Scroll plumbing: progress read inside rAF (no scroll listeners),
  // then damped for glide. ----
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

  function frame(nowMs) {
    const now = (nowMs || 0) * 0.001;
    const max = track.offsetHeight - window.innerHeight;
    target = max > 0 ? Math.min(1, Math.max(0, (window.scrollY - track.offsetTop) / max)) : 0;
    t += (target - t) * 0.07;

    camPath.getPointAt(t, camPos);
    lookPath.getPointAt(t, lookPos);
    camera.position.copy(camPos);
    camera.lookAt(lookPos);

    // The key light travels with the camera so shadow resolution stays
    // concentrated on whichever island is on screen.
    key.position.set(camPos.x + 24, camPos.y + 38, camPos.z + 16);
    key.target.position.set(lookPos.x, 0, lookPos.z);

    // Idle life
    for (const b of bobbers) b.obj.position.y = Math.sin(now * b.speed + b.phase) * b.amp;
    for (const w of wavers) w.obj.rotation[w.axis] = Math.sin(now * w.speed + w.phase) * w.amp;
    for (const d of drifters) {
      d.obj.position.x += d.speed * 0.016;
      if (d.obj.position.x > d.maxX) d.obj.position.x = d.minX;
    }
    for (const o of orbiters) {
      const a = now * o.speed + o.phase;
      o.obj.position.set(
        o.center.x + Math.cos(a) * o.radius,
        o.center.y + Math.sin(now * 0.7 + o.phase) * 0.6,
        o.center.z + Math.sin(a) * o.radius
      );
      o.obj.rotation.y = -a + (o.speed > 0 ? 0 : Math.PI);
    }
    for (const f of flappers) {
      const w = Math.sin(now * f.speed + f.phase) * 0.55;
      f.left.rotation.z = w;
      f.right.rotation.z = -w;
    }

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
