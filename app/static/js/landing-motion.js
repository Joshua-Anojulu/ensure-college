(() => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const root = document.documentElement;
  const hero = document.querySelector(".hero");

  if (!hero || reduceMotion) {
    return;
  }

  const revealTargets = [
    ".catalog-numbers",
    ".proof-band",
    ".difference-panel",
    ".resume-import",
    ".profile-form",
  ]
    .flatMap((selector) => Array.from(document.querySelectorAll(selector)))
    .filter(Boolean);

  for (const target of revealTargets) {
    target.classList.add("reveal-on-scroll");
  }
  root.classList.add("motion-ready");

  const revealObserver = "IntersectionObserver" in window
    ? new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (!entry.isIntersecting) {
              continue;
            }
            entry.target.classList.add("is-revealed");
            revealObserver.unobserve(entry.target);
          }
        },
        { rootMargin: "0px 0px -12% 0px", threshold: 0.12 }
      )
    : null;

  revealTargets.forEach((target, index) => {
    target.style.setProperty("--reveal-delay", `${Math.min(index * 55, 220)}ms`);
    if (revealObserver) {
      revealObserver.observe(target);
    } else {
      target.classList.add("is-revealed");
    }
  });

  const delay = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));
  const fontsReady = document.fonts?.ready || Promise.resolve();
  const fontGate = Promise.race([fontsReady, delay(600)]);

  const runHeroEntrance = () => {
    if (!window.gsap) {
      return;
    }
    const gsap = window.gsap;
    gsap.fromTo(
      ".hero-copy",
      { opacity: 1, y: 14 },
      { opacity: 1, y: 0, duration: 0.58, ease: "power3.out", clearProps: "transform,opacity" }
    );
    gsap.fromTo(
      ".hero-demo",
      { opacity: 1, y: 16, rotate: -0.35 },
      {
        opacity: 1,
        y: 0,
        rotate: 0,
        duration: 0.62,
        delay: 0.04,
        ease: "power3.out",
        clearProps: "transform,opacity",
      }
    );
  };

  fontGate.then(runHeroEntrance);

  const desktopMotion = window.matchMedia("(min-width: 768px)");
  if (!desktopMotion.matches) {
    return;
  }

  const decodeProofImages = () => {
    const images = Array.from(document.querySelectorAll(".proof-band img"));
    return Promise.all(
      images.map((image) => {
        if (!image.decode) {
          return Promise.resolve();
        }
        return image.decode().catch(() => undefined);
      })
    );
  };

  Promise.all([fontGate, decodeProofImages()]).then(() => {
    if (!window.gsap) {
      return;
    }
    const gsap = window.gsap;
    const ScrollTrigger = window.ScrollTrigger;
    if (ScrollTrigger) {
      gsap.registerPlugin(ScrollTrigger);
    }

    if (ScrollTrigger) {
      gsap.fromTo(
        ".proof-photo img",
        { scale: 1.04 },
        {
          scale: 1,
          ease: "none",
          scrollTrigger: {
            trigger: ".proof-band",
            start: "top bottom",
            end: "bottom top",
            scrub: true,
          },
        }
      );
    }

    if (ScrollTrigger) {
      window.requestAnimationFrame(() => ScrollTrigger.refresh());
    }
  });
})();
