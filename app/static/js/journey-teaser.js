/* Landing-page journey teaser, painting-first: the overlook plate is the
   guaranteed visual (hydrated by app.js with the other world plates); the
   live miniature island is a progressive enhancement that loads three.js on
   idle once the section approaches the viewport, then fades in over the
   painting inside the same box so nothing painted ever moves. Reduced
   motion, Save-Data, and low-end devices keep the painting. */
(() => {
  const canvas = document.getElementById("journey-teaser-canvas");
  const section = document.querySelector(".journey-teaser");
  if (!canvas || !section) return;

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const saveData = !!(navigator.connection && navigator.connection.saveData);
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
    s.src = "/static/js/vendor/three.min.js?v=20260721-4";
    s.onload = cb;
    document.head.appendChild(s);
  }

  function init() {
    const T = window.THREE;

    const GRASS = 0x94c082;
    const GRASS_TONES = [0x86b877, 0xa4cf90, 0x76a06d];
    const SOIL = 0x9c7f63;
    const FOREST = 0x1e4034;
    const FOREST_DEEP = 0x132d24;
    const BONE = 0xfbfcfa;
    const INK = 0x16211b;
    const AMBER = 0xc98d2c;
    const AMBER_DEEP = 0x8a5e14;
    const SAGE = 0x8fb98a;
    const SAGE_LIGHT = 0xb5d0af;
    const BERRY = 0xa84d5e;
    const TEAL = 0x2f6d62;

    const renderer = new T.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setClearColor(0x000000, 0);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));

    const scene = new T.Scene();
    const camera = new T.PerspectiveCamera(38, 1, 0.1, 100);

    scene.add(new T.HemisphereLight(0xfffdf6, 0x24463a, 1.0));
    const key = new T.DirectionalLight(0xffe9c4, 1.5);
    key.position.set(14, 20, 10);
    scene.add(key);
    const rim = new T.PointLight(0xffc65e, 14, 22);
    rim.position.set(-3, 6, 2);
    scene.add(rim);

    const world = new T.Group();
    scene.add(world);

    const mat = (color) => new T.MeshLambertMaterial({ color });
    let seed = 5;
    const rnd = () => {
      seed = (seed * 16807) % 2147483647;
      return (seed - 1) / 2147483646;
    };

    function box(w, h, d, color, x, y, z, ry) {
      const m = new T.Mesh(new T.BoxGeometry(w, h, d), mat(color));
      m.position.set(x, y, z);
      if (ry) m.rotation.y = ry;
      world.add(m);
      return m;
    }
    function cyl(rt, rb, h, color, x, y, z, seg) {
      const m = new T.Mesh(new T.CylinderGeometry(rt, rb, h, seg || 12), mat(color));
      m.position.set(x, y, z);
      world.add(m);
      return m;
    }
    function cone(r, h, color, x, y, z) {
      const m = new T.Mesh(new T.ConeGeometry(r, h, 7), mat(color));
      m.position.set(x, y, z);
      world.add(m);
      return m;
    }

    // Island with a noisy coastline
    const geo = new T.CylinderGeometry(7, 6.4, 1.9, 26, 2);
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
    const top = new T.Mesh(geo, mat(GRASS));
    top.position.y = -0.95;
    world.add(top);
    const base = new T.Mesh(new T.ConeGeometry(6, 4.4, 10), mat(SOIL));
    base.rotation.x = Math.PI;
    base.position.y = -4.1;
    world.add(base);
    for (let i = 0; i < 4; i += 1) {
      const pr = 0.9 + rnd() * 1.2;
      const pa = rnd() * 6.28;
      const pd = rnd() * 4;
      const patch = new T.Mesh(new T.CircleGeometry(pr, 9), mat(GRASS_TONES[i % 3]));
      patch.rotation.x = -Math.PI / 2;
      patch.position.set(Math.cos(pa) * pd, 0.012 + i * 0.003, Math.sin(pa) * pd);
      world.add(patch);
    }

    // The desk vignette
    box(3.0, 0.22, 1.6, AMBER_DEEP, 0, 0.95, 0);
    [[-1.3, -0.6], [1.3, -0.6], [-1.3, 0.6], [1.3, 0.6]].forEach((p) => {
      box(0.18, 0.85, 0.18, FOREST_DEEP, p[0], 0.43, p[1]);
    });
    const form = new T.Mesh(
      new T.PlaneGeometry(0.95, 1.25),
      new T.MeshLambertMaterial({ color: BONE, emissive: 0x3c3c30 })
    );
    form.rotation.x = -Math.PI / 2 + 0.35;
    form.position.set(-0.2, 1.15, 0.2);
    world.add(form);
    cyl(0.06, 0.09, 0.95, INK, -1.15, 1.5, -0.45, 8);
    cone(0.3, 0.4, AMBER, -0.98, 1.98, -0.35);
    box(0.55, 0.13, 0.4, TEAL, 0.95, 1.12, -0.35, 0.3);
    box(0.5, 0.12, 0.36, BERRY, 0.92, 1.24, -0.34, 0.1);

    // Trees, bush, tufts
    const tree = (x, z, k, tone) => {
      cyl(0.09 * k, 0.12 * k, 0.5 * k, AMBER_DEEP, x, 0.25 * k, z, 6);
      cone(0.55 * k, 1.0 * k, tone || FOREST, x, 0.95 * k, z);
      cone(0.42 * k, 0.8 * k, SAGE, x, 1.45 * k, z);
      cone(0.27 * k, 0.6 * k, SAGE_LIGHT, x, 1.9 * k, z);
    };
    tree(-3.6, 1.6, 1.2);
    tree(3.4, -1.8, 1.0, 0xcf8a3d);
    tree(2.6, 2.6, 0.8);
    tree(-2.8, -2.8, 0.9);
    const bush = new T.Mesh(new T.IcosahedronGeometry(0.45, 1), mat(SAGE));
    bush.scale.set(1.3, 0.8, 1.1);
    bush.position.set(1.4, 0.3, 3.1);
    world.add(bush);
    for (let i = 0; i < 10; i += 1) {
      const a = rnd() * 6.28;
      const d = 2 + rnd() * 3.6;
      const t = new T.Mesh(new T.ConeGeometry(0.07, 0.24, 5), mat(GRASS_TONES[i % 3]));
      t.position.set(Math.cos(a) * d, 0.1, Math.sin(a) * d);
      world.add(t);
    }

    camera.position.set(0, 6.4, 14.5);
    camera.lookAt(0, 0.6, 0);

    function resize() {
      const w = canvas.clientWidth || section.clientWidth;
      const h = canvas.clientHeight || 420;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
    window.addEventListener("resize", resize);
    resize();

    function onScreen() {
      const r = section.getBoundingClientRect();
      return r.top < window.innerHeight && r.bottom > 0;
    }

    // Paint once immediately, then reveal the canvas over the painting: the
    // swap happens only after real pixels exist, and both layers share the
    // same absolute box, so the exchange can never shift layout.
    world.rotation.y = 0.5;
    renderer.render(scene, camera);
    section.classList.add("teaser-live");

    function frame(nowMs) {
      if (!document.hidden && onScreen()) {
        const now = nowMs * 0.001;
        world.rotation.y = 0.5 + now * 0.14;
        world.position.y = Math.sin(now * 0.5) * 0.18;
        renderer.render(scene, camera);
      }
      window.requestAnimationFrame(frame);
    }
    window.requestAnimationFrame(frame);
  }
})();
