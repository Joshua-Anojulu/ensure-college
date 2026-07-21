// Phase 0-protocol attribution harness (rebuilt per docs/2026-07-19-phase0-lcp-tuning.md):
// puppeteer-core + installed Chrome, 412x823 @ DPR 1.75, Moto G Power UA,
// CPU 4x, mobileSlow4G-equivalent network, cold cache + fresh profile per run.
// Scenarios: cold (consent gate present) and pre-consented returning visit.
const puppeteer = require("puppeteer-core");
const fs = require("fs");
const os = require("os");
const path = require("path");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const UA =
  "Mozilla/5.0 (Linux; Android 11; moto g power (2022)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36";
const RUNS = Number(process.env.RUNS || 5);
const SCENARIOS = (process.env.SCENARIOS || "cold,preconsented").split(",");

async function measure(url, preconsent) {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "harness-"));
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: "new",
    userDataDir: profile,
    args: ["--no-first-run", "--no-default-browser-check"],
  });
  try {
    const page = await browser.newPage();
    await page.setUserAgent(UA);
    await page.setViewport({ width: 412, height: 823, deviceScaleFactor: 1.75, isMobile: true, hasTouch: true });
    const cdp = await page.createCDPSession();
    await cdp.send("Network.enable");
    await cdp.send("Network.emulateNetworkConditions", {
      offline: false,
      latency: 150,
      downloadThroughput: (1638.4 * 1024) / 8,
      uploadThroughput: (675 * 1024) / 8,
    });
    await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
    await page.evaluateOnNewDocument((seed) => {
      if (seed) {
        try { window.localStorage.setItem("site_consent_v1", "yes"); } catch (e) {}
      }
      window.__metrics = { lcp: null, lcpEl: null, cls: 0, longTasks: 0 };
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          window.__metrics.lcp = entry.startTime;
          window.__metrics.lcpEl = entry.element
            ? entry.element.tagName +
              (entry.element.id ? "#" + entry.element.id : "") +
              (entry.element.className && typeof entry.element.className === "string"
                ? "." + entry.element.className.split(" ").slice(0, 2).join(".")
                : "") +
              (entry.url ? " url:" + entry.url.split("/").pop() : "")
            : "(no element)";
        }
      }).observe({ type: "largest-contentful-paint", buffered: true });
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!entry.hadRecentInput) window.__metrics.cls += entry.value;
        }
      }).observe({ type: "layout-shift", buffered: true });
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) window.__metrics.longTasks += entry.duration;
      }).observe({ type: "longtask", buffered: true });
    }, preconsent);
    await page.goto(url, { waitUntil: "networkidle2", timeout: 90000 });
    await new Promise((r) => setTimeout(r, 4000));
    const metrics = await page.evaluate(() => {
      const nav = performance.getEntriesByType("navigation")[0];
      window.__metrics.ttfb = nav ? nav.responseStart : null;
      window.__metrics.renderDelta = window.__metrics.lcp - (nav ? nav.responseStart : 0);
      return window.__metrics;
    });
    return metrics;
  } finally {
    await browser.close();
    try { fs.rmSync(profile, { recursive: true, force: true }); } catch (e) {}
  }
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
}

(async () => {
  const targets = JSON.parse(process.argv[2]);
  const out = {};
  for (const [name, url] of Object.entries(targets)) {
    out[name] = {};
    for (const scenario of SCENARIOS) {
      const runs = [];
      for (let index = 0; index < RUNS; index++) {
        const m = await measure(url, scenario === "preconsented");
        runs.push(m);
        console.error(`${name}/${scenario} run ${index + 1}: LCP ${Math.round(m.lcp)}ms TTFB ${Math.round(m.ttfb)}ms render ${Math.round(m.renderDelta)}ms CLS ${m.cls.toFixed(4)} LT ${Math.round(m.longTasks)}ms el=${m.lcpEl}`);
      }
      out[name][scenario] = {
        runs,
        medianLcp: Math.round(median(runs.map((r) => r.lcp))),
        medianCls: median(runs.map((r) => r.cls)),
        medianLongTasks: Math.round(median(runs.map((r) => r.longTasks))),
      };
    }
  }
  console.log(JSON.stringify(out, null, 2));
})();
