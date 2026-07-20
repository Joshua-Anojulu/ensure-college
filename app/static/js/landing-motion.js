/* In-page anchor scrolling.
   The native `scroll-behavior: smooth` animation for the hero CTA travels
   ~3800px and gets ABORTED partway (any main-thread block or layout shift
   during the trip kills it), stranding the visitor at the proof band instead
   of the profile form. So the landing drives the scroll itself: the target is
   re-measured every frame, so a shift mid-flight cannot leave us short, and
   the tween cannot be silently cancelled. Runs before the motion gate below,
   because it must work even under prefers-reduced-motion (as an instant jump). */
(() => {
  const OFFSET = 84; // sticky header + breathing room
  const links = Array.from(document.querySelectorAll('a[href^="#"]:not([href="#"])'));
  if (!links.length) return;

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const easeOut = (t) => 1 - Math.pow(1 - t, 3);

  function scrollToTarget(el) {
    const goal = () => Math.max(
      0,
      Math.min(
        el.getBoundingClientRect().top + window.scrollY - OFFSET,
        document.documentElement.scrollHeight - window.innerHeight
      )
    );
    // Every scroll call is animated by `html { scroll-behavior: smooth }`, so
    // each step must opt out explicitly or the browser re-smooths our own
    // tween and the two fight (this is what stranded the CTA mid-page).
    const jump = (y) => window.scrollTo({ top: y, behavior: "instant" });

    if (reduced) {
      jump(goal());
      return;
    }
    const from = window.scrollY;
    const duration = Math.min(1100, Math.max(450, Math.abs(goal() - from) * 0.28));
    let startTime = null;
    const step = (now) => {
      if (startTime === null) startTime = now;
      const p = Math.min(1, (now - startTime) / duration);
      // Re-measure every frame: lazy images and the 3D teaser can change
      // layout while we are in flight.
      jump(from + (goal() - from) * easeOut(p));
      if (p < 1) window.requestAnimationFrame(step);
    };
    window.requestAnimationFrame(step);
    // Settle guarantee: if frames were starved (backgrounded tab, heavy work)
    // the tween can end short. Timers still fire, so land it exactly.
    window.setTimeout(() => {
      if (Math.abs(window.scrollY - goal()) > 4) jump(goal());
    }, duration + 80);
  }

  for (const link of links) {
    link.addEventListener("click", (event) => {
      if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey) return;
      const id = link.getAttribute("href").slice(1);
      const target = document.getElementById(id);
      if (!target) return;
      event.preventDefault();
      scrollToTarget(target);
      if (history.replaceState) history.replaceState(null, "", "#" + id);
    });
  }
})();

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

  const nearViewportMargin = () => Math.max(160, window.innerHeight * 0.25);
  const isNearViewport = (target) => {
    const rect = target.getBoundingClientRect();
    const margin = nearViewportMargin();
    return rect.top < window.innerHeight + margin && rect.bottom > -margin;
  };

  const revealNow = (target) => {
    target.classList.add("is-revealed");
    if (revealObserver) {
      revealObserver.unobserve(target);
    }
  };

  const revealNearViewportTargets = () => {
    for (const target of revealTargets) {
      if (!target.classList.contains("is-revealed") && isNearViewport(target)) {
        revealNow(target);
      }
    }
  };

  const revealObserver = "IntersectionObserver" in window
    ? new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (!entry.isIntersecting) {
              continue;
            }
            revealNow(entry.target);
          }
        },
        { rootMargin: "25% 0px 25% 0px", threshold: 0.01 }
      )
    : null;

  const setupReveals = () => {
    revealTargets.forEach((target, index) => {
      target.style.setProperty("--reveal-delay", `${Math.min(index * 55, 220)}ms`);
      if (isNearViewport(target)) {
        target.classList.add("reveal-on-scroll", "is-revealed");
      } else if (revealObserver) {
        target.classList.add("reveal-on-scroll");
        revealObserver.observe(target);
      } else {
        target.classList.add("reveal-on-scroll", "is-revealed");
      }
    });
    root.classList.add("motion-ready");
    window.addEventListener("resize", () => window.requestAnimationFrame(revealNearViewportTargets), { passive: true });
    window.addEventListener("orientationchange", () => window.requestAnimationFrame(revealNearViewportTargets), { passive: true });
  };

  window.requestAnimationFrame(setupReveals);

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
    const heroPieces = Array.from(document.querySelectorAll(".hero-headline, .hero-copy, .hero-demo"));
    if (heroPieces.some(isNearViewport)) {
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
