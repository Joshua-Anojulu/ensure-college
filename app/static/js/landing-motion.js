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
    ".difference-copy",
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

  // Catalog numbers count up from zero the first time they scroll into view.
  // The server-injected totals stay in the markup for no-JS and SEO; this
  // only animates the visible text.
  const countUp = (strong) => {
    const total = parseInt(strong.textContent, 10);
    if (!Number.isFinite(total) || !window.gsap) {
      return;
    }
    const state = { value: 0 };
    window.gsap.to(state, {
      value: total,
      duration: 1.1,
      ease: "power2.out",
      onUpdate: () => {
        strong.textContent = String(Math.round(state.value));
      },
    });
  };

  const numbers = document.querySelector(".catalog-numbers");
  if (numbers && "IntersectionObserver" in window) {
    const numbersObserver = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) {
          return;
        }
        numbersObserver.disconnect();
        numbers.querySelectorAll(".catalog-number strong").forEach(countUp);
      },
      { threshold: 0.4 }
    );
    numbersObserver.observe(numbers);
  }

  const delay = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));
  const fontsReady = document.fonts?.ready || Promise.resolve();
  const fontGate = Promise.race([fontsReady, delay(600)]);

  const runHeroEntrance = () => {
    if (!window.gsap) {
      return;
    }
    const gsap = window.gsap;
    const tl = gsap.timeline({ defaults: { ease: "power4.out" } });
    tl.fromTo(
      ".hero-headline",
      { y: 34, opacity: 1 },
      { y: 0, duration: 0.8, clearProps: "transform" }
    )
      .fromTo(
        ".hero-copy",
        { y: 22, opacity: 1 },
        { y: 0, duration: 0.7, clearProps: "transform" },
        0.12
      )
      .fromTo(
        ".hero-demo",
        { y: 44, rotate: -3.4, opacity: 1 },
        {
          y: 0,
          rotate: -1.2,
          duration: 0.95,
          // Clear the inline transform so the stylesheet's resting rotation
          // (and the focus-within straighten) take over after the entrance.
          onComplete: () => gsap.set(".hero-demo", { clearProps: "transform" }),
        },
        0.2
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
    if (!window.gsap || !window.ScrollTrigger) {
      return;
    }
    const gsap = window.gsap;
    gsap.registerPlugin(window.ScrollTrigger);

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

    // The CSS sticky stack does the pinning; GSAP only dims and shrinks a
    // card while the next one slides over it (storytelling: the covered
    // step recedes, the active step is the one you read).
    const stackCards = gsap.utils.toArray(".difference-stack .stack-card");
    stackCards.forEach((card, index) => {
      const next = stackCards[index + 1];
      if (!next) {
        return;
      }
      // Scale only: animating opacity here makes the incoming card's
      // overlap zone translucent and the two cards' text collides.
      gsap.to(card, {
        scale: 0.955,
        transformOrigin: "center top",
        ease: "none",
        scrollTrigger: {
          trigger: next,
          start: "top bottom",
          end: "top center",
          scrub: true,
        },
      });
    });

    window.requestAnimationFrame(() => window.ScrollTrigger.refresh());
  });
})();
