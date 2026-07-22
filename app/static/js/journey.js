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

  const saveData =
    !!(navigator.connection && navigator.connection.saveData) ||
    root.classList.contains("save-data");

  if (!track || !canvas || reduceMotion || saveData || !webgl) {
    root.classList.add("journey-static");
    return;
  }

  // Three.js loads only after the gates pass: reduced-motion, Save-Data,
  // and no-WebGL visitors read the static page without paying the vendor
  // download. Failure to load degrades to the same static mode.
  const boot = () => {
    if (!window.THREE) {
      root.classList.add("journey-static");
      return;
    }
    init();
  };
  if (window.THREE) {
    boot();
  } else {
    const vendor = document.createElement("script");
    vendor.src = "/static/js/vendor/three.min.js?v=20260721-6";
    vendor.onload = boot;
    vendor.onerror = () => root.classList.add("journey-static");
    document.head.appendChild(vendor);
  }

  function init() {
  const T = window.THREE;

  // ---- Palette (style.css tokens, hex-locked) ----
  const CANVAS = 0xf1f2ee;
  const ISLAND = 0x94c082;      // grass
  const ISLAND_DARK = 0x9c7f63; // soil under the grass
  const GRASS_TONES = [0x86b877, 0xa4cf90, 0x76a06d, 0x9fca7e];
  const STONE = 0xb3a48f;
  const FOREST = 0x1e4034;
  const FOREST_DEEP = 0x132d24;
  const BONE = 0xfbfcfa;
  const PAPER = 0xe8ece6;
  const INK = 0x16211b;
  const AMBER = 0xc98d2c;
  const AMBER_DEEP = 0x8a5e14;
  const SAGE = 0x8fb98a;
  const SAGE_LIGHT = 0xb5d0af;
  // Extended illustration palette (scene content only; UI chrome stays amber)
  const TEAL = 0x2f6d62;
  const TEAL_LIGHT = 0x5d998c;
  const BERRY = 0xa84d5e;
  const ROSE = 0xd08a97;
  const TERRACOTTA = 0xb96a45;
  const GOLD = 0xd9a441;
  const CREAM = 0xf3e8cf;
  const PEACH = 0xf2c49a;
  const MOSS = 0x76a06d;
  const AUTUMN = 0xcf8a3d;
  // Tree base tier: deep enough to give the canopy depth, close enough to the
  // tier above that the step does not read as a hard band.
  const TREE_BASE = 0x3d7a58;

  const renderer = new T.WebGLRenderer({ canvas, antialias: true });
  renderer.setClearColor(CANVAS, 1);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = T.PCFSoftShadowMap;

  const scene = new T.Scene();
  scene.fog = new T.Fog(CANVAS, 48, 135);

  const camera = new T.PerspectiveCamera(42, 1, 0.1, 400);

  // ---- Sky dome: gradient that rides with the camera and warms toward
  // dawn as the flight nears the gate. Fog color tracks the horizon so the
  // distance fade never mismatches the sky. ----
  const SKY_DAY_TOP = new T.Color(0x9ccadf);
  const SKY_DAY_HORIZON = new T.Color(CANVAS);
  const SKY_DAWN_TOP = new T.Color(0xdba98a);
  const SKY_DAWN_HORIZON = new T.Color(0xf6d9b8);
  const skyMat = new T.ShaderMaterial({
    side: T.BackSide,
    depthWrite: false,
    fog: false,
    uniforms: {
      topColor: { value: SKY_DAY_TOP.clone() },
      horizonColor: { value: SKY_DAY_HORIZON.clone() },
    },
    vertexShader:
      "varying float vH;\n" +
      "void main() {\n" +
      "  vH = clamp(position.y / 300.0, 0.0, 1.0);\n" +
      "  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);\n" +
      "}",
    fragmentShader:
      "uniform vec3 topColor;\n" +
      "uniform vec3 horizonColor;\n" +
      "varying float vH;\n" +
      "void main() {\n" +
      "  float k = pow(smoothstep(0.0, 1.0, vH), 0.62);\n" +
      "  gl_FragColor = vec4(mix(horizonColor, topColor, k), 1.0);\n" +
      "}",
  });
  const sky = new T.Mesh(new T.SphereGeometry(300, 24, 16), skyMat);
  sky.renderOrder = -1;
  scene.add(sky);
  const skyTop = new T.Color();
  const skyHorizon = new T.Color();

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
  const dawnFaders = []; // {mesh, base}: sun discs fade in with the dawn

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

    // The soil keel must stay UNDER the grass, never poking out past the
    // coastline. The grass plateau is noised outward up to ~1.13x, so the keel
    // is cut well inside that (0.72) and its taper starts below the rim.
    const base = new T.Mesh(
      new T.ConeGeometry(radius * 0.72, radius * 0.62, 14),
      mat(ISLAND_DARK)
    );
    base.rotation.x = Math.PI;
    base.position.y = -2.6 - radius * 0.31;
    g.add(base);

    // Mottled meadow: irregular patches of neighbouring greens
    for (let i = 0; i < 6; i += 1) {
      const pr = jitter(radius * 0.16, radius * 0.12);
      const pa = rnd() * Math.PI * 2;
      const pd = rnd() * radius * 0.62;
      const patch = new T.Mesh(
        new T.CircleGeometry(pr, 10),
        mat(GRASS_TONES[i % GRASS_TONES.length])
      );
      patch.rotation.x = -Math.PI / 2;
      patch.rotation.z = rnd() * 3;
      patch.scale.x = jitter(1.25, 0.4);
      patch.position.set(Math.cos(pa) * pd, 0.012 + i * 0.002, Math.sin(pa) * pd);
      patch.receiveShadow = true;
      g.add(patch);
    }
    // Grass tufts
    const tufts = Math.round(radius * 1.6);
    for (let i = 0; i < tufts; i += 1) {
      const ta = rnd() * Math.PI * 2;
      const td = radius * (0.3 + rnd() * 0.6);
      const tuft = new T.Mesh(
        new T.ConeGeometry(jitter(0.09, 0.04), jitter(0.3, 0.14), 5),
        mat(GRASS_TONES[Math.floor(rnd() * GRASS_TONES.length)])
      );
      tuft.position.set(Math.cos(ta) * td, 0.12, Math.sin(ta) * td);
      tuft.rotation.z = (rnd() - 0.5) * 0.25;
      g.add(tuft);
    }

    g.position.z = z;
    scene.add(g);
    bobbers.push({ obj: g, amp: 0.22, speed: jitter(0.4, 0.15), phase: phase * 2 });
    return g;
  }

  function tree(parent, x, z, s, kind) {
    const k = (s || 1) * jitter(1, 0.25);
    const lean = (rnd() - 0.5) * 0.12;
    const grp = new T.Group();
    cyl(grp, 0.12 * k, 0.17 * k, 0.8 * k, AMBER_DEEP, 0, 0.4 * k, 0, 6);
    // Tiers run light at the base to light at the tip. The old bottom tier was
    // near-black forest against a mid sage above it, and the jump read as a
    // hard band; MOSS keeps the foliage reading as one tree.
    let tiers;
    if (kind === "autumn") {
      tiers = [AUTUMN, jitter(0.5, 1) > 0.5 ? TERRACOTTA : AUTUMN, GOLD];
    } else if (kind === "moss") {
      tiers = [MOSS, SAGE, SAGE_LIGHT];
    } else {
      tiers = [TREE_BASE, SAGE, SAGE_LIGHT];
    }
    cone(grp, 0.8 * k, 1.4 * k, tiers[0], 0, 1.35 * k, 0, 7);
    cone(grp, 0.62 * k, 1.15 * k, tiers[1], 0, 2.05 * k, 0, 7);
    cone(grp, 0.4 * k, 0.85 * k, tiers[2], 0, 2.7 * k, 0, 7);
    grp.position.set(x, 0, z);
    grp.rotation.z = lean;
    parent.add(grp);
    shadowDisc(parent, 0.9 * k, x, z);
    return grp;
  }

  const FLOWER_TONES = [0xd9788a, GOLD, CREAM, TEAL_LIGHT, ROSE];

  function flowerBed(parent, x, z, r) {
    const k = r || 1;
    const bed = new T.Mesh(new T.CircleGeometry(0.85 * k, 14), mat(MOSS));
    bed.rotation.x = -Math.PI / 2;
    bed.position.set(x, 0.025, z);
    bed.receiveShadow = true;
    parent.add(bed);
    const count = 5 + Math.floor(rnd() * 4);
    for (let i = 0; i < count; i += 1) {
      const a = rnd() * Math.PI * 2;
      const rr = rnd() * 0.6 * k;
      const tone = FLOWER_TONES[Math.floor(rnd() * FLOWER_TONES.length)];
      cyl(parent, 0.018, 0.018, 0.22, FOREST, x + Math.cos(a) * rr, 0.11, z + Math.sin(a) * rr, 5);
      blob(parent, 0.075, tone, x + Math.cos(a) * rr, 0.26, z + Math.sin(a) * rr, 1, 0.8, 1);
    }
  }

  function fence(parent, x, z, len, ry) {
    const grp = new T.Group();
    const posts = Math.max(2, Math.round(len / 0.7));
    for (let i = 0; i < posts; i += 1) {
      box(grp, 0.09, 0.55, 0.09, CREAM, -len / 2 + (i / (posts - 1)) * len, 0.28, 0);
    }
    box(grp, len, 0.07, 0.06, CREAM, 0, 0.42, 0);
    box(grp, len, 0.07, 0.06, CREAM, 0, 0.2, 0);
    grp.position.set(x, 0, z);
    grp.rotation.y = ry || 0;
    parent.add(grp);
    return grp;
  }

  function bench(parent, x, z, ry, tone) {
    const grp = new T.Group();
    box(grp, 1.4, 0.09, 0.45, tone || TEAL, 0, 0.42, 0);
    box(grp, 1.4, 0.4, 0.08, tone || TEAL, 0, 0.7, -0.2);
    box(grp, 0.09, 0.4, 0.4, INK, -0.6, 0.2, 0);
    box(grp, 0.09, 0.4, 0.4, INK, 0.6, 0.2, 0);
    grp.position.set(x, 0, z);
    grp.rotation.y = ry || 0;
    parent.add(grp);
    shadowDisc(parent, 0.8, x, z);
    return grp;
  }

  function butterfly(cx, cy, cz, radius, speed, tone) {
    const g = new T.Group();
    const wingMat = mat(tone);
    const left = new T.Mesh(new T.BoxGeometry(0.26, 0.02, 0.18), wingMat);
    const right = new T.Mesh(new T.BoxGeometry(0.26, 0.02, 0.18), wingMat);
    left.position.x = -0.13;
    right.position.x = 0.13;
    g.add(left);
    g.add(right);
    scene.add(g);
    orbiters.push({ obj: g, center: new T.Vector3(cx, cy, cz), radius, speed, phase: rnd() * 6.28 });
    flappers.push({ left, right, speed: jitter(14, 4), phase: rnd() * 6.28 });
  }

  function bush(parent, x, z, s) {
    const k = (s || 1) * jitter(1, 0.3);
    blob(parent, 0.5 * k, rnd() > 0.5 ? SAGE : SAGE_LIGHT, x, 0.35 * k, z, 1.3, 0.8, 1.1);
    shadowDisc(parent, 0.55 * k, x, z);
  }

  function rock(parent, x, z, s) {
    const k = (s || 1) * jitter(1, 0.4);
    blob(parent, 0.32 * k, STONE, x, 0.2 * k, z, 1.2, 0.7, 1);
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
    // Two-tone rug
    const rug = new T.Mesh(new T.CircleGeometry(3.6, 28), mat(TEAL_LIGHT));
    rug.rotation.x = -Math.PI / 2;
    rug.position.y = 0.02;
    rug.receiveShadow = true;
    g.add(rug);
    const rugInner = new T.Mesh(new T.CircleGeometry(2.7, 28), mat(CREAM));
    rugInner.rotation.x = -Math.PI / 2;
    rugInner.position.y = 0.03;
    rugInner.receiveShadow = true;
    g.add(rugInner);
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
    box(g, 0.9, 0.2, 0.62, TEAL, 1.55, 1.86, -0.62, 0.3);
    box(g, 0.8, 0.18, 0.56, BERRY, 1.48, 2.05, -0.6, 0.12);
    box(g, 0.72, 0.16, 0.5, GOLD, 1.52, 2.22, -0.58, 0.45);
    cyl(g, 0.14, 0.12, 0.24, BERRY, -1.15, 1.87, 0.85, 10);
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
    // The mailbox where applications leave
    const mailbox = new T.Group();
    cyl(mailbox, 0.06, 0.08, 1.1, INK, 0, 0.55, 0, 6);
    box(mailbox, 0.55, 0.4, 0.35, BERRY, 0, 1.28, 0);
    const mtop = cyl(mailbox, 0.175, 0.175, 0.55, BERRY, 0, 1.48, 0, 10);
    mtop.rotation.z = Math.PI / 2;
    const mflag = box(mailbox, 0.05, 0.3, 0.08, GOLD, 0.3, 1.55, 0);
    mflag.rotation.z = -0.3;
    mailbox.position.set(-3.6, 0, 2.6);
    mailbox.rotation.y = 0.6;
    g.add(mailbox);
    shadowDisc(g, 0.5, -3.6, 2.6);
    // Grounds
    tree(g, -6.8, 3.2, 1.25);
    tree(g, -5.4, -4.6, 0.9, "moss");
    tree(g, 6.9, -3.6, 1.0);
    tree(g, 7.6, 2.6, 0.7, "autumn");
    bush(g, -4.2, 5.6, 1);
    bush(g, 5.2, 4.8, 1.2);
    bush(g, -7.9, -1.2, 0.8);
    rock(g, 3.9, -5.8, 1.3);
    rock(g, -2.5, -6.9, 1);
    lantern(g, 3.2, 3.4);
    flowerBed(g, 4.8, 1.2, 1);
    flowerBed(g, -6.2, 0.9, 0.8);
    bench(g, 5.9, -1.4, -0.8, TEAL);
    butterfly(-2, 2.6, 1.5, 2.2, 0.9, ROSE);
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
    cyl(g, 0.55, 0.75, 0.5, STONE, 0, 0.25, 3, 12);
    cyl(g, 0.32, 0.4, 0.7, BONE, 0, 0.75, 3, 10);
    blob(g, 0.28, TEAL_LIGHT, 0, 1.2, 3, 1, 1, 1);
    flowerBed(g, 1.9, 4.6, 0.9);
    flowerBed(g, -2.1, 4.4, 0.9);
    bench(g, 3.4, 3.2, -2.2, BERRY);
    bench(g, -3.5, 3.0, 2.2, GOLD);
    const path = (x, z, len, ry) => {
      // Marigold trail dots, the world's wayfinding motif: the same dotted
      // amber line the plates and the landing Trail draw, not solid paving.
      const trail = new T.Group();
      const count = Math.max(2, Math.round(len / 0.62));
      for (let i = 0; i < count; i += 1) {
        const t = count === 1 ? 0.5 : i / (count - 1);
        const r = 0.1 + (i % 3) * 0.022;
        const dot = new T.Mesh(
          new T.CylinderGeometry(r, r + 0.02, 0.05, 8),
          mat(i % 4 === 3 ? GOLD : AMBER)
        );
        dot.position.set(i % 2 ? 0.16 : -0.12, 0.05, len / 2 - t * len);
        trail.add(dot);
      }
      trail.position.set(x, 0.02, z);
      trail.rotation.y = ry;
      g.add(trail);
    };
    path(-4.6, -0.4, 10, 0.65);
    path(0, -2.5, 9, 0);
    path(4.8, -0.2, 10, -0.7);
    // Scholarship hall (left): the GOLD lane
    const hall = new T.Group();
    box(hall, 6.6, 2.7, 4.6, BONE, 0, 1.65, 0);
    box(hall, 7.2, 0.5, 5.2, TEAL, 0, 3.25, 0);
    cone(hall, 3.9, 1.9, TEAL, 0, 4.4, 0, 4);
    const dome = new T.Mesh(new T.SphereGeometry(0.85, 12, 8), mat(GOLD));
    dome.position.set(0, 5.4, 0);
    hall.add(dome);
    cyl(hall, 0.05, 0.05, 0.7, GOLD, 0, 6.35, 0, 6);
    for (let i = -2; i <= 2; i += 1) {
      cyl(hall, 0.17, 0.17, 2.4, BONE, i * 1.3, 1.5, 2.55, 8);
    }
    box(hall, 7.0, 0.3, 5.4, PAPER, 0, 0.15, 0.4);
    box(hall, 6.2, 0.3, 1.2, PAPER, 0, 0.45, 2.9);
    box(hall, 1.1, 1.5, 0.12, FOREST_DEEP, 0, 1.05, 2.32);
    box(hall, 1.5, 0.35, 0.1, GOLD, 0, 2.6, 2.36);
    // Hanging gold banners between the columns
    const hb1 = box(hall, 0.55, 1.3, 0.05, GOLD, -1.95, 1.9, 2.6);
    const hb2 = box(hall, 0.55, 1.3, 0.05, AMBER, 1.95, 1.9, 2.6);
    wavers.push({ obj: hb1, axis: "x", amp: 0.08, speed: 1.8, phase: 0.4 });
    wavers.push({ obj: hb2, axis: "x", amp: 0.08, speed: 2.1, phase: 1.7 });
    hall.position.set(-9.0, 0, -4.0);
    hall.rotation.y = 0.55;
    g.add(hall);
    shadowDisc(g, 4.6, -9.0, -4.0, 0.08);
    // Summer campus (right): the TEAL lane, terracotta roofs
    const camp = new T.Group();
    const cabin = (x, z, ry, s) => {
      const k = s || 1;
      box(camp, 1.8 * k, 1.15 * k, 1.5 * k, CREAM, x, 0.58 * k, z, ry);
      cone(camp, 1.35 * k, 0.95 * k, TERRACOTTA, x, 1.62 * k, z, 4);
      box(camp, 0.22 * k, 0.6 * k, 0.22 * k, BONE, x + 0.5 * k, 1.75 * k, z);
      box(camp, 0.4 * k, 0.55 * k, 0.06 * k, TEAL, x, 0.5 * k, z + 0.76 * k, ry);
      box(camp, 0.32 * k, 0.32 * k, 0.05 * k, TEAL_LIGHT, x - 0.5 * k, 0.75 * k, z + 0.76 * k, ry);
      box(camp, 0.4 * k, 0.08 * k, 0.12 * k, MOSS, x - 0.5 * k, 0.55 * k, z + 0.8 * k, ry);
    };
    cabin(0, 0, 0.2, 1.1);
    cabin(2.6, 1.7, -0.4, 0.9);
    cabin(-2.0, 2.0, 0.7, 0.85);
    // Teal campus flag
    cyl(camp, 0.05, 0.05, 2.4, INK, 0.9, 1.2, 1.1, 6);
    const campFlag = box(camp, 0.8, 0.45, 0.04, TEAL, 1.32, 2.2, 1.1);
    wavers.push({ obj: campFlag, axis: "z", amp: 0.16, speed: 2.2, phase: 0.9 });
    tree(camp, 1.3, -2.0, 1.05);
    tree(camp, -2.8, -0.7, 0.85, "autumn");
    tree(camp, 3.8, -0.5, 0.95);
    bush(camp, 0.6, 3.2, 1);
    flowerBed(camp, -0.9, 3.4, 0.7);
    camp.position.set(9.4, 0, -3.4);
    g.add(camp);
    // Competition arena (back): the BERRY lane, tiered ring, pennants
    const arena = new T.Group();
    cyl(arena, 3.9, 4.2, 0.9, BONE, 0, 0.45, 0, 22);
    cyl(arena, 3.3, 3.6, 0.9, CREAM, 0, 0.9, 0, 22);
    cyl(arena, 2.5, 2.5, 1.0, BERRY, 0, 1.15, 0, 22);
    cyl(arena, 1.7, 1.7, 1.06, MOSS, 0, 1.2, 0, 22);
    cyl(arena, 0.12, 0.12, 2.6, BONE, 0, 2.4, 0, 8);
    const flag = new T.Mesh(new T.BoxGeometry(1.0, 0.55, 0.04), mat(BERRY));
    flag.position.set(0.55, 3.4, 0);
    arena.add(flag);
    wavers.push({ obj: flag, axis: "z", amp: 0.18, speed: 2.4, phase: 0 });
    const PENNANT_TONES = [BERRY, CREAM, GOLD, ROSE];
    for (let i = 0; i < 7; i += 1) {
      const a = (i / 7) * Math.PI * 2;
      const fx = Math.cos(a) * 3.8;
      const fz = Math.sin(a) * 3.8;
      cyl(arena, 0.05, 0.05, 1.7, INK, fx, 2.1, fz, 6);
      const pennant = new T.Mesh(
        new T.ConeGeometry(0.16, 0.55, 4),
        mat(PENNANT_TONES[i % PENNANT_TONES.length])
      );
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
    tree(g, 14.2, 3.6, 1.35, "autumn");
    tree(g, -4.4, 9.2, 0.95, "moss");
    tree(g, 5.8, 8.6, 0.8);
    bush(g, -11.5, -0.5, 1.1);
    bush(g, 12.6, -1.4, 0.9);
    rock(g, -6.8, 6.8, 1.2);
    lantern(g, -2.4, 4.6);
    lantern(g, 2.6, 4.8);
    fence(g, -6.2, 7.6, 3.4, 0.55);
    fence(g, 7.0, 7.2, 3.4, -0.6);
    flowerBed(g, -9.2, 6.0, 1.1);
    flowerBed(g, 10.4, 5.4, 1);
    bird(0, 9.5, -70, 9, 0.35);
    bird(0, 11, -70, 12, -0.28);
    butterfly(0, 3, -66, 3.4, 0.7, GOLD);
    butterfly(8, 2.6, -73, 2.6, -0.8, TEAL_LIGHT);
  }

  // =======================================================================
  // Scene 3 (z = -140): the plan war-room
  // =======================================================================
  {
    const g = island(-140, 13, 8.9);
    const rug = new T.Mesh(new T.CircleGeometry(4.4, 28), mat(TEAL));
    rug.rotation.x = -Math.PI / 2;
    rug.position.set(0, 0.02, 0.4);
    rug.receiveShadow = true;
    g.add(rug);
    const rugIn = new T.Mesh(new T.CircleGeometry(3.4, 28), mat(CREAM));
    rugIn.rotation.x = -Math.PI / 2;
    rugIn.position.set(0, 0.03, 0.4);
    rugIn.receiveShadow = true;
    g.add(rugIn);
    // The board on legs
    box(g, 9.4, 5.4, 0.22, AMBER_DEEP, 0, 3.2, -3.45);
    box(g, 8.8, 4.8, 0.3, FOREST, 0, 3.2, -3.28);
    cyl(g, 0.09, 0.11, 1.2, INK, -4.2, 0.6, -3.4, 6);
    cyl(g, 0.09, 0.11, 1.2, INK, 4.2, 0.6, -3.4, 6);
    // Cards carry status colors, like the plan itself: gold = drafting,
    // teal = submitted, berry = deadline soon.
    const pins = [];
    const card = (x, y, tone, tag, pinTone) => {
      box(g, 1.4, 0.95, 0.07, tone, x, y, -3.1);
      if (tag) box(g, 0.5, 0.16, 0.09, tag, x - 0.3, y + 0.28, -3.06);
      const pin = new T.Mesh(new T.SphereGeometry(0.09, 8, 8), mat(pinTone || AMBER));
      pin.position.set(x, y + 0.4, -3.05);
      g.add(pin);
      pins.push(pin.position.clone());
    };
    card(-3.2, 4.4, BONE, GOLD, GOLD);
    card(-1.0, 3.2, CREAM, TEAL, TEAL_LIGHT);
    card(1.5, 4.6, BONE, BERRY, BERRY);
    card(3.1, 2.7, CREAM, GOLD, GOLD);
    card(-2.7, 2.0, BONE, TEAL, TEAL_LIGHT);
    card(0.7, 1.8, BONE, BERRY, BERRY);
    // sticky notes
    box(g, 0.34, 0.34, 0.06, GOLD, 2.2, 3.6, -3.1, 0.1);
    box(g, 0.34, 0.34, 0.06, ROSE, -0.1, 4.7, -3.1, -0.12);
    box(g, 0.34, 0.34, 0.06, TEAL_LIGHT, -3.9, 3.3, -3.1, 0.2);
    box(g, 0.34, 0.34, 0.06, GOLD, 3.9, 4.2, -3.1, -0.18);
    const threadTones = [AMBER, TEAL_LIGHT, BERRY];
    for (let i = 0; i < pins.length - 1; i += 1) {
      const geo = new T.BufferGeometry().setFromPoints([pins[i], pins[i + 1]]);
      g.add(new T.Line(geo, new T.LineBasicMaterial({ color: threadTones[i % 3] })));
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
    cyl(g, 0.13, 0.11, 0.22, TEAL, 1.9, 1.42, 1.3, 10);
    // Book stack on the table corner
    box(g, 0.6, 0.14, 0.44, BERRY, -1.7, 1.38, 2.1, 0.2);
    box(g, 0.55, 0.13, 0.4, GOLD, -1.66, 1.51, 2.08, -0.1);
    box(g, 0.5, 0.12, 0.36, TEAL, -1.72, 1.63, 2.12, 0.35);
    // Filing cabinet
    box(g, 1.0, 1.6, 0.9, TEAL, 3.6, 0.8, 0.4);
    box(g, 0.5, 0.06, 0.08, GOLD, 3.6, 1.15, 0.86);
    box(g, 0.5, 0.06, 0.08, GOLD, 3.6, 0.65, 0.86);
    shadowDisc(g, 3.2, 0, 1.4, 0.08);
    // Grounds
    tree(g, 7.8, 4.4, 1.05, "autumn");
    tree(g, -8.2, 2.6, 1.2);
    tree(g, -6.4, -5.2, 0.8, "moss");
    bush(g, 6.2, -4.4, 1);
    bush(g, -3.8, 6.4, 0.9);
    rock(g, 8.6, 0.2, 1.1);
    lantern(g, -5.2, 4.6);
    flowerBed(g, 6.4, 2.8, 0.9);
    bench(g, -6.8, 5.6, 2.4, BERRY);
    butterfly(2, 3.2, -137, 2.8, 0.85, ROSE);
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
    // Dawn: triple-layered peach sun + warm light
    const sunCore = new T.Mesh(
      new T.CircleGeometry(5.6, 40),
      new T.MeshBasicMaterial({ color: 0xf5cf94, transparent: true, opacity: 0.95 })
    );
    sunCore.position.set(0, 7.5, -23);
    g.add(sunCore);
    const sunMid = new T.Mesh(
      new T.CircleGeometry(8.2, 40),
      new T.MeshBasicMaterial({ color: PEACH, transparent: true, opacity: 0.55 })
    );
    sunMid.position.set(0, 7.5, -23.4);
    g.add(sunMid);
    const sunHalo = new T.Mesh(
      new T.CircleGeometry(11.5, 40),
      new T.MeshBasicMaterial({ color: 0xf6dcc4, transparent: true, opacity: 0.32 })
    );
    sunHalo.position.set(0, 7.5, -23.8);
    g.add(sunHalo);
    dawnFaders.push({ mesh: sunCore, base: 0.95 });
    dawnFaders.push({ mesh: sunMid, base: 0.55 });
    dawnFaders.push({ mesh: sunHalo, base: 0.32 });
    // Petals scattered along the approach
    for (let i = 0; i < 16; i += 1) {
      const tone = [BERRY, GOLD, ROSE, CREAM][i % 4];
      const petal = box(g, 0.14, 0.02, 0.1, tone, jitter(0, 3.4), 0.06, jitter(5, 8));
      petal.rotation.y = rnd() * 3;
      petal.castShadow = false;
    }
    const dawn = new T.PointLight(0xffd98a, 26, 46);
    dawn.position.set(0, 6.5, -11);
    g.add(dawn);
    // Lantern-lined approach
    lantern(g, -1.9, 5.5);
    lantern(g, 1.9, 7.5);
    lantern(g, -1.9, 9.5);
    // Grounds: autumn frames the gate
    tree(g, -8.6, 1.4, 1.25, "autumn");
    tree(g, 9.0, 2.8, 1.05, "autumn");
    tree(g, -6.0, -6.8, 0.95);
    tree(g, 6.4, -7.2, 1.15, "moss");
    tree(g, -10.2, -3.0, 0.8, "autumn");
    tree(g, 10.6, -1.6, 0.75);
    bush(g, -4.6, 3.8, 1.1);
    bush(g, 5.0, 5.2, 0.9);
    bush(g, 8.2, -3.6, 1);
    rock(g, -3.2, 8.6, 1.2);
    fence(g, -5.4, 6.8, 3.2, 0.5);
    fence(g, 5.6, 7.4, 3.2, -0.45);
    flowerBed(g, -6.8, 4.6, 1.1);
    flowerBed(g, 7.2, 5.8, 1);
    bench(g, -4.4, 9.4, 2.8, GOLD);
    bird(0, 10, -210, 10, 0.3);
    bird(0, 12, -212, 14, -0.22);
    butterfly(0, 3.5, -204, 3, 0.75, ROSE);
    butterfly(-4, 2.8, -208, 2.4, -0.9, GOLD);
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
  const dots = Array.from(document.querySelectorAll(".journey-rail button"));

  // Rail stops fly the camera to an island: scroll to the point on the track
  // whose flight progress matches that stop, and let the existing damping
  // carry the camera there as a real move rather than a cut.
  for (const dot of dots) {
    dot.addEventListener("click", () => {
      const stop = parseFloat(dot.dataset.stop || "0");
      const max = track.offsetHeight - window.innerHeight;
      window.scrollTo({ top: track.offsetTop + max * stop, behavior: "smooth" });
    });
  }

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

    // The sky rides along and eases from day blue into dawn peach over the
    // last stretch of the flight; the fog horizon follows it.
    sky.position.set(camPos.x, 0, camPos.z);
    const dawnK = Math.min(1, Math.max(0, (t - 0.72) / 0.23));
    skyTop.lerpColors(SKY_DAY_TOP, SKY_DAWN_TOP, dawnK);
    skyHorizon.lerpColors(SKY_DAY_HORIZON, SKY_DAWN_HORIZON, dawnK);
    skyMat.uniforms.topColor.value.copy(skyTop);
    skyMat.uniforms.horizonColor.value.copy(skyHorizon);
    scene.fog.color.copy(skyHorizon);
    const sunK = Math.min(1, Math.max(0, (t - 0.55) / 0.3));
    for (const f of dawnFaders) f.mesh.material.opacity = f.base * sunK;

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
  }
})();
