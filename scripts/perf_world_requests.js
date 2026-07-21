// One desktop load of prod: record every /static/img/world/ response + bytes.
const puppeteer = require("puppeteer-core");

(async () => {
  const browser = await puppeteer.launch({
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    headless: "new",
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });
  await page.evaluateOnNewDocument(() => {
    try { window.localStorage.setItem("site_consent_v1", "yes"); } catch (e) {}
  });
  const assets = [];
  page.on("response", async (response) => {
    if (response.url().includes("/static/img/world/")) {
      const headers = response.headers();
      assets.push({
        url: response.url().split("/").pop(),
        status: response.status(),
        bytes: Number(headers["content-length"] || 0),
        cache: headers["cache-control"],
      });
    }
  });
  await page.goto("https://ensurecollege.com/", { waitUntil: "networkidle2", timeout: 60000 });
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await new Promise((r) => setTimeout(r, 4000));
  console.log(JSON.stringify(assets, null, 2));
  console.log("total bytes:", assets.reduce((sum, a) => sum + a.bytes, 0));
  await browser.close();
})();
