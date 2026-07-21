/**
 * EnsureCollege frontend.
 *
 * Logged-out users get the original stateless experience. Logged-in users can
 * save their profile (it prefills on return) and turn matches into a tracked
 * application plan. Session state lives in an httponly cookie set by the
 * server, not in browser storage.
 */

const AI_ENABLED =
  document.querySelector('meta[name="ai-features-enabled"]')?.content === "true";

let vocabulary = null;
let lastSubmittedProfile = null;
let lastResults = null;
let lastPrograms = null;
let lastCompetitions = null;
const lastNearMisses = { scholarships: [], programs: [], competitions: [] };
let catalogScholarships = null;
let catalogPrograms = null;
let catalogCompetitions = null;
let catalogScholarshipsPromise = null;
let catalogProgramsPromise = null;
let catalogCompetitionsPromise = null;
let activeOpportunityView = "scholarships";
let activeViewTransition = null;
let scholarshipSearchQuery = "";
let programSearchQuery = "";
let competitionSearchQuery = "";
let catalogSearchQuery = "";
let catalogKindFilter = "all";
let catalogSort = "name";
let catalogFieldFilter = "";
let catalogNoEssay = false;
let catalogVerifiedOnly = false;
let searchInDescriptions = false;

const CATALOG_BATCH_SIZE = 30;
const catalogVisibleCounts = { scholarships: CATALOG_BATCH_SIZE, programs: CATALOG_BATCH_SIZE, competitions: CATALOG_BATCH_SIZE };

function resetCatalogWindow() {
  catalogVisibleCounts.scholarships = CATALOG_BATCH_SIZE;
  catalogVisibleCounts.programs = CATALOG_BATCH_SIZE;
  catalogVisibleCounts.competitions = CATALOG_BATCH_SIZE;
}

function buildShowMoreButton(kind, remaining) {
  const wrap = document.createElement("div");
  wrap.className = "catalog-show-more-wrap";
  const button = document.createElement("button");
  button.type = "button";
  button.className = "btn-secondary catalog-show-more";
  button.textContent = `Show ${Math.min(CATALOG_BATCH_SIZE, remaining)} more (${remaining} remaining)`;
  button.addEventListener("click", () => {
    catalogVisibleCounts[kind] += CATALOG_BATCH_SIZE;
    renderCatalog();
  });
  wrap.appendChild(button);
  return wrap;
}

// Same batching pattern as the catalog window above, applied per match lane
// (scholarships/programs/competitions) so a fresh match with a long result
// list renders in pages instead of dumping every card at once.
const LANE_BATCH_SIZE = CATALOG_BATCH_SIZE;
const laneVisibleCounts = {
  scholarships: LANE_BATCH_SIZE,
  programs: LANE_BATCH_SIZE,
  competitions: LANE_BATCH_SIZE,
};

function resetLaneWindow(kind) {
  laneVisibleCounts[kind] = LANE_BATCH_SIZE;
}

function resetAllLaneWindows() {
  resetLaneWindow("scholarships");
  resetLaneWindow("programs");
  resetLaneWindow("competitions");
}

// Same batching pattern, applied to the Quick applies panel (Application Plan
// tab), which is capped at 10 rows with a Show more button beyond that.
const QUICK_APPLIES_BATCH = 10;
let quickAppliesVisibleCount = QUICK_APPLIES_BATCH;

function resetQuickAppliesWindow() {
  quickAppliesVisibleCount = QUICK_APPLIES_BATCH;
}

function rerenderLane(kind) {
  if (kind === "scholarships" && lastResults) {
    renderResults(lastResults);
  } else if (kind === "programs" && lastPrograms) {
    renderPrograms(lastPrograms);
  } else if (kind === "competitions" && lastCompetitions) {
    renderCompetitions(lastCompetitions);
  }
}

function buildLaneShowMoreButton(kind, remaining) {
  const wrap = document.createElement("div");
  wrap.className = "catalog-show-more-wrap";
  const button = document.createElement("button");
  button.type = "button";
  button.className = "btn-secondary catalog-show-more";
  button.textContent = `Show ${Math.min(LANE_BATCH_SIZE, remaining)} more (${remaining} remaining)`;
  button.addEventListener("click", () => {
    laneVisibleCounts[kind] += LANE_BATCH_SIZE;
    rerenderLane(kind);
  });
  wrap.appendChild(button);
  return wrap;
}

const NEAR_MISS_KIND_META = {
  scholarships: { path: "scholarships", idField: "scholarship_id", nameField: "scholarship_name" },
  programs: { path: "programs", idField: "program_id", nameField: "name" },
  competitions: { path: "competitions", idField: "competition_id", nameField: "name" },
};

function buildNearMissGroup(kind, entries) {
  const meta = NEAR_MISS_KIND_META[kind];
  const details = document.createElement("details");
  details.className = "near-miss-group";
  const summary = document.createElement("summary");
  summary.textContent = `Not yet eligible (${entries.length})`;
  details.appendChild(summary);
  const list = document.createElement("div");
  list.className = "near-miss-list";
  for (const entry of entries) {
    const row = document.createElement("div");
    row.className = "browse-row near-miss-row";
    const left = document.createElement("div");
    left.className = "quick-apply-left";
    const nameLine = document.createElement("p");
    nameLine.className = "quick-apply-name";
    const link = document.createElement("a");
    link.className = "card-title-link";
    link.href = `/${meta.path}/${encodeURIComponent(entry[meta.idField])}`;
    link.textContent = entry[meta.nameField];
    nameLine.appendChild(link);
    left.appendChild(nameLine);
    const dl = deadlineParts(entry.deadline, entry.estimated_deadline);
    const metaLine = document.createElement("p");
    metaLine.className = "browse-row-meta";
    metaLine.textContent = `${entry.near_miss_reason} · ${dl.value}${dl.note ? ` (${dl.note})` : ""}`;
    left.appendChild(metaLine);
    row.appendChild(left);
    list.appendChild(row);
  }
  details.appendChild(list);
  return details;
}

let currentUser = null;
const savedIds = new Set();
const savedProgramIds = new Set();
const savedCompetitionIds = new Set();
let authMode = "login";
let passwordResetToken = null;

const form = document.getElementById("profile-form");
const formError = document.getElementById("form-error");
const profileProgress = document.getElementById("profile-progress");
const profileProgressFill = document.getElementById("profile-progress-fill");
const profileProgressLabel = document.getElementById("profile-progress-label");
const profileProgressStatus = document.getElementById("profile-progress-status");
const resultsSection = document.getElementById("results-section");
const resultsContainer = document.getElementById("results-container");
const resultsSummary = document.getElementById("results-summary");
const resultsEmpty = document.getElementById("results-empty");
const loadingEl = document.getElementById("loading");
const programsSection = document.getElementById("programs-section");
const programsContainer = document.getElementById("programs-container");
const programsSummary = document.getElementById("programs-summary");
const programsEmpty = document.getElementById("programs-empty");
const competitionsSection = document.getElementById("competitions-section");
const competitionsContainer = document.getElementById("competitions-container");
const competitionsSummary = document.getElementById("competitions-summary");
const competitionsEmpty = document.getElementById("competitions-empty");
const submitBtn = document.getElementById("submit-btn");
const opportunityTabs = document.getElementById("opportunity-tabs");
const opportunityTabButtons = Array.from(document.querySelectorAll(".opportunity-tab"));
const scholarshipsTabCount = document.getElementById("scholarships-tab-count");
const programsTabCount = document.getElementById("programs-tab-count");
const competitionsTabCount = document.getElementById("competitions-tab-count");
const catalogTabCount = document.getElementById("catalog-tab-count");
const savedTabCount = document.getElementById("saved-tab-count");

const authLoggedOut = document.getElementById("auth-logged-out");
const authLoggedIn = document.getElementById("auth-logged-in");
const openLoginBtn = document.getElementById("open-login");
const openSignupBtn = document.getElementById("open-signup");
const logoutBtn = document.getElementById("logout-btn");
const accountEmail = document.getElementById("account-email");
const showSavedBtn = document.getElementById("show-saved-btn");
const savedCountEl = document.getElementById("saved-count");

const authModal = document.getElementById("auth-modal");
const authModalTitle = document.getElementById("auth-modal-title");
const authModalIntro = document.getElementById("auth-modal-intro");
const authModalClose = document.getElementById("auth-modal-close");
const authForm = document.getElementById("auth-form");
const authEmail = document.getElementById("auth-email");
const authPassword = document.getElementById("auth-password");
const authPasswordHint = document.getElementById("auth-password-hint");
const authError = document.getElementById("auth-error");
const authSubmit = document.getElementById("auth-submit");
const authSwitchText = document.getElementById("auth-switch-text");
const authSwitchBtn = document.getElementById("auth-switch-btn");
const authRecovery = document.getElementById("auth-recovery");
const openPasswordResetBtn = document.getElementById("open-password-reset");
const passwordResetModal = document.getElementById("password-reset-modal");
const passwordResetClose = document.getElementById("password-reset-close");
const passwordResetTitle = document.getElementById("password-reset-title");
const passwordResetIntro = document.getElementById("password-reset-intro");
const passwordResetRequestForm = document.getElementById("password-reset-request-form");
const passwordResetConfirmForm = document.getElementById("password-reset-confirm-form");
const passwordResetEmail = document.getElementById("password-reset-email");
const passwordResetRequestError = document.getElementById("password-reset-request-error");
const passwordResetRequestSuccess = document.getElementById("password-reset-request-success");
const passwordResetRequestSubmit = document.getElementById("password-reset-request-submit");
const passwordResetNewPassword = document.getElementById("password-reset-new-password");
const passwordResetConfirmPassword = document.getElementById("password-reset-confirm-password");
const passwordResetConfirmError = document.getElementById("password-reset-confirm-error");
const passwordResetConfirmSubmit = document.getElementById("password-reset-confirm-submit");
const passwordResetBack = document.getElementById("password-reset-back");

const savedSection = document.getElementById("saved-section");
const savedSummary = document.getElementById("saved-summary");
const savedEmpty = document.getElementById("saved-empty");
const savedContainer = document.getElementById("saved-container");
const journeyMap = document.getElementById("journey-map");
const recLettersPanel = document.getElementById("rec-letters-panel");
const recLettersList = document.getElementById("rec-letters-list");
const recLettersEmpty = document.getElementById("rec-letters-empty");
const recLettersCount = document.getElementById("rec-letters-count");
const quickAppliesPanel = document.getElementById("quick-applies-panel");
const quickAppliesList = document.getElementById("quick-applies-list");
const quickAppliesEmpty = document.getElementById("quick-applies-empty");
const quickAppliesCount = document.getElementById("quick-applies-count");
const quickAppliesCopyBtn = document.getElementById("quick-applies-copy");

const resultsFilters = document.getElementById("results-filters");
const filterQuality = document.getElementById("filter-quality");
const filterSort = document.getElementById("filter-sort");
const filterMinScore = document.getElementById("filter-min-score");
const filterMinScoreValue = document.getElementById("filter-min-score-value");
const filterNoEssay = document.getElementById("filter-no-essay");
const filterFieldMatch = document.getElementById("filter-field-match");
const filterSchoolMatch = document.getElementById("filter-school-match");
const filterDemographicMatch = document.getElementById("filter-demographic-match");
const filterClosingSoon = document.getElementById("filter-closing-soon");
const filterVerifiedOnly = document.getElementById("filter-verified-only");
const filterClear = document.getElementById("filter-clear");
const scholarshipSearch = document.getElementById("scholarship-search");
const programSearch = document.getElementById("program-search");
const programsSearchPanel = document.getElementById("programs-search-panel");
const programFilterQuality = document.getElementById("program-filter-quality");
const programFilterSort = document.getElementById("program-filter-sort");
const programFilterMinScore = document.getElementById("program-filter-min-score");
const programFilterMinScoreValue = document.getElementById("program-filter-min-score-value");
const programFilterFieldMatch = document.getElementById("program-filter-field-match");
const programFilterClosingSoon = document.getElementById("program-filter-closing-soon");
const programFilterVerifiedOnly = document.getElementById("program-filter-verified-only");
const programFilterClear = document.getElementById("program-filter-clear");
const competitionSearch = document.getElementById("competition-search");
const competitionsSearchPanel = document.getElementById("competitions-search-panel");
const competitionFilterQuality = document.getElementById("competition-filter-quality");
const competitionFilterSort = document.getElementById("competition-filter-sort");
const competitionFilterMinScore = document.getElementById("competition-filter-min-score");
const competitionFilterMinScoreValue = document.getElementById("competition-filter-min-score-value");
const competitionFilterFieldMatch = document.getElementById("competition-filter-field-match");
const competitionFilterClosingSoon = document.getElementById("competition-filter-closing-soon");
const competitionFilterVerifiedOnly = document.getElementById("competition-filter-verified-only");
const competitionFilterClear = document.getElementById("competition-filter-clear");
const catalogSection = document.getElementById("catalog-section");
const catalogSummary = document.getElementById("catalog-summary");
const catalogSearch = document.getElementById("catalog-search");
const catalogField = document.getElementById("catalog-field");
const catalogSortSelect = document.getElementById("catalog-sort");
const catalogNoEssayCheck = document.getElementById("catalog-no-essay");
const catalogVerifiedOnlyCheck = document.getElementById("catalog-verified-only");
const catalogClear = document.getElementById("catalog-clear");
const catalogEmpty = document.getElementById("catalog-empty");
const catalogContainer = document.getElementById("catalog-container");

const CRITERIA_HELP = {
  gpa:
    "Used as an eligibility gate when a scholarship publishes a minimum GPA. It does not boost ranking by itself.",
  "grade-level":
    "Used as an eligibility gate. Pick your actual class year; broad sponsor rules like 'high school students' or 'undergraduates' are handled automatically.",
  citizenship:
    "Used as an eligibility gate when the sponsor publishes a citizenship rule. Unverified rules stay visible with a warning.",
  state:
    "Used as an eligibility gate for state-restricted awards. National awards remain available from every state.",
  "financial-need":
    "Adds fit points only for need-based scholarships. It does not hide merit awards or non-need-based awards.",
  "fields-of-study-group":
    "The strongest fit signal. Field-specific scholarships need an exact or approved broad-field match; otherwise they are capped to Possible with a caveat.",
  "demographic-tags-group":
    "Positive-only. These can explain scholarships that mention an identity group, but they never exclude you from results.",
  "target-schools":
    "Adds points for school-specific scholarships at schools you list. If a school-specific award points elsewhere, it is capped from Strong to Possible.",
  activities:
    "Adds a small capped bonus when meaningful activity keywords appear in the scholarship description. It never replaces eligibility.",
};

const LEGACY_GRADE_LABELS = {
  high_school: "High school (saved broad estimate)",
  college_undergraduate: "College undergraduate (saved broad estimate)",
};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  try {
    const response = await fetch("/vocabulary");
    if (!response.ok) {
      throw new Error(`Vocabulary request failed (${response.status})`);
    }
    vocabulary = await response.json();
    populateForm(vocabulary);
  } catch (err) {
    showFormError(
      "The form options could not load. Refresh the page. If this keeps happening, check that the server is running."
    );
    submitBtn.disabled = true;
    console.error(err);
  }

  form.addEventListener("submit", handleSubmit);
  wireProfileProgress();
  wirePageMotion();
  wireAuthControls();
  wirePasswordReset();
  wireOpportunityTabs();
  wireCatalogKindTabs();
  wireCatalogFilters();
  wirePreviewForm();
  wireFormSteps();
  wireFilterControls();
  wireSearchControls();
  wireResumeImport();
  wireSettings();
  wireQuickApplies();
  wireSiteNav();
  await loadSession();

  // Deep link used by other pages (e.g. /journey) to open the in-app
  // catalog: /#browse lands here, then the hash is cleared so a refresh
  // returns to the normal landing view.
  if (window.location.hash === "#browse") {
    window.history.replaceState({}, "", window.location.pathname + window.location.search);
    activateOpportunityView("catalog", { scroll: true });
  }
}

/* ---------- Page feedback and motion ---------- */

function wireProfileProgress() {
  form.addEventListener("input", updateProfileProgress);
  form.addEventListener("change", updateProfileProgress);
  updateProfileProgress();
}

function updateProfileProgress() {
  if (!profileProgress) {
    return;
  }
  const essentials = [
    document.getElementById("gpa").value.trim() !== "",
    Boolean(document.getElementById("grade-level").value),
    Boolean(document.getElementById("citizenship").value),
    Boolean(document.getElementById("state").value),
    Boolean(document.getElementById("financial-need").value),
    getCheckedValues("fields-of-study").length > 0,
  ];
  const complete = essentials.filter(Boolean).length;
  const percent = Math.round((complete / essentials.length) * 100);

  const progressText =
    complete === essentials.length ? "Profile essentials complete" : `${complete} of 6 essentials`;
  profileProgress.setAttribute("aria-valuenow", String(complete));
  profileProgress.setAttribute("aria-valuetext", progressText);
  profileProgressFill.style.width = `${percent}%`;
  profileProgressLabel.textContent = progressText;
  profileProgressStatus.textContent =
    complete === essentials.length ? "Ready to see your matches" : "Add the essentials to continue";
  form.classList.toggle("profile-ready", complete === essentials.length);
}

function wirePageMotion() {
  const sentinel = document.createElement("div");
  sentinel.className = "scroll-sentinel";
  sentinel.setAttribute("aria-hidden", "true");
  document.body.prepend(sentinel);

  const setHeaderScrolled = (isScrolled) => {
    document.body.classList.toggle("has-scrolled", isScrolled);
  };
  setHeaderScrolled(false);

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      ([entry]) => setHeaderScrolled(!entry.isIntersecting),
      { threshold: 0 }
    );
    observer.observe(sentinel);
  }

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }
  // Gates the few state-tied animations (hero marker draw, new-result arrival,
  // fit-ring draw). Sections themselves render instantly with no reveal.
  document.documentElement.classList.add("motion-ready");
}

function wireOpportunityTabs() {
  for (const button of opportunityTabButtons) {
    button.addEventListener("click", () => {
      const view = button.dataset.view || "scholarships";
      activateOpportunityView(view, { scroll: true });
    });
  }
  updateOpportunityTabCounts();
}

function wireSiteNav() {
  document.getElementById("nav-matches-btn")?.addEventListener("click", () => {
    if (lastResults || lastPrograms || lastCompetitions) {
      activateOpportunityView("scholarships", { scroll: true });
    } else {
      document.getElementById("profile-form")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
  document.getElementById("nav-plan-btn")?.addEventListener("click", () => {
    activateOpportunityView("saved", { scroll: true });
  });
  document.getElementById("nav-browse-btn")?.addEventListener("click", () => {
    activateOpportunityView("catalog", { scroll: true });
  });
}

function wireCatalogKindTabs() {
  const tabs = Array.from(document.querySelectorAll(".catalog-kind-tab"));
  for (const tab of tabs) {
    tab.addEventListener("click", () => {
      catalogKindFilter = tab.dataset.kind || "all";
      for (const other of tabs) {
        const selected = other === tab;
        other.classList.toggle("is-active", selected);
        other.setAttribute("aria-selected", selected ? "true" : "false");
      }
      applyCatalogKindScoping();
      resetCatalogWindow();
      renderCatalog();
    });
  }
  applyCatalogKindScoping();
}

// "No essay required" and the "Award (high->low)" sort only make sense for
// scholarships (programs and competitions do not carry an award amount, and
// hiding essay requirement here keeps the control from implying a filter that
// doesn't apply to the other two kinds). Hide both outside the scholarships
// tab, and fall back any state/selection that no longer applies.
function applyCatalogKindScoping() {
  const scholarshipsOnly = catalogKindFilter === "scholarships";
  const noEssayLabel = catalogNoEssayCheck?.closest(".filter-check");
  if (noEssayLabel) {
    noEssayLabel.hidden = !scholarshipsOnly;
  }
  const awardOption = catalogSortSelect?.querySelector('option[value="award"]');
  if (awardOption) {
    awardOption.hidden = !scholarshipsOnly;
    awardOption.disabled = !scholarshipsOnly;
  }
  if (!scholarshipsOnly) {
    if (catalogNoEssay) {
      catalogNoEssay = false;
      if (catalogNoEssayCheck) catalogNoEssayCheck.checked = false;
    }
    if (catalogSort === "award") {
      catalogSort = "name";
      if (catalogSortSelect) catalogSortSelect.value = "name";
    }
  }
}

function updateOpportunityTabCounts() {
  if (scholarshipsTabCount) {
    scholarshipsTabCount.textContent = lastResults ? String(lastResults.length) : "0";
  }
  if (programsTabCount) {
    programsTabCount.textContent = lastPrograms ? String(lastPrograms.length) : "0";
  }
  if (competitionsTabCount) {
    competitionsTabCount.textContent = lastCompetitions ? String(lastCompetitions.length) : "0";
  }
  if (catalogTabCount) {
    const loadedCount =
      catalogScholarships && catalogPrograms && catalogCompetitions
        ? catalogScholarships.length + catalogPrograms.length + catalogCompetitions.length
        : null;
    catalogTabCount.textContent = loadedCount === null ? "All" : String(loadedCount);
  }
  if (savedTabCount) {
    savedTabCount.textContent = String(
      savedIds.size + savedProgramIds.size + savedCompetitionIds.size
    );
  }
}

function setOpportunityTabsVisible(visible) {
  if (!opportunityTabs) {
    return;
  }
  opportunityTabs.hidden = !visible;
}

async function activateOpportunityView(view, options = {}) {
  activeOpportunityView = view;
  // First SPA-world activation loads world.css (never in the landing's
  // critical path); the stage renders only under .world-ready, set in the
  // stylesheet's load callback (see initWorldLayer).
  if (typeof window.__ensureWorldStage === "function") window.__ensureWorldStage();
  setOpportunityTabsVisible(true);

  for (const button of opportunityTabButtons) {
    const selected = button.dataset.view === view;
    button.classList.toggle("is-active", selected);
    button.setAttribute("aria-selected", selected ? "true" : "false");
  }

  // Everything that changes layout, renders, visibility, and the scroll,
  // runs together, so the scroll target's position is measured against the
  // settled layout, never against an outgoing section that is about to
  // collapse (which used to strand the viewport at the bottom of the page).
  const applyView = (scrollBehavior) => {
    resultsSection.hidden = view !== "scholarships" || !lastResults;
    programsSection.hidden = view !== "programs" || lastPrograms === null;
    competitionsSection.hidden = view !== "competitions" || lastCompetitions === null;
    catalogSection.hidden = view !== "catalog";
    savedSection.hidden = view !== "saved";
    if (view === "programs" && lastPrograms !== null) {
      renderPrograms(lastPrograms);
      programsSection.hidden = false;
    }
    if (view === "competitions" && lastCompetitions !== null) {
      renderCompetitions(lastCompetitions);
      competitionsSection.hidden = false;
    }
    if (options.scroll) {
      const target =
        view === "programs"
          ? programsSection
          : view === "competitions"
          ? competitionsSection
          : view === "catalog"
          ? catalogSection
          : view === "saved"
          ? savedSection
          : resultsSection;
      (target || opportunityTabs).scrollIntoView({ behavior: scrollBehavior, block: "start" });
    }
  };
  // Lane switches crossfade via the View Transitions API where supported;
  // the scroll is instant under the crossfade (the fade covers the jump).
  // Only one transition at a time: starting another aborts the first with an
  // unhandled InvalidStateError, so rapid updates fall back to instant.
  if (
    document.startViewTransition &&
    document.documentElement.classList.contains("motion-ready") &&
    !document.hidden &&
    !activeViewTransition
  ) {
    activeViewTransition = document.startViewTransition(() => applyView("auto"));
    const clearTransition = () => {
      activeViewTransition = null;
    };
    activeViewTransition.finished.then(clearTransition, clearTransition);
    activeViewTransition.ready.catch(() => {});
  } else {
    applyView("smooth");
  }

  if (view === "catalog") {
    await showCatalogView();
  }

  if (view === "saved") {
    if (currentUser) {
      await showSavedView({ scroll: false });
    } else {
      savedSection.hidden = false;
      savedContainer.innerHTML = "";
      savedEmpty.hidden = false;
      savedSummary.textContent = "Log in to save scholarships, summer programs, and competitions to your application plan.";
      if (recLettersPanel) recLettersPanel.hidden = true;
    }
  }

  updateOpportunityTabCounts();
}

/* ---------- Results filtering ---------- */

function wireFilterControls() {
  filterQuality.addEventListener("change", rerenderResults);
  filterSort.addEventListener("change", rerenderResults);
  filterMinScore.addEventListener("input", () => {
    filterMinScoreValue.textContent = filterMinScore.value;
    rerenderResults();
  });
  filterNoEssay.addEventListener("change", rerenderResults);
  filterFieldMatch.addEventListener("change", rerenderResults);
  filterSchoolMatch.addEventListener("change", rerenderResults);
  filterDemographicMatch.addEventListener("change", rerenderResults);
  filterClosingSoon.addEventListener("change", rerenderResults);
  filterVerifiedOnly.addEventListener("change", rerenderResults);
  filterClear.addEventListener("click", resetFilters);

  programFilterQuality?.addEventListener("change", rerenderProgramResults);
  programFilterSort?.addEventListener("change", rerenderProgramResults);
  programFilterMinScore?.addEventListener("input", () => {
    programFilterMinScoreValue.textContent = programFilterMinScore.value;
    rerenderProgramResults();
  });
  programFilterFieldMatch?.addEventListener("change", rerenderProgramResults);
  programFilterClosingSoon?.addEventListener("change", rerenderProgramResults);
  programFilterVerifiedOnly?.addEventListener("change", rerenderProgramResults);
  programFilterClear?.addEventListener("click", resetProgramFilters);

  competitionFilterQuality?.addEventListener("change", rerenderCompetitionResults);
  competitionFilterSort?.addEventListener("change", rerenderCompetitionResults);
  competitionFilterMinScore?.addEventListener("input", () => {
    competitionFilterMinScoreValue.textContent = competitionFilterMinScore.value;
    rerenderCompetitionResults();
  });
  competitionFilterFieldMatch?.addEventListener("change", rerenderCompetitionResults);
  competitionFilterClosingSoon?.addEventListener("change", rerenderCompetitionResults);
  competitionFilterVerifiedOnly?.addEventListener("change", rerenderCompetitionResults);
  competitionFilterClear?.addEventListener("click", resetCompetitionFilters);
}

function wireSearchControls() {
  const rerenderScholarships = debounce(() => {
    rerenderResults();
    ensureCatalogData(["scholarships"]).then(rerenderResults).catch(console.error);
  }, 150);
  const rerenderPrograms = debounce(() => {
    if (lastPrograms) {
      renderPrograms(lastPrograms);
    }
    ensureCatalogData(["programs"])
      .then(() => {
        if (lastPrograms) {
          renderPrograms(lastPrograms);
        }
      })
      .catch(console.error);
  }, 150);
  const rerenderCompetitions = debounce(() => {
    if (lastCompetitions) {
      renderCompetitions(lastCompetitions);
    }
    ensureCatalogData(["competitions"])
      .then(() => {
        if (lastCompetitions) {
          renderCompetitions(lastCompetitions);
        }
      })
      .catch(console.error);
  }, 150);
  const rerenderCatalog = debounce(() => {
    renderCatalog();
  }, 150);

  scholarshipSearch?.addEventListener("input", () => {
    scholarshipSearchQuery = scholarshipSearch.value.trim();
    resetLaneWindow("scholarships");
    rerenderScholarships();
  });
  programSearch?.addEventListener("input", () => {
    programSearchQuery = programSearch.value.trim();
    resetLaneWindow("programs");
    rerenderPrograms();
  });
  competitionSearch?.addEventListener("input", () => {
    competitionSearchQuery = competitionSearch.value.trim();
    resetLaneWindow("competitions");
    rerenderCompetitions();
  });
  catalogSearch?.addEventListener("input", () => {
    catalogSearchQuery = catalogSearch.value.trim();
    resetCatalogWindow();
    rerenderCatalog();
  });

  const descriptionToggles = Array.from(
    document.querySelectorAll(".search-descriptions-toggle")
  );
  descriptionToggles.forEach((toggle) => {
    toggle.addEventListener("change", () => {
      searchInDescriptions = toggle.checked;
      descriptionToggles.forEach((other) => {
        other.checked = searchInDescriptions;
      });
      resetAllLaneWindows();
      rerenderResults();
      if (lastPrograms) {
        renderPrograms(lastPrograms);
      }
      if (lastCompetitions) {
        renderCompetitions(lastCompetitions);
      }
      resetCatalogWindow();
      renderCatalog();
    });
  });
}

function debounce(fn, delay = 150) {
  let timer = null;
  return (...args) => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => fn(...args), delay);
  };
}

function resetFilters() {
  filterQuality.value = "all";
  filterSort.value = "fit";
  filterMinScore.value = "0";
  filterMinScoreValue.textContent = "0";
  scholarshipSearch.value = "";
  scholarshipSearchQuery = "";
  searchInDescriptions = false;
  for (const toggle of document.querySelectorAll(".search-descriptions-toggle")) {
    toggle.checked = false;
  }
  filterNoEssay.checked = false;
  filterFieldMatch.checked = false;
  filterSchoolMatch.checked = false;
  filterDemographicMatch.checked = false;
  filterClosingSoon.checked = false;
  filterVerifiedOnly.checked = false;
  rerenderResults();
}

function rerenderResults() {
  resetLaneWindow("scholarships");
  if (lastResults) {
    renderResults(lastResults);
  }
}

function resetProgramFilters() {
  programFilterQuality.value = "all";
  programFilterSort.value = "fit";
  programFilterMinScore.value = "0";
  programFilterMinScoreValue.textContent = "0";
  programSearch.value = "";
  programSearchQuery = "";
  searchInDescriptions = false;
  for (const toggle of document.querySelectorAll(".search-descriptions-toggle")) {
    toggle.checked = false;
  }
  programFilterFieldMatch.checked = false;
  programFilterClosingSoon.checked = false;
  programFilterVerifiedOnly.checked = false;
  rerenderProgramResults();
}

function rerenderProgramResults() {
  resetLaneWindow("programs");
  if (lastPrograms) {
    renderPrograms(lastPrograms);
  }
}

function resetCompetitionFilters() {
  competitionFilterQuality.value = "all";
  competitionFilterSort.value = "fit";
  competitionFilterMinScore.value = "0";
  competitionFilterMinScoreValue.textContent = "0";
  competitionSearch.value = "";
  competitionSearchQuery = "";
  searchInDescriptions = false;
  for (const toggle of document.querySelectorAll(".search-descriptions-toggle")) {
    toggle.checked = false;
  }
  competitionFilterFieldMatch.checked = false;
  competitionFilterClosingSoon.checked = false;
  competitionFilterVerifiedOnly.checked = false;
  rerenderCompetitionResults();
}

function rerenderCompetitionResults() {
  resetLaneWindow("competitions");
  if (lastCompetitions) {
    renderCompetitions(lastCompetitions);
  }
}

function normalizeSearch(text) {
  return String(text || "").toLowerCase();
}

// Levenshtein distance capped at maxDist, bailing out early once every cell in
// a row exceeds the cap. Returns maxDist + 1 to signal "further than allowed".
function boundedEditDistance(a, b, maxDist) {
  const al = a.length;
  const bl = b.length;
  if (Math.abs(al - bl) > maxDist) {
    return maxDist + 1;
  }
  let prev = Array.from({ length: bl + 1 }, (_, i) => i);
  for (let i = 1; i <= al; i++) {
    const curr = [i];
    let rowMin = i;
    for (let j = 1; j <= bl; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      const value = Math.min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost);
      curr[j] = value;
      if (value < rowMin) {
        rowMin = value;
      }
    }
    if (rowMin > maxDist) {
      return maxDist + 1;
    }
    prev = curr;
  }
  return prev[bl];
}

// A query token matches a field if it is a substring (fast, exact) or, for
// tokens long enough to be safe, within a small edit distance of some word in
// the field. This tolerates typos ("standford") without re-ranking results.
function tokenMatchesHaystacks(token, haystacks) {
  if (haystacks.some((value) => value.includes(token))) {
    return true;
  }
  if (token.length < 4) {
    return false;
  }
  const maxDist = token.length <= 6 ? 1 : 2;
  for (const value of haystacks) {
    for (const word of value.split(/[^a-z0-9]+/)) {
      if (word.length < 3) {
        continue;
      }
      if (boundedEditDistance(token, word, maxDist) <= maxDist) {
        return true;
      }
      // Typo inside a longer name: compare against a length-matched prefix.
      if (word.length > token.length + maxDist) {
        const prefix = word.slice(0, token.length + maxDist);
        if (boundedEditDistance(token, prefix, maxDist) <= maxDist) {
          return true;
        }
      }
    }
  }
  return false;
}

function itemMatchesSearch(values, query) {
  // Require every whitespace-separated word to appear in at least one field
  // (AND across words, OR across fields), so multi-word queries narrow instead
  // of looking for one literal substring. Each token may match exactly or via
  // small typo tolerance.
  const tokens = normalizeSearch(query).split(/\s+/).filter(Boolean);
  if (!tokens.length) {
    return true;
  }
  const haystacks = values.filter(Boolean).map(normalizeSearch);
  return tokens.every((token) => tokenMatchesHaystacks(token, haystacks));
}

function noResultsMessage(query, noun) {
  const wrap = document.createElement("div");
  wrap.className = "results-empty panel";
  const heading = document.createElement("h3");
  heading.textContent = `No ${noun} results for "${query}"`;
  const copy = document.createElement("p");
  copy.textContent = "Try fewer or different words, or turn on 'Search descriptions' for a wider search.";
  wrap.appendChild(heading);
  wrap.appendChild(copy);
  return wrap;
}

function catalogScholarshipById(id) {
  return (catalogScholarships || []).find((scholarship) => scholarship.id === id) || null;
}

function catalogProgramById(id) {
  return (catalogPrograms || []).find((program) => program.id === id) || null;
}

function scholarshipSearchValues(resultOrScholarship) {
  const scholarshipId = resultOrScholarship.scholarship_id || resultOrScholarship.id;
  const catalogItem = catalogScholarshipById(scholarshipId);
  // Default scope is identity only (name + sponsor) so common words in the
  // description don't flood results. The "Search descriptions" toggle widens it.
  const values = [
    resultOrScholarship.scholarship_name,
    resultOrScholarship.name,
    resultOrScholarship.sponsor,
    catalogItem?.sponsor,
  ];
  if (searchInDescriptions) {
    values.push(
      resultOrScholarship.description,
      catalogItem?.description,
      ...(resultOrScholarship.match_reasons || []),
    );
  }
  return values;
}

function programSearchValues(program) {
  const programId = program.program_id || program.id;
  const catalogItem = catalogProgramById(programId);
  // Default scope is identity only (name + host + subject).
  const values = [
    program.name,
    program.host,
    program.subject,
    catalogItem?.host,
    catalogItem?.subject,
  ];
  if (searchInDescriptions) {
    values.push(
      program.description,
      catalogItem?.description,
      ...(program.match_reasons || []),
    );
  }
  return values;
}

// Field score of 40 means a specific field/subject/category match (10 = open-to-all).
const SPECIFIC_FIELD_SCORE = 40;

function applyProgramFilters(programs) {
  const minScore = Number(programFilterMinScore.value) || 0;
  const quality = programFilterQuality.value;
  return programs.filter((program) => {
    if (!itemMatchesSearch(programSearchValues(program), programSearchQuery)) {
      return false;
    }
    const requiresSpecialCheck = Boolean(program.requires_special_check);
    if (quality === "special" && !requiresSpecialCheck) {
      return false;
    }
    if (
      quality !== "all" &&
      quality !== "special" &&
      (program.match_tier !== quality || requiresSpecialCheck)
    ) {
      return false;
    }
    if (program.score < minScore) {
      return false;
    }
    if (
      programFilterFieldMatch.checked &&
      (program.score_breakdown?.subject ?? 0) < SPECIFIC_FIELD_SCORE
    ) {
      return false;
    }
    if (programFilterClosingSoon.checked && !computeClosingSoon(program.deadline)) {
      return false;
    }
    if (programFilterVerifiedOnly.checked && !program.verified) {
      return false;
    }
    return true;
  });
}

function sortPrograms(programs) {
  const sorted = programs.slice();
  switch (programFilterSort.value) {
    case "name":
      sorted.sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" }));
      break;
    case "deadline":
      sorted.sort(compareByDeadline);
      break;
    default:
      // "fit": preserve the server's score/name ordering.
      break;
  }
  return sorted;
}

function catalogCompetitionById(id) {
  return (catalogCompetitions || []).find((competition) => competition.id === id) || null;
}

function competitionSearchValues(competition) {
  const competitionId = competition.competition_id || competition.id;
  const catalogItem = catalogCompetitionById(competitionId);
  // Default scope is identity only (name + host + category).
  const values = [
    competition.name,
    competition.host,
    competition.category,
    catalogItem?.host,
    catalogItem?.category,
  ];
  if (searchInDescriptions) {
    values.push(
      competition.description,
      catalogItem?.description,
      ...(competition.match_reasons || []),
    );
  }
  return values;
}

function applyCompetitionFilters(competitions) {
  const minScore = Number(competitionFilterMinScore.value) || 0;
  const quality = competitionFilterQuality.value;
  return competitions.filter((competition) => {
    if (!itemMatchesSearch(competitionSearchValues(competition), competitionSearchQuery)) {
      return false;
    }
    const requiresSpecialCheck = Boolean(competition.requires_special_check);
    if (quality === "special" && !requiresSpecialCheck) {
      return false;
    }
    if (
      quality !== "all" &&
      quality !== "special" &&
      (competition.match_tier !== quality || requiresSpecialCheck)
    ) {
      return false;
    }
    if (competition.score < minScore) {
      return false;
    }
    if (
      competitionFilterFieldMatch.checked &&
      (competition.score_breakdown?.category ?? 0) < SPECIFIC_FIELD_SCORE
    ) {
      return false;
    }
    if (competitionFilterClosingSoon.checked && !computeClosingSoon(competition.deadline)) {
      return false;
    }
    if (competitionFilterVerifiedOnly.checked && !competition.verified) {
      return false;
    }
    return true;
  });
}

function sortCompetitions(competitions) {
  const sorted = competitions.slice();
  switch (competitionFilterSort.value) {
    case "name":
      sorted.sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" }));
      break;
    case "deadline":
      sorted.sort(compareByDeadline);
      break;
    default:
      // "fit": preserve the server's score/name ordering.
      break;
  }
  return sorted;
}

function applyResultFilters(results) {
  const minScore = Number(filterMinScore.value) || 0;
  const quality = filterQuality.value;
  return results.filter((r) => {
    if (!itemMatchesSearch(scholarshipSearchValues(r), scholarshipSearchQuery)) {
      return false;
    }
    const requiresSpecialCheck = Boolean(r.requires_special_check);
    if (quality === "special" && !requiresSpecialCheck) {
      return false;
    }
    if (
      quality !== "all" &&
      quality !== "special" &&
      (r.match_tier !== quality || requiresSpecialCheck)
    ) {
      return false;
    }
    if (r.score < minScore) {
      return false;
    }
    if (filterNoEssay.checked && r.essay_required) {
      return false;
    }
    if (
      filterFieldMatch.checked &&
      (r.score_breakdown?.field_of_study ?? 0) < SPECIFIC_FIELD_SCORE
    ) {
      return false;
    }
    if (filterSchoolMatch.checked && (r.score_breakdown?.target_school ?? 0) <= 0) {
      return false;
    }
    if (filterDemographicMatch.checked && (r.score_breakdown?.demographics ?? 0) <= 0) {
      return false;
    }
    if (filterClosingSoon.checked && !r.closing_soon) {
      return false;
    }
    if (filterVerifiedOnly.checked && !r.verified) {
      return false;
    }
    return true;
  });
}

function sortResults(results) {
  const sorted = results.slice();
  switch (filterSort.value) {
    case "name":
      sorted.sort((a, b) =>
        a.scholarship_name.localeCompare(b.scholarship_name, undefined, {
          sensitivity: "base",
        })
      );
      break;
    case "award":
      sorted.sort((a, b) => awardSortValue(b.award_amount) - awardSortValue(a.award_amount));
      break;
    case "deadline":
      sorted.sort(compareByDeadline);
      break;
    default:
      // "fit": preserve the server's score/deadline/name ordering.
      break;
  }
  return sorted;
}

// "Deadline (soonest)" ranks what a student can actually act on:
//   tier 0 - a confirmed deadline, by date
//   tier 1 - an estimate, by its NEXT occurrence
//   tier 2 - rolling or unknown
// Estimates are a projection of an annual cycle, so a Feb estimate that has
// already passed means "expect roughly this date next year", not "closed
// months ago". Sorting them on their literal past date used to pile every
// unverified February entry at the top of the list, ahead of the deadlines a
// student can actually meet. The rolled-forward date is used for ORDER only;
// the card still displays the sponsor's estimate exactly as recorded.
const DEADLINE_TIER_REAL = 0;
const DEADLINE_TIER_ESTIMATE = 1;
const DEADLINE_TIER_NONE = 2;

function isUsableDate(value) {
  return Boolean(value) && value !== "rolling" && !String(value).startsWith("VERIFY");
}

function nextOccurrence(date) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const rolled = new Date(date.getTime());
  while (rolled < today) {
    rolled.setFullYear(rolled.getFullYear() + 1);
  }
  return rolled;
}

function deadlineSortKey(result) {
  if (isUsableDate(result.deadline)) {
    const real = parseRealDeadline(result.deadline);
    if (real) {
      return [DEADLINE_TIER_REAL, real.getTime()];
    }
  }
  if (isUsableDate(result.estimated_deadline)) {
    const est = parseRealDeadline(result.estimated_deadline);
    if (est) {
      return [DEADLINE_TIER_ESTIMATE, nextOccurrence(est).getTime()];
    }
  }
  return [DEADLINE_TIER_NONE, Infinity];
}

function compareByDeadline(a, b) {
  const ka = deadlineSortKey(a);
  const kb = deadlineSortKey(b);
  return ka[0] - kb[0] || ka[1] - kb[1];
}

// Best-effort numeric value for sorting only; descriptive/VERIFY amounts sort last.
function awardSortValue(amount) {
  if (typeof amount === "number") {
    return amount;
  }
  const numbers = String(amount).match(/\d[\d,]*/g);
  if (!numbers) {
    return -1;
  }
  return Math.max(...numbers.map((n) => Number(n.replace(/,/g, ""))));
}

/* ---------- Resume auto-fill ---------- */

function wireResumeImport() {
  if (!AI_ENABLED) return; // leave the resume-import section hidden and unwired
  const section = document.getElementById("resume-import-section");
  if (section) section.removeAttribute("hidden");
  const importBtn = document.getElementById("resume-import-btn");
  if (importBtn) {
    importBtn.addEventListener("click", handleResumeImport);
  }
}

async function handleResumeImport() {
  const fileInput = document.getElementById("resume-file");
  const textInput = document.getElementById("resume-text");
  const loading = document.getElementById("resume-loading");
  const errorEl = document.getElementById("resume-error");
  const noteEl = document.getElementById("resume-note");
  const importBtn = document.getElementById("resume-import-btn");

  const file = fileInput.files && fileInput.files[0];
  const text = (textInput.value || "").trim();
  if (!file && !text) {
    errorEl.textContent = "Choose a PDF or paste your resume text first.";
    errorEl.hidden = false;
    return;
  }

  if (!ensureAiConsent()) {
    return;
  }

  errorEl.hidden = true;
  noteEl.hidden = true;
  loading.hidden = false;
  importBtn.disabled = true;

  try {
    const formData = new FormData();
    if (file) {
      formData.append("file", file);
    }
    if (text) {
      formData.append("text", text);
    }

    const response = await fetch("/resume/extract", { method: "POST", body: formData });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      errorEl.textContent = extractError(
        data,
        "We could not read that resume. Try pasting the text instead."
      );
      errorEl.hidden = false;
      return;
    }

    const profile = data.profile || {};
    prefillForm(profile);

    noteEl.innerHTML = "";
    const summary = summarizeExtraction(profile);
    const intro = document.createElement("p");
    intro.textContent = summary
      ? `Pre-filled ${summary}. Review everything below, then add anything missing.`
      : "We could not pull much from that resume. Fill in the form below.";
    noteEl.appendChild(intro);
    if (data.notes) {
      const detail = document.createElement("p");
      detail.className = "resume-note-detail";
      detail.textContent = data.notes;
      noteEl.appendChild(detail);
    }
    noteEl.hidden = false;
    form.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    errorEl.textContent = "Could not reach the server. Check your connection and try again.";
    errorEl.hidden = false;
    console.error(err);
  } finally {
    loading.hidden = true;
    importBtn.disabled = false;
  }
}

function summarizeExtraction(profile) {
  const parts = [];
  if (profile.gpa !== undefined && profile.gpa !== null) parts.push("GPA");
  if (profile.grade_level) parts.push("grade level");
  if (profile.state) parts.push("state");
  if (profile.citizenship) parts.push("citizenship");
  if (profile.intended_majors && profile.intended_majors.length) parts.push("fields of study");
  if (profile.demographic_tags && profile.demographic_tags.length) parts.push("background");
  if (profile.activities && profile.activities.length) parts.push("activities");
  if (profile.target_schools && profile.target_schools.length) parts.push("target schools");
  if (parts.length === 0) return "";
  if (parts.length === 1) return parts[0];
  return parts.slice(0, -1).join(", ") + " and " + parts[parts.length - 1];
}

/* ---------- Account settings ---------- */

const settingsModal = document.getElementById("settings-modal");
const googleSettingsNote = document.getElementById("google-settings-note");
const passwordSettingsSection = document.getElementById("password-settings-section");

function wireSettings() {
  const openBtn = document.getElementById("open-settings");
  if (!openBtn || !settingsModal) {
    return;
  }
  openBtn.addEventListener("click", openSettingsModal);
  document.getElementById("settings-close").addEventListener("click", closeSettingsModal);
  settingsModal.addEventListener("click", (event) => {
    if (event.target === settingsModal) {
      closeSettingsModal();
    }
  });
  // Native <dialog> handles Escape and the top layer; run cleanup on any close.
  settingsModal.addEventListener("close", hideSettingsMessages);
  document
    .getElementById("change-password-form")
    .addEventListener("submit", handleChangePassword);
  document
    .getElementById("delete-account-btn")
    .addEventListener("click", handleDeleteAccount);
  document.getElementById("reminders-toggle")?.addEventListener("change", handleReminderToggle);
}

async function handleReminderToggle(event) {
  const enabled = event.target.checked;
  try {
    const response = await fetch("/account/reminders", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    });
    if (response.ok) {
      if (currentUser) {
        currentUser.reminders_enabled = enabled;
      }
    } else {
      event.target.checked = !enabled; // revert on failure
    }
  } catch (err) {
    event.target.checked = !enabled;
    console.error(err);
  }
}

function openSettingsModal() {
  hideSettingsMessages();
  document.getElementById("change-password-form").reset();
  updateSettingsControls();
  const remindersToggle = document.getElementById("reminders-toggle");
  if (remindersToggle) {
    remindersToggle.checked = currentUser?.reminders_enabled !== false;
  }
  if (!settingsModal.open) {
    settingsModal.showModal();
  }
  if (currentUser?.has_password === false) {
    document.getElementById("settings-close").focus();
  } else {
    document.getElementById("current-password").focus();
  }
}

function closeSettingsModal() {
  if (settingsModal.open) {
    settingsModal.close();
  }
}

function hideSettingsMessages() {
  const error = document.getElementById("settings-error");
  const success = document.getElementById("settings-success");
  error.hidden = true;
  error.textContent = "";
  success.hidden = true;
  success.textContent = "";
}

function updateSettingsControls() {
  const hasPassword = currentUser?.has_password !== false;
  if (passwordSettingsSection) {
    passwordSettingsSection.hidden = !hasPassword;
  }
  if (googleSettingsNote) {
    googleSettingsNote.hidden = hasPassword;
  }
}

function showSettingsError(message) {
  const error = document.getElementById("settings-error");
  document.getElementById("settings-success").hidden = true;
  error.textContent = message;
  error.hidden = false;
}

async function handleChangePassword(event) {
  event.preventDefault();
  hideSettingsMessages();
  if (currentUser?.has_password === false) {
    showSettingsError("This account signs in with Google and does not have a password to change.");
    return;
  }
  const current = document.getElementById("current-password").value;
  const next = document.getElementById("new-password").value;
  if (!current) {
    showSettingsError("Enter your current password.");
    return;
  }
  if (next.length < 8) {
    showSettingsError("Choose a new password with at least 8 characters.");
    return;
  }
  const submit = document.getElementById("change-password-submit");
  submit.disabled = true;
  try {
    const response = await fetch("/auth/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current_password: current, new_password: next }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      showSettingsError(extractError(data, "Could not change your password. Try again."));
      return;
    }
    const success = document.getElementById("settings-success");
    success.textContent = "Password changed.";
    success.hidden = false;
    document.getElementById("change-password-form").reset();
  } catch (err) {
    showSettingsError("Could not reach the server. Check your connection and try again.");
    console.error(err);
  } finally {
    submit.disabled = false;
  }
}

async function handleDeleteAccount() {
  hideSettingsMessages();
  // Password accounts confirm with their password; Google-only accounts have
  // none, so their logged-in session plus the confirm dialog authorizes.
  const hasPassword = currentUser?.has_password !== false;
  const password = hasPassword ? document.getElementById("current-password").value : null;
  if (hasPassword && !password) {
    showSettingsError("Enter your current password above to confirm deletion.");
    return;
  }
  if (
    !window.confirm(
      "Delete your account permanently? This removes your profile and saved scholarships/programs."
    )
  ) {
    return;
  }
  try {
    const response = await fetch("/auth/delete-account", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(hasPassword ? { password } : {}),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      showSettingsError(extractError(data, "Could not delete your account. Try again."));
      return;
    }
    currentUser = null;
    savedIds.clear();
    savedProgramIds.clear();
    savedCompetitionIds.clear();
    savedSection.hidden = true;
    closeSettingsModal();
    renderAuthState();
    updateSavedCount();
    refreshLanesAfterAuthChange();
  } catch (err) {
    showSettingsError("Could not reach the server. Check your connection and try again.");
    console.error(err);
  }
}

/* ---------- Auth wiring ---------- */

function wireAuthControls() {
  openLoginBtn.addEventListener("click", () => openAuthModal("login"));
  openSignupBtn.addEventListener("click", () => openAuthModal("signup"));
  logoutBtn.addEventListener("click", handleLogout);
  showSavedBtn.addEventListener("click", toggleSavedView);

  authModalClose.addEventListener("click", closeAuthModal);
  authModal.addEventListener("click", (event) => {
    if (event.target === authModal) {
      closeAuthModal();
    }
  });
  // Native <dialog> handles Escape and the top layer; run cleanup on any close.
  authModal.addEventListener("close", () => {
    authForm.reset();
    hideAuthError();
  });
  authSwitchBtn.addEventListener("click", () => {
    openAuthModal(authMode === "login" ? "signup" : "login");
  });
  authForm.addEventListener("submit", handleAuthSubmit);
}

function wirePasswordReset() {
  openPasswordResetBtn.addEventListener("click", () => openPasswordResetModal());
  passwordResetClose.addEventListener("click", closePasswordResetModal);
  passwordResetBack.addEventListener("click", () => {
    closePasswordResetModal();
    openAuthModal("login");
  });
  passwordResetModal.addEventListener("click", (event) => {
    if (event.target === passwordResetModal) {
      closePasswordResetModal();
    }
  });
  // Native <dialog> handles Escape and the top layer; run cleanup on any close.
  passwordResetModal.addEventListener("close", onPasswordResetClosed);
  passwordResetRequestForm.addEventListener("submit", handlePasswordResetRequest);
  passwordResetConfirmForm.addEventListener("submit", handlePasswordResetConfirm);

  const token = new URLSearchParams(window.location.search).get("reset_token");
  if (token) {
    openPasswordResetModal(token);
  }
}

function openAuthModal(mode, message) {
  authMode = mode;
  const isLogin = mode === "login";
  authModalTitle.textContent = isLogin ? "Log in" : "Create an account";
  authModalIntro.textContent =
    message ||
    (isLogin
      ? "Log in to save your profile and turn opportunities into an application plan."
      : "Sign up to save your profile and turn opportunities into an application plan.");
  authSubmit.textContent = isLogin ? "Log in" : "Create account";
  authSwitchText.textContent = isLogin ? "New here?" : "Already have an account?";
  authSwitchBtn.textContent = isLogin ? "Create an account" : "Log in";
  authPasswordHint.hidden = isLogin;
  authRecovery.hidden = !isLogin;
  authPassword.setAttribute(
    "autocomplete",
    isLogin ? "current-password" : "new-password"
  );

  hideAuthError();
  if (!authModal.open) {
    authModal.showModal();
  }
  authEmail.focus();
}

function closeAuthModal() {
  if (authModal.open) {
    authModal.close();
  }
}

function openPasswordResetModal(token = null) {
  closeAuthModal();
  passwordResetToken = token;
  const confirming = Boolean(passwordResetToken);
  passwordResetTitle.textContent = confirming ? "Choose a new password" : "Reset your password";
  passwordResetIntro.textContent = confirming
    ? "Choose a new password for your EnsureCollege account."
    : "Enter your email and we'll send a one-time reset link.";
  passwordResetRequestForm.hidden = confirming;
  passwordResetConfirmForm.hidden = !confirming;
  hidePasswordResetMessages();
  if (!passwordResetModal.open) {
    passwordResetModal.showModal();
  }
  (confirming ? passwordResetNewPassword : passwordResetEmail).focus();
}

function closePasswordResetModal() {
  if (passwordResetModal.open) {
    passwordResetModal.close();
  }
}

function onPasswordResetClosed() {
  passwordResetRequestForm.reset();
  passwordResetConfirmForm.reset();
  passwordResetToken = null;
  hidePasswordResetMessages();
  const url = new URL(window.location.href);
  if (url.searchParams.has("reset_token")) {
    url.searchParams.delete("reset_token");
    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
  }
}

function hidePasswordResetMessages() {
  passwordResetRequestError.hidden = true;
  passwordResetRequestError.textContent = "";
  passwordResetRequestSuccess.hidden = true;
  passwordResetRequestSuccess.textContent = "";
  passwordResetConfirmError.hidden = true;
  passwordResetConfirmError.textContent = "";
}

function showPasswordResetRequestError(message) {
  passwordResetRequestSuccess.hidden = true;
  passwordResetRequestError.textContent = message;
  passwordResetRequestError.hidden = false;
}

function showPasswordResetConfirmError(message) {
  passwordResetConfirmError.textContent = message;
  passwordResetConfirmError.hidden = false;
}

async function handlePasswordResetRequest(event) {
  event.preventDefault();
  hidePasswordResetMessages();
  const email = passwordResetEmail.value.trim();
  if (!email) {
    showPasswordResetRequestError("Enter your email.");
    return;
  }

  passwordResetRequestSubmit.disabled = true;
  try {
    const response = await fetch("/auth/password-reset/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      showPasswordResetRequestError(
        extractError(data, "Could not request a reset link. Please try again.")
      );
      return;
    }
    passwordResetRequestSuccess.textContent =
      data.message || "If an account exists for that email, a reset link will arrive shortly.";
    passwordResetRequestSuccess.hidden = false;
  } catch (err) {
    showPasswordResetRequestError("Could not reach the server. Check your connection and try again.");
    console.error(err);
  } finally {
    passwordResetRequestSubmit.disabled = false;
  }
}

async function handlePasswordResetConfirm(event) {
  event.preventDefault();
  passwordResetConfirmError.hidden = true;
  passwordResetConfirmError.textContent = "";
  const password = passwordResetNewPassword.value;
  const confirmation = passwordResetConfirmPassword.value;
  if (password.length < 8) {
    showPasswordResetConfirmError("Choose a password with at least 8 characters.");
    return;
  }
  if (password !== confirmation) {
    showPasswordResetConfirmError("Those passwords do not match.");
    return;
  }

  passwordResetConfirmSubmit.disabled = true;
  try {
    const response = await fetch("/auth/password-reset/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: passwordResetToken, new_password: password }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      showPasswordResetConfirmError(
        extractError(data, "Could not reset your password. Request a new link and try again.")
      );
      return;
    }
    closePasswordResetModal();
    await loadSession();
  } catch (err) {
    showPasswordResetConfirmError("Could not reach the server. Check your connection and try again.");
    console.error(err);
  } finally {
    passwordResetConfirmSubmit.disabled = false;
  }
}

function showAuthError(message) {
  authError.textContent = message;
  authError.hidden = false;
}

function hideAuthError() {
  authError.hidden = true;
  authError.textContent = "";
}

async function handleAuthSubmit(event) {
  event.preventDefault();
  hideAuthError();

  const email = authEmail.value.trim();
  const password = authPassword.value;

  if (!email) {
    showAuthError("Enter your email.");
    return;
  }
  if (authMode === "signup" && password.length < 8) {
    showAuthError("Choose a password with at least 8 characters.");
    return;
  }
  if (!password) {
    showAuthError("Enter your password.");
    return;
  }

  const endpoint = authMode === "login" ? "/auth/login" : "/auth/signup";
  authSubmit.disabled = true;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      showAuthError(extractError(data, "That did not work. Check your details and try again."));
      return;
    }

    currentUser = data;
    closeAuthModal();
    renderAuthState();
    await Promise.all([loadProfileIntoForm(), loadSaved()]);
    await autoMatchFromSavedProfile();
    refreshLanesAfterAuthChange();
  } catch (err) {
    showAuthError("Could not reach the server. Check your connection and try again.");
    console.error(err);
  } finally {
    authSubmit.disabled = false;
  }
}

async function handleLogout() {
  try {
    await fetch("/auth/logout", { method: "POST" });
  } catch (err) {
    console.error(err);
  }
  currentUser = null;
  savedIds.clear();
  savedProgramIds.clear();
  savedCompetitionIds.clear();
  savedSection.hidden = true;
  if (recLettersPanel) recLettersPanel.hidden = true;
  renderAuthState();
  updateSavedCount();
  refreshLanesAfterAuthChange();
}

async function loadSession() {
  try {
    const response = await fetch("/auth/me");
    if (response.ok) {
      currentUser = await response.json();
      renderAuthState();
      await Promise.all([loadProfileIntoForm(), loadSaved()]);
      await autoMatchFromSavedProfile();
    } else {
      currentUser = null;
      savedIds.clear();
      savedProgramIds.clear();
      savedCompetitionIds.clear();
      renderAuthState();
    }
  } catch (err) {
    currentUser = null;
    savedIds.clear();
    savedProgramIds.clear();
    savedCompetitionIds.clear();
    renderAuthState();
    console.error(err);
  }
}

// Save buttons read saved-ID state at render time, so a login/logout must
// re-render every lane that has data, not just scholarships, or the lane the
// user is looking at keeps the previous account's Saved labels (and a stale
// "Saved" button would un-invert and save on click).
function refreshLanesAfterAuthChange() {
  if (lastResults) {
    renderResults(lastResults);
  }
  if (lastPrograms) {
    renderPrograms(lastPrograms);
  }
  if (lastCompetitions) {
    renderCompetitions(lastCompetitions);
  }
  if (!catalogSection.hidden) {
    renderCatalog();
  }
}

function renderAuthState() {
  const loggedIn = currentUser !== null;
  authLoggedIn.hidden = !loggedIn;
  authLoggedOut.hidden = loggedIn;
  if (loggedIn) {
    accountEmail.textContent = currentUser.email;
    accountEmail.title = currentUser.email;
  }
  updateSavedCount();
  updateOpportunityTabCounts();
  updatePreviewAccountPitch();
}

/* ---------- Profile persistence ---------- */

async function loadProfileIntoForm() {
  if (!currentUser) {
    return;
  }
  try {
    const response = await fetch("/account/profile");
    if (!response.ok) {
      return;
    }
    const data = await response.json();
    if (data.profile) {
      prefillForm(data.profile);
      lastSubmittedProfile = data.profile;
    }
  } catch (err) {
    console.error(err);
  }
}

function prefillForm(profile) {
  setValue("gpa", profile.gpa);
  setValue("grade-level", profile.grade_level);
  setValue("citizenship", profile.citizenship);
  setValue("state", profile.state);
  setValue("financial-need", profile.financial_need_level);
  setCheckboxes("fields-of-study", profile.intended_majors || []);
  setCheckboxes("demographic-tags", profile.demographic_tags || []);
  setValue("target-schools", (profile.target_schools || []).join(", "));
  setValue("activities", (profile.activities || []).join(", "));
  updateProfileProgress();
}

function setValue(elementId, value) {
  const el = document.getElementById(elementId);
  if (el && value !== undefined && value !== null) {
    if (el.tagName === "SELECT") {
      ensureSelectValue(el, value, elementId);
    }
    el.value = value;
  }
}

function ensureSelectValue(select, value, elementId) {
  if (!value || Array.from(select.options).some((option) => option.value === value)) {
    return;
  }
  if (elementId !== "grade-level" || !LEGACY_GRADE_LABELS[value]) {
    return;
  }
  const option = document.createElement("option");
  option.value = value;
  option.textContent = LEGACY_GRADE_LABELS[value];
  option.title = "This broad saved value is still accepted, but choosing your exact class year will return better matches.";
  select.appendChild(option);
}

function setCheckboxes(containerId, values) {
  const wanted = new Set(values);
  const container = document.getElementById(containerId);
  if (!container) {
    return;
  }
  for (const input of container.querySelectorAll("input[type=checkbox]")) {
    input.checked = wanted.has(input.value);
  }
}

async function saveProfileSilently(profile) {
  if (!currentUser) {
    return;
  }
  try {
    await fetch("/account/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
  } catch (err) {
    console.error(err);
  }
}

/* ---------- Saved scholarships/programs ---------- */

function syncSavedState(data) {
  savedIds.clear();
  savedProgramIds.clear();
  savedCompetitionIds.clear();
  for (const item of data.saved || []) {
    savedIds.add(item.scholarship_id);
  }
  for (const item of data.programs || []) {
    savedProgramIds.add(item.program_id);
  }
  for (const item of data.competitions || []) {
    savedCompetitionIds.add(item.competition_id);
  }
  updateSavedCount();
}

async function loadSaved() {
  if (!currentUser) {
    return;
  }
  try {
    const response = await fetch("/account/saved");
    if (!response.ok) {
      return;
    }
    const data = await response.json();
    syncSavedState(data);
    if (!savedSection.hidden) {
      renderSaved(data.saved, data.programs || [], data.competitions || []);
    }
  } catch (err) {
    console.error(err);
  }
}

function updateSavedCount() {
  const count = savedIds.size + savedProgramIds.size + savedCompetitionIds.size;
  const changed = savedCountEl.textContent !== String(count);
  savedCountEl.textContent = String(count);
  savedCountEl.hidden = count === 0;
  if (changed && count > 0) {
    savedCountEl.classList.remove("count-pop");
    void savedCountEl.offsetWidth;
    savedCountEl.classList.add("count-pop");
  }
  updateOpportunityTabCounts();
}

async function toggleSavedView() {
  await activateOpportunityView("saved", { scroll: true });
}

async function showSavedView(options = {}) {
  savedSection.hidden = false;
  savedContainer.innerHTML = "";
  savedSummary.textContent = "Loading...";
  try {
    const response = await fetch("/account/saved");
    if (!response.ok) {
      savedSummary.textContent = "Saved items could not be loaded.";
      return;
    }
    const data = await response.json();
    syncSavedState(data);
    renderSaved(data.saved, data.programs || [], data.competitions || []);
  } catch (err) {
    savedSummary.textContent = "Saved items could not be loaded.";
    console.error(err);
  }
  if (options.scroll !== false) {
    savedSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

const SAVED_STATUSES = [
  { value: "interested", label: "Interested" },
  { value: "drafting", label: "Drafting" },
  { value: "submitted", label: "Submitted" },
  { value: "awarded", label: "Awarded" },
  { value: "rejected", label: "Rejected" },
];
let trackerItems = [];

function trackerSummary(items) {
  const counts = {};
  for (const item of items) {
    const status = item.status || "interested";
    counts[status] = (counts[status] || 0) + 1;
  }
  const parts = SAVED_STATUSES.filter((s) => counts[s.value]).map(
    (s) => `${counts[s.value]} ${s.label.toLowerCase()}`
  );
  const total = items.length;
  const head = `${total} saved item${total === 1 ? "" : "s"}`;
  const totalSteps = items.reduce(
    (sum, item) =>
      sum +
      (item.scholarship?.application_requirements?.length ||
        item.program?.application_requirements?.length ||
        item.competition?.application_requirements?.length ||
        0),
    0
  );
  const completedSteps = items.reduce(
    (sum, item) => sum + (item.completed_requirement_ids?.length || 0),
    0
  );
  if (totalSteps) {
    const statusSummary = parts.length ? `${head}: ${parts.join(", ")}.` : `${head}.`;
    return `${statusSummary} ${completedSteps}/${totalSteps} application steps complete.`;
  }
  return parts.length ? `${head}: ${parts.join(", ")}.` : `${head}.`;
}

function refreshTrackerSummary() {
  if (trackerItems.length > 0) {
    savedSummary.textContent = trackerSummary(trackerItems);
    const existingPlan = savedContainer.querySelector(".plan-guidance");
    if (existingPlan) {
      existingPlan.replaceWith(buildPlanGuidance(trackerItems));
    }
  }
  renderRecLettersRollup(trackerItems);
  renderQuickApplies();
  renderJourneyMap();
}

/* ---------- Quick applies ---------- */
// Derived live from the current match state (lastResults/lastPrograms/lastCompetitions),
// not from saved items, so the panel renders whether or not the student is logged in,
// as soon as any lane has matches.

const QUICK_APPLY_KIND_META = {
  scholarship: { label: "Scholarship", path: "scholarships" },
  program: { label: "Summer program", path: "programs" },
  competition: { label: "Competition", path: "competitions" },
};

function matchResultsExist() {
  return lastResults !== null || lastPrograms !== null || lastCompetitions !== null;
}

function quickApplyItemId(kind, item) {
  if (kind === "program") return item.program_id;
  if (kind === "competition") return item.competition_id;
  return item.scholarship_id;
}

function quickApplyItemName(kind, item) {
  return kind === "scholarship" ? item.scholarship_name : item.name;
}

// Qualifies when the item does not require a special check, does not require
// an essay, and has 3 or fewer required application steps. When a match result
// has no application_requirements data (not yet verified for that scholarship,
// the backend serializes that as an empty list, never as a missing key), it
// qualifies on essay alone and is labeled "requirements not yet verified"
// rather than given a count.
function quickApplyCandidate(kind, item) {
  if (item.requires_special_check) {
    return null;
  }
  if (item.essay_required) {
    return null;
  }
  const id = quickApplyItemId(kind, item);
  const name = quickApplyItemName(kind, item);
  if (!id || !name) {
    return null;
  }
  const base = {
    kind,
    id,
    name,
    url: item.url,
    deadline: item.deadline,
    estimated_deadline: item.estimated_deadline,
  };
  const requirements = item.application_requirements;
  if (!requirements || requirements.length === 0) {
    return { ...base, requiredCount: 0, unverified: true };
  }
  const requiredCount = requirements.filter((requirement) => requirement.required).length;
  if (requiredCount > 3) {
    return null;
  }
  return { ...base, requiredCount, unverified: false };
}

// Three strict tiers: every real deadline sorts ahead of every estimated-only
// one, which sorts ahead of every item with neither. The lane lists now use the
// same tiering (compareByDeadline), so both surfaces agree: a confirmed date a
// student can meet always outranks a projection.
const QUICK_APPLY_TIER_ESTIMATED = 1e13;

function quickApplySortValue(candidate) {
  const real = parseRealDeadline(candidate.deadline);
  if (real) {
    return real.getTime();
  }
  const estimated = candidate.estimated_deadline ? new Date(candidate.estimated_deadline) : null;
  if (estimated && !Number.isNaN(estimated.getTime())) {
    return QUICK_APPLY_TIER_ESTIMATED + estimated.getTime();
  }
  return Infinity;
}

function collectQuickApplyCandidates() {
  const candidates = [];
  for (const item of lastResults || []) {
    const candidate = quickApplyCandidate("scholarship", item);
    if (candidate) candidates.push(candidate);
  }
  for (const item of lastPrograms || []) {
    const candidate = quickApplyCandidate("program", item);
    if (candidate) candidates.push(candidate);
  }
  for (const item of lastCompetitions || []) {
    const candidate = quickApplyCandidate("competition", item);
    if (candidate) candidates.push(candidate);
  }
  candidates.sort((a, b) => quickApplySortValue(a) - quickApplySortValue(b));
  return candidates;
}

function renderQuickApplies() {
  if (!quickAppliesPanel) {
    return;
  }
  if (!matchResultsExist()) {
    quickAppliesPanel.hidden = true;
    return;
  }
  quickAppliesPanel.hidden = false;
  renderQuickApplyFieldChips();
  const candidates = collectQuickApplyCandidates();
  quickAppliesList.innerHTML = "";
  quickAppliesEmpty.hidden = candidates.length > 0;
  if (quickAppliesCount) {
    const knownRequirementCount = candidates.filter((c) => !c.unverified).length;
    const unknownRequirementCount = candidates.filter((c) => c.unverified).length;
    const countParts = [];
    if (knownRequirementCount > 0) {
      countParts.push(`${knownRequirementCount} need no essay and 3 or fewer requirements`);
    }
    if (unknownRequirementCount > 0) {
      countParts.push(
        `${unknownRequirementCount} more have requirements we haven't verified yet`
      );
    }
    quickAppliesCount.textContent = countParts.length ? `${countParts.join("; ")}.` : "";
  }
  const visible = candidates.slice(0, quickAppliesVisibleCount);
  for (const candidate of visible) {
    quickAppliesList.appendChild(buildQuickApplyRow(candidate));
  }
  if (candidates.length > quickAppliesVisibleCount) {
    quickAppliesList.appendChild(
      buildQuickAppliesShowMoreButton(candidates.length - quickAppliesVisibleCount)
    );
  }
}

function buildQuickApplyRow(candidate) {
  const meta = QUICK_APPLY_KIND_META[candidate.kind];
  const row = document.createElement("div");
  row.className = "browse-row quick-apply-row";

  const left = document.createElement("div");
  left.className = "quick-apply-left";

  const nameLine = document.createElement("p");
  nameLine.className = "quick-apply-name";
  const link = document.createElement("a");
  link.className = "card-title-link";
  link.href = `/${meta.path}/${encodeURIComponent(candidate.id)}`;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = candidate.name;
  nameLine.appendChild(link);
  left.appendChild(nameLine);

  const dl = deadlineParts(candidate.deadline, candidate.estimated_deadline);
  const requirementText = candidate.unverified
    ? "requirements not yet verified"
    : `${candidate.requiredCount} requirement${candidate.requiredCount === 1 ? "" : "s"}`;
  const metaLine = document.createElement("p");
  metaLine.className = "browse-row-meta quick-apply-meta";
  metaLine.textContent = `${meta.label} · ${dl.value}${dl.note ? ` (${dl.note})` : ""} · ${requirementText}`;
  left.appendChild(metaLine);

  row.appendChild(left);

  const apply = document.createElement("a");
  apply.className = "card-link quick-apply-link";
  apply.href = candidate.url;
  apply.target = "_blank";
  apply.rel = "noopener noreferrer";
  apply.textContent = "View and apply";
  row.appendChild(apply);

  return row;
}

function buildQuickAppliesShowMoreButton(remaining) {
  const wrap = document.createElement("div");
  wrap.className = "catalog-show-more-wrap";
  const button = document.createElement("button");
  button.type = "button";
  button.className = "btn-secondary catalog-show-more";
  button.textContent = `Show ${Math.min(QUICK_APPLIES_BATCH, remaining)} more (${remaining} remaining)`;
  button.addEventListener("click", () => {
    quickAppliesVisibleCount += QUICK_APPLIES_BATCH;
    renderQuickApplies();
  });
  wrap.appendChild(button);
  return wrap;
}

// Looks up the human-readable label for a vocabulary-backed profile value
// (e.g. citizenship "us_citizen" -> "U.S. citizen"), falling back to the raw
// value if the vocabulary has not loaded or the value is not found.
function vocabLabel(field, value) {
  if (!value) {
    return "";
  }
  const options = vocabulary?.[field] || [];
  const match = options.find((option) => option.value === value);
  return match ? match.label : value;
}

// Profile facts for fast form-filling on a sponsor's own site, built from the
// profile that produced the current matches (lastSubmittedProfile), not from
// live (possibly since-edited) form fields. Omits any empty field. Each fact
// is a {label, value} pair so it can copy on its own (application forms take
// one fact per box) or join into the full plain-text summary.
function buildProfileSummaryFields(profile) {
  if (!profile) {
    return [];
  }
  const fields = [];
  if (typeof profile.gpa === "number" && !Number.isNaN(profile.gpa)) {
    fields.push({ label: "GPA", value: String(profile.gpa) });
  }
  const gradeLabel = vocabLabel("grade_level", profile.grade_level);
  if (gradeLabel) {
    fields.push({ label: "Grade", value: gradeLabel });
  }
  const citizenshipLabel = vocabLabel("citizenship", profile.citizenship);
  if (citizenshipLabel) {
    fields.push({ label: "Citizenship", value: citizenshipLabel });
  }
  const stateLabel = vocabLabel("state", profile.state);
  if (stateLabel) {
    fields.push({ label: "State", value: stateLabel });
  }
  const studyFields = (profile.intended_majors || [])
    .map((value) => vocabLabel("fields_of_study", value))
    .filter(Boolean);
  if (studyFields.length > 0) {
    fields.push({ label: "Fields of study", value: studyFields.join(", ") });
  }
  if (profile.activities && profile.activities.length > 0) {
    fields.push({ label: "Activities", value: profile.activities.join(", ") });
  }
  return fields;
}

function buildProfileSummaryText(profile) {
  return buildProfileSummaryFields(profile)
    .map((field) => `${field.label}: ${field.value}`)
    .join("\n");
}

// One chip per profile fact; clicking copies just that fact's value, since
// sponsor forms want facts one box at a time.
function renderQuickApplyFieldChips() {
  const container = document.getElementById("quick-applies-fields");
  if (!container) {
    return;
  }
  const fields = buildProfileSummaryFields(lastSubmittedProfile);
  container.innerHTML = "";
  container.hidden = fields.length === 0;
  for (const field of fields) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "quick-apply-field-chip";
    chip.setAttribute("aria-label", `Copy ${field.label.toLowerCase()}`);
    chip.title = `Copy ${field.label.toLowerCase()}`;
    const label = document.createElement("strong");
    label.textContent = field.label;
    chip.append(label, document.createTextNode(` ${field.value}`));
    chip.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(field.value);
        chip.textContent = "Copied";
      } catch (err) {
        console.error(err);
        chip.textContent = "Could not copy";
      }
      window.setTimeout(renderQuickApplyFieldChips, 1400);
    });
    container.appendChild(chip);
  }
}

function wireQuickApplies() {
  if (!quickAppliesCopyBtn) {
    return;
  }
  const defaultLabel = quickAppliesCopyBtn.textContent;
  let resetTimer = null;
  quickAppliesCopyBtn.addEventListener("click", async () => {
    const text = buildProfileSummaryText(lastSubmittedProfile);
    window.clearTimeout(resetTimer);
    try {
      await navigator.clipboard.writeText(text);
      quickAppliesCopyBtn.textContent = "Copied";
    } catch (err) {
      console.error(err);
      quickAppliesCopyBtn.textContent = "Could not copy";
    }
    resetTimer = window.setTimeout(() => {
      quickAppliesCopyBtn.textContent = defaultLabel;
    }, 2000);
  });
}

/* ---------- Recommendation-letters rollup ---------- */
// Auto-derived from saved items' application_requirements: no separate storage,
// no manual entry. Matching steps already live in each item's checklist, so the
// checkbox here reuses that exact persistence path (patchSaved/patchSavedProgram/
// patchSavedCompetition writing completed_requirement_ids).

// "recommendation"/"recommender" rather than bare "recommend": catalog copy
// like "(optional but recommended)" or "5-6 recommended" is not a letter.
const REC_LETTER_PATTERN = /recommendation|recommender|reference letter|letter of reference/i;

function isRecLetterRequirement(requirement) {
  return REC_LETTER_PATTERN.test(requirement.id || "") || REC_LETTER_PATTERN.test(requirement.label || "");
}

function savedItemKind(item) {
  if (item.competition) return "competition";
  if (item.program) return "program";
  return "scholarship";
}

function savedItemId(item, kind) {
  if (kind === "program") return item.program_id;
  if (kind === "competition") return item.competition_id;
  return item.scholarship_id;
}

function savedItemPatcher(kind) {
  if (kind === "program") return patchSavedProgram;
  if (kind === "competition") return patchSavedCompetition;
  return patchSaved;
}

function savedItemKindPath(kind) {
  if (kind === "program") return "programs";
  if (kind === "competition") return "competitions";
  return "scholarships";
}

function collectRecLetterNeeds(items) {
  const needs = [];
  for (const item of items || []) {
    const kind = savedItemKind(item);
    for (const requirement of savedOpportunityRequirements(item)) {
      if (isRecLetterRequirement(requirement)) {
        needs.push({ item, kind, requirement });
      }
    }
  }
  needs.sort((a, b) => timelineSortValue(a.item) - timelineSortValue(b.item));
  return needs;
}

function renderRecLettersRollup(items) {
  if (!recLettersPanel) {
    return;
  }
  // With nothing saved, the saved-empty panel already explains the state;
  // showing this panel's empty state too reads as two empty messages at once.
  if (!items || items.length === 0) {
    recLettersPanel.hidden = true;
    return;
  }
  const needs = collectRecLetterNeeds(items);
  recLettersPanel.hidden = false;
  recLettersList.innerHTML = "";
  recLettersEmpty.hidden = needs.length > 0;
  if (recLettersCount) {
    recLettersCount.textContent = needs.length
      ? `${needs.length} recommendation letter${needs.length === 1 ? "" : "s"} across your saved items`
      : "";
  }
  for (const need of needs) {
    recLettersList.appendChild(buildRecLetterNeedRow(need));
  }
}

function buildRecLetterNeedRow({ item, kind, requirement }) {
  const itemId = savedItemId(item, kind);
  const patcher = savedItemPatcher(kind);

  const row = document.createElement("label");
  row.className = "tracker-task rec-letter-need";

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.checked = (item.completed_requirement_ids || []).includes(requirement.id);

  const copy = document.createElement("span");
  copy.className = "tracker-task-copy";
  const title = document.createElement("strong");
  title.textContent = requirement.label;
  copy.appendChild(title);

  const details = document.createElement("span");
  details.className = "tracker-task-details";
  const link = document.createElement("a");
  link.className = "card-title-link";
  link.href = `/${savedItemKindPath(kind)}/${encodeURIComponent(itemId)}`;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = savedOpportunityName(item);
  link.addEventListener("click", (event) => event.stopPropagation());
  details.appendChild(link);
  const dl = deadlineParts(savedOpportunityDeadline(item), savedOpportunityEstimatedDeadline(item));
  const deadlineText = document.createElement("span");
  deadlineText.textContent = ` · ${dl.value}${dl.note ? ` (${dl.note})` : ""}`;
  details.appendChild(deadlineText);
  copy.appendChild(details);

  row.appendChild(checkbox);
  row.appendChild(copy);

  checkbox.addEventListener("change", async () => {
    const before = new Set(item.completed_requirement_ids || []);
    const next = new Set(before);
    if (checkbox.checked) {
      next.add(requirement.id);
    } else {
      next.delete(requirement.id);
    }
    checkbox.disabled = true;
    const ok = await patcher(itemId, { completed_requirement_ids: Array.from(next) });
    checkbox.disabled = false;
    if (!ok) {
      checkbox.checked = before.has(requirement.id);
      return;
    }
    item.completed_requirement_ids = Array.from(next);
    // A saved card's own checklist checkbox for this same requirement is a
    // separate DOM element; refreshTrackerSummary() alone would leave it
    // stale (risking a later toggle there clobbering this change). Rebuild
    // the saved cards from the already-updated trackerItems so both views
    // agree on the truth.
    renderSaved(
      trackerItems.filter((i) => i.scholarship),
      trackerItems.filter((i) => i.program),
      trackerItems.filter((i) => i.competition)
    );
  });

  return row;
}

/* ---------- Journey map ----------
   The 2D illustrated progress map on the saved view. One state function reads
   the real saved data (all three lanes, via trackerItems) plus the session's
   lastResults; the illustrated scene's fog lifts as milestones are reached.
   Milestones read independent sources so a stale/unrun session never lies. */

// x-positions (percent) of the six landmarks in journey-map.webp, in order.
const JOURNEY_STOP_X = [6, 21, 40, 57, 74, 92];

function computeJourneyMapState() {
  const items = trackerItems || [];
  const known = new Set(SAVED_STATUSES.map((s) => s.value));
  const count = (v) => items.filter((it) => (it.status || "interested") === v).length;
  for (const it of items) {
    const s = it.status || "interested";
    if (!known.has(s)) console.warn(`Journey map: ignoring unknown saved status "${s}"`);
  }
  const rejected = count("rejected");
  const activeSaved = items.length - rejected; // active = everything not rejected
  const drafting = count("drafting");
  const submitted = count("submitted");
  const awarded = count("awarded");
  const matchesRun = Boolean(lastResults && lastResults.length);
  // Reaching the authenticated saved view means a profile exists.
  const stops = [
    { key: "profile", label: "Profile", reached: true, badge: "Done" },
    { key: "matches", label: "Matches", reached: matchesRun,
      badge: matchesRun ? String(lastResults.length) : "Not run", muted: !matchesRun },
    { key: "saved", label: "Saved", reached: activeSaved > 0, badge: String(activeSaved) },
    { key: "drafting", label: "Drafting", reached: drafting > 0, badge: String(drafting) },
    { key: "submitted", label: "Submitted", reached: submitted > 0, badge: String(submitted) },
    { key: "awarded", label: "Awarded", reached: awarded > 0, badge: String(awarded), flag: true },
  ];
  let reachedIndex = -1;
  stops.forEach((s, i) => { if (s.reached) reachedIndex = i; });
  return { stops, reachedIndex, rejected, activeSaved, submitted, awarded };
}

function journeyStatusLine(state) {
  if (state.activeSaved === 0) {
    return "Your trail starts here. Save opportunities that fit you.";
  }
  const parts = [`${state.activeSaved} active`];
  if (state.submitted) parts.push(`${state.submitted} submitted`);
  if (state.awarded) parts.push(`${state.awarded} awarded`);
  return parts.join(", ");
}

function renderJourneyMap() {
  if (!journeyMap) return;
  const state = computeJourneyMapState();
  // Fog covers from just past the furthest reached stop to the end.
  const ri = state.reachedIndex;
  const fogStart = ri >= JOURNEY_STOP_X.length - 1
    ? 101
    : (JOURNEY_STOP_X[ri] + JOURNEY_STOP_X[ri + 1]) / 2;
  const stopsHtml = state.stops.map((s, i) => {
    const cls = ["journey-stop"];
    cls.push(s.reached ? "is-reached" : "is-ahead");
    if (s.flag) cls.push("is-flag");
    if (s.muted) cls.push("is-muted");
    return (
      `<li class="${cls.join(" ")}" style="--x:${JOURNEY_STOP_X[i]}%">` +
      `<span class="journey-stop-dot" aria-hidden="true"></span>` +
      `<span class="journey-stop-badge">${escapeHtml(s.badge)}</span>` +
      `<span class="journey-stop-label">${escapeHtml(s.label)}</span>` +
      `</li>`
    );
  }).join("");
  const rejectedHtml = state.rejected
    ? `<p class="journey-map-rejected">${state.rejected} not this cycle, and that is part of the path too.</p>`
    : "";
  journeyMap.innerHTML =
    `<div class="journey-map-head">` +
      `<p class="eyebrow">Your journey</p>` +
      `<h3 id="journey-map-title">Your path to award day</h3>` +
      `<p class="journey-map-status">${escapeHtml(journeyStatusLine(state))}</p>` +
    `</div>` +
    `<div class="journey-map-scene" style="--fog-start:${fogStart}%">` +
      `<div class="journey-map-fog" aria-hidden="true"></div>` +
      `<ol class="journey-map-stops">${stopsHtml}</ol>` +
    `</div>` +
    rejectedHtml;
  journeyMap.hidden = false;
}

function renderSaved(scholarshipItems, programItems = [], competitionItems = []) {
  const items = [
    ...(scholarshipItems || []),
    ...(programItems || []),
    ...(competitionItems || []),
  ];
  trackerItems = items;
  renderJourneyMap();
  savedContainer.innerHTML = "";
  renderRecLettersRollup(items);
  renderQuickApplies();
  if (items.length === 0) {
    savedSummary.textContent = "";
    savedEmpty.hidden = false;
    return;
  }
  savedEmpty.hidden = true;
  savedSummary.textContent = trackerSummary(items);
  savedContainer.appendChild(buildPlanGuidance(items));

  for (const item of items) {
    if (!item.scholarship) {
      continue;
    }
    // A saved item is part of the application tracker, not a fresh match for
    // the current profile. Give it neutral tracker styling instead of claiming
    // it is a strong match.
    const card = buildCard(scholarshipToCard(item.scholarship), "saved");
    card.classList.add(`status-${item.status || "interested"}`);
    // Append inside the card-body (the wide grid column), not the card grid
    // itself, or the controls land in the narrow path-bar column.
    const cardBody = card.querySelector(".card-body");
    (cardBody || card).appendChild(buildTrackerControls(item, card, "scholarship"));
    savedContainer.appendChild(card);
  }

  for (const item of programItems || []) {
    if (!item.program) {
      continue;
    }
    const card = buildProgramCard(item.program, { savedContext: true });
    card.classList.add(`status-${item.status || "interested"}`);
    const cardBody = card.querySelector(".card-body");
    (cardBody || card).appendChild(buildTrackerControls(item, card, "program"));
    savedContainer.appendChild(card);
  }

  for (const item of competitionItems || []) {
    if (!item.competition) {
      continue;
    }
    const card = buildCompetitionCard(item.competition, { savedContext: true });
    card.classList.add(`status-${item.status || "interested"}`);
    const cardBody = card.querySelector(".card-body");
    (cardBody || card).appendChild(buildTrackerControls(item, card, "competition"));
    savedContainer.appendChild(card);
  }
}

function savedOpportunity(item) {
  return item.scholarship || item.program || item.competition || null;
}

function savedOpportunityKind(item) {
  if (item.competition) {
    return "Competition";
  }
  return item.program ? "Program" : "Scholarship";
}

function savedOpportunityName(item) {
  const opportunity = savedOpportunity(item);
  return opportunity?.name || opportunity?.scholarship_name || "Saved opportunity";
}

function savedOpportunityDeadline(item) {
  const opportunity = savedOpportunity(item);
  return opportunity?.deadline || "";
}

function savedOpportunityEstimatedDeadline(item) {
  const opportunity = savedOpportunity(item);
  return opportunity?.estimated_deadline || null;
}

function savedOpportunityRequirements(item) {
  return savedOpportunity(item)?.application_requirements || [];
}

function savedOpportunitySpecialRequirements(item) {
  const opportunity = savedOpportunity(item);
  return opportunity?.special_requirements?.length
    ? opportunity.special_requirements
    : opportunity?.eligibility?.special_requirements || [];
}

function parseRealDeadline(deadline) {
  if (!deadline || deadline === "rolling" || String(deadline).startsWith("VERIFY")) {
    return null;
  }
  const parsed = new Date(`${deadline}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function daysUntil(deadline) {
  const parsed = parseRealDeadline(deadline);
  if (!parsed) {
    return null;
  }
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.ceil((parsed - today) / (1000 * 60 * 60 * 24));
}

function deadlinePriority(item) {
  const realDays = daysUntil(savedOpportunityDeadline(item));
  if (realDays === null) {
    return 12000;
  }
  return realDays < 0 ? 30000 + Math.abs(realDays) : realDays;
}

function incompleteRequirements(item) {
  const completed = new Set(item.completed_requirement_ids || []);
  return savedOpportunityRequirements(item).filter((requirement) => !completed.has(requirement.id));
}

function requirementMatches(requirement, patterns) {
  const text = `${requirement.label || ""} ${requirement.details || ""}`.toLowerCase();
  return patterns.some((pattern) => text.includes(pattern));
}

function firstIncompleteRequired(items) {
  const sorted = [...items].sort((a, b) => {
    return deadlinePriority(a) - deadlinePriority(b);
  });
  for (const item of sorted) {
    const next = incompleteRequirements(item).find((requirement) => requirement.required !== false);
    if (next) {
      return { item, requirement: next };
    }
  }
  return null;
}

function collectRequirementNeeds(items, patterns, limit = 4) {
  const needs = [];
  for (const item of items) {
    for (const requirement of incompleteRequirements(item)) {
      if (requirementMatches(requirement, patterns)) {
        needs.push({ item, requirement });
      }
    }
  }
  return needs.slice(0, limit);
}

function formatNeedList(needs) {
  return needs
    .map(({ item, requirement }) => `${savedOpportunityName(item)}: ${requirement.label}`)
    .join("; ");
}

const REQUIREMENT_GROUPS = [
  {
    key: "writing",
    label: "Writing",
    patterns: ["essay", "short answer", "short-answer", "response", "personal statement", "statement"],
  },
  {
    key: "recommendations",
    label: "Recs",
    patterns: ["recommend", "teacher", "counselor", "reference", "letter"],
  },
  {
    key: "records",
    label: "Records",
    patterns: ["transcript", "grade report", "academic record", "school profile", "test score"],
  },
  {
    key: "forms",
    label: "Forms",
    patterns: ["application", "form", "portal", "account", "submit"],
  },
  {
    key: "interview",
    label: "Interview",
    patterns: ["interview", "finalist", "selection weekend"],
  },
];

function requirementGroup(requirement) {
  const text = `${requirement.label || ""} ${requirement.details || ""}`.toLowerCase();
  return (
    REQUIREMENT_GROUPS.find((group) =>
      group.patterns.some((pattern) => text.includes(pattern))
    ) || { key: "other", label: "Other" }
  );
}

function requirementMatrixForItem(item) {
  const completed = new Set(item.completed_requirement_ids || []);
  const matrix = Object.fromEntries(
    [...REQUIREMENT_GROUPS, { key: "other", label: "Other" }].map((group) => [
      group.key,
      { total: 0, complete: 0 },
    ])
  );
  for (const requirement of savedOpportunityRequirements(item)) {
    const group = requirementGroup(requirement);
    matrix[group.key].total += 1;
    if (completed.has(requirement.id)) {
      matrix[group.key].complete += 1;
    }
  }
  return matrix;
}

function formatRequirementProgress(progress) {
  if (!progress.total) {
    return "None";
  }
  return `${progress.complete}/${progress.total}`;
}

function buildRequirementMatrix(items) {
  const section = document.createElement("section");
  section.className = "plan-matrix";
  section.setAttribute("aria-label", "Requirement matrix");

  const head = document.createElement("div");
  head.className = "plan-subsection-head";
  head.innerHTML =
    "<div><p class=\"eyebrow\">Requirement matrix</p>" +
    "<h4>See what each opportunity is asking for</h4></div>" +
    "<p>Counts show completed checklist steps over total source-linked steps.</p>";
  section.appendChild(head);

  const tableWrap = document.createElement("div");
  tableWrap.className = "plan-table-wrap";
  const table = document.createElement("table");
  table.className = "plan-table";
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  ["Opportunity", ...REQUIREMENT_GROUPS.map((group) => group.label), "Other"].forEach((label) => {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = label;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  for (const item of items) {
    const row = document.createElement("tr");
    const name = document.createElement("th");
    name.scope = "row";
    const kind = document.createElement("span");
    kind.textContent = savedOpportunityKind(item);
    const strong = document.createElement("strong");
    strong.textContent = savedOpportunityName(item);
    name.appendChild(kind);
    name.appendChild(strong);
    row.appendChild(name);

    const matrix = requirementMatrixForItem(item);
    [...REQUIREMENT_GROUPS.map((group) => group.key), "other"].forEach((key) => {
      const td = document.createElement("td");
      const progress = matrix[key];
      td.textContent = formatRequirementProgress(progress);
      if (progress.total && progress.complete === progress.total) {
        td.className = "is-complete";
      } else if (progress.total) {
        td.className = "has-work";
      }
      row.appendChild(td);
    });
    tbody.appendChild(row);
  }
  table.appendChild(tbody);
  tableWrap.appendChild(table);
  section.appendChild(tableWrap);
  return section;
}

function timelineSortValue(item) {
  const realDays = daysUntil(savedOpportunityDeadline(item));
  if (realDays !== null) {
    return realDays < 0 ? 30000 + Math.abs(realDays) : realDays;
  }
  const deadline = savedOpportunityDeadline(item);
  if (deadline === "rolling") {
    return 20000;
  }
  if (String(deadline || "").startsWith("VERIFY")) {
    return 15000;
  }
  return 12000;
}

function timelineStatus(item) {
  const realDays = daysUntil(savedOpportunityDeadline(item));
  if (realDays === null) {
    const parts = deadlineParts(savedOpportunityDeadline(item), savedOpportunityEstimatedDeadline(item));
    return parts.note ? `${parts.value} · ${parts.note}` : parts.value;
  }
  if (realDays < 0) {
    return "Deadline passed";
  }
  if (realDays === 0) {
    return "Due today";
  }
  if (realDays <= 14) {
    return `Due in ${realDays} day${realDays === 1 ? "" : "s"}`;
  }
  return `Due in ${realDays} days`;
}

function buildDeadlineTimeline(items) {
  const section = document.createElement("section");
  section.className = "plan-timeline";
  section.setAttribute("aria-label", "Deadline timeline");

  const head = document.createElement("div");
  head.className = "plan-subsection-head";
  head.innerHTML =
    "<div><p class=\"eyebrow\">Deadline timeline</p>" +
    "<h4>Order your work by time pressure</h4></div>" +
    "<p>Verified dates come first; estimated or unknown dates stay labeled.</p>";
  section.appendChild(head);

  const list = document.createElement("div");
  list.className = "timeline-list";
  const sorted = [...items].sort((a, b) => timelineSortValue(a) - timelineSortValue(b));

  for (const item of sorted.slice(0, 8)) {
    const row = document.createElement("article");
    const realDays = daysUntil(savedOpportunityDeadline(item));
    row.className = "timeline-item";
    if (realDays !== null && realDays <= 14 && realDays >= 0) {
      row.classList.add("is-urgent");
    } else if (realDays !== null && realDays < 0) {
      row.classList.add("is-past");
    } else if (realDays === null) {
      row.classList.add("is-estimated");
    }

    const date = document.createElement("span");
    date.className = "timeline-date";
    date.textContent = timelineStatus(item);

    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = savedOpportunityName(item);
    const next = incompleteRequirements(item).find((requirement) => requirement.required !== false);
    const detail = document.createElement("p");
    detail.textContent = next
      ? `${savedOpportunityKind(item)} · next step: ${next.label}`
      : `${savedOpportunityKind(item)} · checklist complete or no source-linked steps yet`;
    copy.appendChild(title);
    copy.appendChild(detail);

    const startBy = essayStartByLabel(item);
    if (startBy) {
      const startLine = document.createElement("p");
      startLine.className = "timeline-start-by";
      startLine.textContent = startBy;
      copy.appendChild(startLine);
    }

    row.appendChild(date);
    row.appendChild(copy);
    list.appendChild(row);
  }

  section.appendChild(list);
  return section;
}

const WRITING_REUSE_GROUPS = [
  {
    key: "identity",
    label: "Identity, community, and lived experience",
    patterns: ["identity", "community", "background", "experiences", "adversit", "story"],
  },
  {
    key: "why-fit",
    label: "Why this program or scholarship",
    patterns: ["why", "fit", "course", "program", "major", "future goals", "career"],
  },
  {
    key: "leadership-service",
    label: "Leadership, service, and impact",
    patterns: ["leadership", "service", "impact", "improving", "courage", "veteran", "activities"],
  },
  {
    key: "academic-research",
    label: "Academic interest, research, or problem solving",
    patterns: ["academic", "research", "problem set", "solutions", "project", "stem", "science", "mathematics"],
  },
  {
    key: "general-writing",
    label: "General essays and short answers",
    patterns: ["essay", "short answer", "short-answer", "response", "statement", "writing"],
  },
];

function isWritingRequirement(requirement) {
  return requirementMatches(requirement, [
    "essay",
    "short answer",
    "short-answer",
    "response",
    "statement",
    "writing",
    "problem set",
    "solutions",
  ]);
}

function writingReuseGroup(requirement) {
  const text = `${requirement.label || ""} ${requirement.details || ""}`.toLowerCase();
  return (
    WRITING_REUSE_GROUPS.find((group) =>
      group.patterns.some((pattern) => text.includes(pattern))
    ) || WRITING_REUSE_GROUPS[WRITING_REUSE_GROUPS.length - 1]
  );
}

function collectWritingClusters(items) {
  const clusters = new Map(
    WRITING_REUSE_GROUPS.map((group) => [group.key, { group, needs: [] }])
  );
  for (const item of items) {
    for (const requirement of incompleteRequirements(item)) {
      if (!isWritingRequirement(requirement)) {
        continue;
      }
      const group = writingReuseGroup(requirement);
      clusters.get(group.key).needs.push({ item, requirement });
    }
  }
  return Array.from(clusters.values())
    .filter((cluster) => cluster.needs.length > 0)
    .sort((a, b) => b.needs.length - a.needs.length);
}

function buildPromptBlock(requirement) {
  const prompts = requirement.essay_prompts;
  if (!prompts) {
    if (!isWritingRequirement(requirement)) return null;
    const note = document.createElement("p");
    note.className = "prompt-gated";
    note.textContent = "Essay prompts not yet verified - check the sponsor page.";
    return note;
  }
  if (prompts.status === "gated") {
    const note = document.createElement("p");
    note.className = "prompt-gated";
    note.textContent = "Prompts revealed after registration on the sponsor site.";
    return note;
  }
  if (prompts.status !== "public" || !prompts.items?.length) return null;
  const details = document.createElement("details");
  details.className = "prompt-details";
  const summary = document.createElement("summary");
  summary.textContent = prompts.items.length > 1 ? "Essay prompts" : "Essay prompt";
  details.appendChild(summary);
  const list = document.createElement("ul");
  list.className = "prompt-list";
  for (const item of prompts.items) {
    const li = document.createElement("li");
    li.textContent = item.prompt;
    if (item.length) {
      const chip = document.createElement("span");
      chip.className = "prompt-length";
      chip.textContent = item.length;
      li.appendChild(document.createTextNode(" "));
      li.appendChild(chip);
    }
    list.appendChild(li);
  }
  details.appendChild(list);
  return details;
}

const ESSAY_START_LEAD_DAYS = 21;

function essayStartByDate(item) {
  const hasWriting = incompleteRequirements(item).some((requirement) =>
    isWritingRequirement(requirement)
  );
  if (!hasWriting) return null;

  // parseRealDeadline() treats "rolling"/"VERIFY"/empty as "no real deadline"
  // (returns null), which is exactly the signal we need to fall back to the
  // estimated deadline instead of misreading those sentinel strings as dates.
  const rawDeadline = savedOpportunityDeadline(item);
  // Rolling deadlines accept applications anytime; falling through to the
  // estimated-deadline branch would print a start-by date right beside a
  // status line reading "Applications accepted anytime" (mirrors
  // deadlineParts(), which also ignores estimates for rolling items).
  if (rawDeadline === "rolling") return null;
  const realDeadline = parseRealDeadline(rawDeadline);
  let target;
  if (realDeadline) {
    // A real deadline that already passed gets no start-by line; the
    // timeline row already reads "Deadline passed" for it.
    if (isPastDate(rawDeadline)) return null;
    target = realDeadline;
  } else {
    // No usable real deadline: fall back to the estimated one, but skip a
    // stale last-cycle estimate (mirrors deadlineParts()'s "Not yet
    // announced" handling) instead of rendering "Essays: start now" for an
    // unannounced next cycle.
    const estimated = savedOpportunityEstimatedDeadline(item);
    if (!estimated || isPastDate(estimated)) return null;
    target = parseRealDeadline(estimated);
    if (!target) return null;
  }

  target.setDate(target.getDate() - ESSAY_START_LEAD_DAYS);
  return target;
}

function essayStartByLabel(item) {
  const start = essayStartByDate(item);
  if (!start) return null;
  if (start <= new Date()) return "Essays: start now";
  const text = start.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  return `Start drafting by ${text}`;
}

function buildEssayReuseMap(items) {
  const section = document.createElement("section");
  section.className = "plan-essay-map";
  section.setAttribute("aria-label", "Essay reuse map");

  const head = document.createElement("div");
  head.className = "plan-subsection-head";
  head.innerHTML =
    "<div><p class=\"eyebrow\">Essay reuse map</p>" +
    "<h4>Draft once, tailor carefully</h4></div>" +
    "<p>Groups unfinished writing steps by likely reusable theme. Always answer each official prompt directly.</p>";
  section.appendChild(head);

  const clusters = collectWritingClusters(items);
  const wrap = document.createElement("div");
  wrap.className = "essay-clusters";
  if (!clusters.length) {
    const empty = document.createElement("p");
    empty.className = "plan-empty-note";
    empty.textContent = "No unfinished essay, short-answer, or problem-set steps detected in your saved checklist.";
    wrap.appendChild(empty);
  }

  for (const cluster of clusters.slice(0, 5)) {
    const card = document.createElement("article");
    card.className = "essay-cluster";
    const title = document.createElement("h5");
    title.textContent = cluster.group.label;
    const meta = document.createElement("p");
    const count = cluster.needs.length;
    meta.textContent = `${count} unfinished writing step${count === 1 ? "" : "s"} could share a base draft.`;

    const startDates = cluster.needs
      .map((need) => essayStartByDate(need.item))
      .filter(Boolean);

    const list = document.createElement("ul");
    for (const need of cluster.needs.slice(0, 4)) {
      const li = document.createElement("li");
      li.textContent = `${savedOpportunityName(need.item)}: ${need.requirement.label}`;
      const promptBlock = buildPromptBlock(need.requirement);
      if (promptBlock) li.appendChild(promptBlock);
      list.appendChild(li);
    }
    if (cluster.needs.length > 4) {
      const li = document.createElement("li");
      li.textContent = `+ ${cluster.needs.length - 4} more`;
      list.appendChild(li);
    }

    card.appendChild(title);
    card.appendChild(meta);
    if (startDates.length) {
      const earliest = new Date(Math.min(...startDates.map((d) => d.getTime())));
      const startLine = document.createElement("p");
      startLine.className = "essay-cluster-start";
      startLine.textContent =
        earliest <= new Date()
          ? "Earliest start: now"
          : `Earliest start: ${earliest.toLocaleDateString("en-US", { month: "short", day: "numeric" })}`;
      card.appendChild(startLine);
    }
    card.appendChild(list);
    const guideLink = document.createElement("a");
    guideLink.className = "essay-guide-link";
    guideLink.href = `/guides/essays/${cluster.group.key}`;
    guideLink.textContent = "How to write this kind of essay";
    card.appendChild(guideLink);
    wrap.appendChild(card);
  }

  section.appendChild(wrap);
  return section;
}

function buildSpecialEligibilityPanel(items) {
  const section = document.createElement("section");
  section.className = "plan-special-panel";
  section.setAttribute("aria-label", "Special eligibility checks");

  const head = document.createElement("div");
  head.className = "plan-subsection-head";
  head.innerHTML =
    "<div><p class=\"eyebrow\">Special eligibility checks</p>" +
    "<h4>Confirm the strict gates before going deep</h4></div>" +
    "<p>These are niche requirements like nomination, finalist status, membership, or sponsor affiliation.</p>";
  section.appendChild(head);

  const specialItems = items.filter((item) => savedOpportunitySpecialRequirements(item).length > 0);
  const wrap = document.createElement("div");
  wrap.className = "special-check-list";
  if (!specialItems.length) {
    const empty = document.createElement("p");
    empty.className = "plan-empty-note";
    empty.textContent = "No special eligibility checks detected in the opportunities you saved.";
    wrap.appendChild(empty);
  }

  for (const item of specialItems) {
    const card = document.createElement("article");
    card.className = "special-check-card";
    const title = document.createElement("h5");
    title.textContent = savedOpportunityName(item);
    const type = document.createElement("p");
    type.textContent = `${savedOpportunityKind(item)} · verify this before investing major time`;
    const list = document.createElement("ul");
    for (const check of savedOpportunitySpecialRequirements(item)) {
      const li = document.createElement("li");
      li.textContent = specialRequirementText(check);
      list.appendChild(li);
    }
    card.appendChild(title);
    card.appendChild(type);
    card.appendChild(list);
    wrap.appendChild(card);
  }

  section.appendChild(wrap);
  return section;
}

function specialRequirementText(requirement) {
  if (typeof requirement === "string") {
    return requirement;
  }
  const label = requirement?.label || "Extra eligibility check";
  return requirement?.details ? `${label}: ${requirement.details}` : label;
}

function deadlineUrgencyText(item) {
  const deadline = savedOpportunityDeadline(item);
  const realDays = daysUntil(deadline);
  if (realDays === null) {
    const parts = deadlineParts(deadline, savedOpportunityEstimatedDeadline(item));
    return `${savedOpportunityName(item)}: ${parts.value}${parts.note ? ` (${parts.note})` : ""}`;
  }
  if (realDays < 0) {
    return `${savedOpportunityName(item)}: deadline has passed`;
  }
  if (realDays === 0) {
    return `${savedOpportunityName(item)}: due today`;
  }
  return `${savedOpportunityName(item)}: due in ${realDays} day${realDays === 1 ? "" : "s"}`;
}

function makePlanCard(title, body, meta = "", tone = "") {
  const card = document.createElement("article");
  card.className = `plan-card ${tone ? `plan-card-${tone}` : ""}`;
  const heading = document.createElement("h4");
  heading.textContent = title;
  const copy = document.createElement("p");
  copy.textContent = body;
  card.appendChild(heading);
  card.appendChild(copy);
  if (meta) {
    const detail = document.createElement("span");
    detail.className = "plan-card-meta";
    detail.textContent = meta;
    card.appendChild(detail);
  }
  return card;
}

function buildPlanGuidance(items) {
  const wrap = document.createElement("div");
  wrap.className = "plan-guidance";

  const totalSteps = items.reduce(
    (sum, item) => sum + savedOpportunityRequirements(item).length,
    0
  );
  const completedSteps = items.reduce(
    (sum, item) => sum + (item.completed_requirement_ids?.length || 0),
    0
  );
  const specialChecks = items.filter((item) => savedOpportunitySpecialRequirements(item).length > 0);
  const realDeadlineItems = items
    .filter((item) => daysUntil(savedOpportunityDeadline(item)) !== null)
    .sort((a, b) => deadlinePriority(a) - deadlinePriority(b));
  const upcomingDeadlines = realDeadlineItems.filter(
    (item) => daysUntil(savedOpportunityDeadline(item)) >= 0
  );
  const nextRequired = firstIncompleteRequired(items);
  const recommendationNeeds = collectRequirementNeeds(items, [
    "recommend",
    "teacher",
    "counselor",
    "reference",
  ]);
  const writingNeeds = collectRequirementNeeds(items, [
    "essay",
    "short answer",
    "short-answer",
    "response",
    "personal statement",
    "problem set",
  ]);
  const transcriptNeeds = collectRequirementNeeds(items, [
    "transcript",
    "grade report",
    "academic record",
    "school profile",
  ]);

  const head = document.createElement("div");
  head.className = "plan-guidance-head";
  head.innerHTML =
    "<div><p class=\"eyebrow\">Application command center</p>" +
    "<h3>What needs attention next</h3>" +
    "<p>Built from your saved opportunities and their source-linked checklist steps.</p></div>" +
    `<div class="plan-progress"><strong>${completedSteps}/${totalSteps || 0}</strong><span>steps complete</span></div>`;
  wrap.appendChild(head);

  const stats = document.createElement("div");
  stats.className = "plan-stats";
  stats.appendChild(makePlanCard("Saved", `${items.length} active item${items.length === 1 ? "" : "s"}`));
  stats.appendChild(makePlanCard("Verified steps", totalSteps ? `${totalSteps - completedSteps} left` : "No checklist steps yet"));
  stats.appendChild(makePlanCard("Special checks", `${specialChecks.length} to confirm`));
  stats.appendChild(makePlanCard("Real deadlines", `${upcomingDeadlines.length} dated item${upcomingDeadlines.length === 1 ? "" : "s"}`));
  wrap.appendChild(stats);

  const actions = document.createElement("div");
  actions.className = "plan-actions";
  if (nextRequired) {
    actions.appendChild(
      makePlanCard(
        "Do this next",
        nextRequired.requirement.label,
        `${savedOpportunityKind(nextRequired.item)} - ${savedOpportunityName(nextRequired.item)}`,
        "primary"
      )
    );
  } else {
    actions.appendChild(
      makePlanCard(
        "Do this next",
        "Save an opportunity with checklist steps, or mark your remaining steps complete.",
        "The plan updates as you save and check items off.",
        "primary"
      )
    );
  }
  actions.appendChild(
    makePlanCard(
      "Recommendations",
      recommendationNeeds.length ? formatNeedList(recommendationNeeds) : "No unfinished recommendation steps detected.",
      recommendationNeeds.length ? "Ask early; recommenders are usually the bottleneck." : "",
      "recommendation"
    )
  );
  actions.appendChild(
    makePlanCard(
      "Writing work",
      writingNeeds.length ? formatNeedList(writingNeeds) : "No unfinished essays or written-response steps detected.",
      writingNeeds.length ? "See the essay reuse map below for likely shared draft themes." : "",
      "writing"
    )
  );
  actions.appendChild(
    makePlanCard(
      "Transcripts & records",
      transcriptNeeds.length ? formatNeedList(transcriptNeeds) : "No unfinished transcript or academic-record steps detected.",
      transcriptNeeds.length ? "Some must come from school staff, so start early." : "",
      "records"
    )
  );
  if (specialChecks.length) {
    actions.appendChild(
      makePlanCard(
        "Special eligibility",
        specialChecks.map((item) => savedOpportunityName(item)).join("; "),
        "Confirm nomination, membership, finalist status, or affiliation before investing heavy effort.",
        "special"
      )
    );
  }
  if (upcomingDeadlines.length) {
    actions.appendChild(
      makePlanCard(
        "Upcoming deadlines",
        upcomingDeadlines.slice(0, 3).map(deadlineUrgencyText).join("; "),
        "Only verified ISO deadlines are counted here.",
        "deadline"
      )
    );
  }
  wrap.appendChild(actions);
  wrap.appendChild(buildRequirementMatrix(items));
  wrap.appendChild(buildEssayReuseMap(items));
  wrap.appendChild(buildSpecialEligibilityPanel(items));
  wrap.appendChild(buildDeadlineTimeline(items));

  return wrap;
}

function buildTrackerControls(item, card, kind = "scholarship") {
  const wrap = document.createElement("div");
  wrap.className = "tracker-controls";

  const itemId =
    kind === "program"
      ? item.program_id
      : kind === "competition"
      ? item.competition_id
      : item.scholarship_id;
  const patcher =
    kind === "program"
      ? patchSavedProgram
      : kind === "competition"
      ? patchSavedCompetition
      : patchSaved;

  const checklist = buildApplicationChecklist(item, kind);
  if (checklist) {
    wrap.appendChild(checklist);
  }

  const statusField = document.createElement("div");
  statusField.className = "tracker-field";
  const statusLabelEl = document.createElement("span");
  statusLabelEl.className = "tracker-label";
  statusLabelEl.textContent = "Status";
  const select = document.createElement("select");
  select.className = "tracker-status";
  for (const opt of SAVED_STATUSES) {
    const option = document.createElement("option");
    option.value = opt.value;
    option.textContent = opt.label;
    if ((item.status || "interested") === opt.value) {
      option.selected = true;
    }
    select.appendChild(option);
  }
  select.addEventListener("change", async () => {
    const ok = await patcher(itemId, { status: select.value });
    if (ok) {
      item.status = select.value;
      card.className = card.className.replace(/\bstatus-\w+\b/, `status-${select.value}`);
      refreshTrackerSummary();
    }
  });
  statusField.appendChild(statusLabelEl);
  statusField.appendChild(select);

  const notesField = document.createElement("div");
  notesField.className = "tracker-field tracker-field-notes";
  const notesLabelEl = document.createElement("span");
  notesLabelEl.className = "tracker-label";
  notesLabelEl.textContent = "Notes";
  const notes = document.createElement("textarea");
  notes.className = "tracker-notes";
  notes.rows = 2;
  notes.maxLength = 2000;
  notes.value = item.notes || "";
  notes.placeholder = "Deadlines, requirements, where you left off...";
  let lastSaved = item.notes || "";
  notes.addEventListener("blur", () => {
    if (notes.value !== lastSaved) {
      lastSaved = notes.value;
      patcher(itemId, { notes: notes.value });
    }
  });
  notesField.appendChild(notesLabelEl);
  notesField.appendChild(notes);

  wrap.appendChild(statusField);
  wrap.appendChild(notesField);
  return wrap;
}

function buildApplicationChecklist(item, kind = "scholarship") {
  const requirements =
    kind === "program"
      ? item.program?.application_requirements || []
      : kind === "competition"
      ? item.competition?.application_requirements || []
      : item.scholarship?.application_requirements || [];
  if (!requirements.length) {
    return null;
  }

  const itemId =
    kind === "program"
      ? item.program_id
      : kind === "competition"
      ? item.competition_id
      : item.scholarship_id;
  const patcher =
    kind === "program"
      ? patchSavedProgram
      : kind === "competition"
      ? patchSavedCompetition
      : patchSaved;

  const field = document.createElement("div");
  field.className = "tracker-field tracker-checklist";
  const header = document.createElement("div");
  header.className = "tracker-checklist-header";
  const label = document.createElement("span");
  label.className = "tracker-label";
  label.textContent = "Application checklist";
  const progress = document.createElement("span");
  progress.className = "tracker-checklist-progress";
  header.appendChild(label);
  header.appendChild(progress);
  field.appendChild(header);
  const nextAction = document.createElement("span");
  nextAction.className = "tracker-checklist-next";
  field.appendChild(nextAction);

  const requirementIds = new Set(requirements.map((requirement) => requirement.id));
  let completed = new Set(
    (item.completed_requirement_ids || []).filter((requirementId) => requirementIds.has(requirementId))
  );
  const updateProgress = () => {
    progress.textContent = `${completed.size}/${requirements.length} complete`;
    const nextRequired = requirements.find(
      (requirement) => requirement.required !== false && !completed.has(requirement.id)
    );
    const nextAny = requirements.find((requirement) => !completed.has(requirement.id));
    if (nextRequired) {
      nextAction.textContent = `Next: ${nextRequired.label}`;
    } else if (nextAny) {
      nextAction.textContent = `Optional next: ${nextAny.label}`;
    } else {
      nextAction.textContent = "All verified steps complete";
    }
  };
  updateProgress();

  for (const requirement of requirements) {
    const task = document.createElement("label");
    task.className = "tracker-task";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = completed.has(requirement.id);
    const copy = document.createElement("span");
    copy.className = "tracker-task-copy";
    const title = document.createElement("strong");
    title.textContent = requirement.label;
    copy.appendChild(title);
    if (requirement.required === false) {
      const optional = document.createElement("span");
      optional.className = "tracker-task-optional";
      optional.textContent = "Optional";
      copy.appendChild(optional);
    }
    if (requirement.details) {
      const details = document.createElement("span");
      details.className = "tracker-task-details";
      details.textContent = requirement.details;
      copy.appendChild(details);
    }
    if (requirement.source_url) {
      const source = document.createElement("a");
      source.href = requirement.source_url;
      source.target = "_blank";
      source.rel = "noopener noreferrer";
      source.textContent = "Source";
      source.addEventListener("click", (event) => event.stopPropagation());
      copy.appendChild(source);
    }
    task.appendChild(checkbox);
    task.appendChild(copy);
    const promptBlock = buildPromptBlock(requirement);
    if (promptBlock) {
      promptBlock.addEventListener("click", (event) => {
        event.stopPropagation();
        // The row is a <label>: clicking a plain element inside it forwards
        // the click to the checkbox as a default action, which only
        // preventDefault can cancel. The public-prompt <details> block is
        // exempt (interactive content) and must keep its toggle default.
        if (!(event.currentTarget instanceof HTMLDetailsElement)) {
          event.preventDefault();
        }
      });
      task.appendChild(promptBlock);
    }
    checkbox.addEventListener("change", async () => {
      const before = new Set(completed);
      if (checkbox.checked) {
        completed.add(requirement.id);
      } else {
        completed.delete(requirement.id);
      }
      checkbox.disabled = true;
      updateProgress();
      const ok = await patcher(itemId, {
        completed_requirement_ids: Array.from(completed),
      });
      checkbox.disabled = false;
      if (!ok) {
        completed = before;
        checkbox.checked = completed.has(requirement.id);
        updateProgress();
        return;
      }
      item.completed_requirement_ids = Array.from(completed);
      refreshTrackerSummary();
    });
    field.appendChild(task);
  }
  return field;
}

async function patchSaved(scholarshipId, payload) {
  try {
    const response = await fetch(`/account/saved/${encodeURIComponent(scholarshipId)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return response.ok;
  } catch (err) {
    console.error(err);
    return false;
  }
}

async function patchSavedProgram(programId, payload) {
  try {
    const response = await fetch(`/account/saved/programs/${encodeURIComponent(programId)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return response.ok;
  } catch (err) {
    console.error(err);
    return false;
  }
}

async function patchSavedCompetition(competitionId, payload) {
  try {
    const response = await fetch(
      `/account/saved/competitions/${encodeURIComponent(competitionId)}`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );
    return response.ok;
  } catch (err) {
    console.error(err);
    return false;
  }
}

async function toggleSavedCompetition(competitionId, button) {
  if (!currentUser) {
    openAuthModal("login", "Log in to save competitions to your account.");
    return;
  }

  const isSaved = savedCompetitionIds.has(competitionId);
  button.disabled = true;
  try {
    const response = await fetch(
      `/account/saved/competitions/${encodeURIComponent(competitionId)}`,
      { method: isSaved ? "DELETE" : "POST" }
    );
    if (response.ok) {
      if (isSaved) {
        savedCompetitionIds.delete(competitionId);
      } else {
        savedCompetitionIds.add(competitionId);
      }
    }
    applySavedButtonState(button, savedCompetitionIds.has(competitionId));
    updateSavedCount();
    if (!savedSection.hidden) {
      const refreshResponse = await fetch("/account/saved");
      if (refreshResponse.ok) {
        const refreshed = await refreshResponse.json();
        syncSavedState(refreshed);
        renderSaved(refreshed.saved, refreshed.programs || [], refreshed.competitions || []);
      }
    }
  } catch (err) {
    console.error(err);
  } finally {
    button.disabled = false;
  }
}

async function toggleSaved(scholarshipId, button) {
  if (!currentUser) {
    openAuthModal("login", "Log in to save scholarships to your account.");
    return;
  }

  const isSaved = savedIds.has(scholarshipId);
  button.disabled = true;
  try {
    if (isSaved) {
      const response = await fetch(`/account/saved/${encodeURIComponent(scholarshipId)}`, {
        method: "DELETE",
      });
      if (response.ok) {
        savedIds.delete(scholarshipId);
      }
    } else {
      const response = await fetch(`/account/saved/${encodeURIComponent(scholarshipId)}`, {
        method: "POST",
      });
      if (response.ok) {
        savedIds.add(scholarshipId);
      }
    }
    applySavedButtonState(button, savedIds.has(scholarshipId));
    updateSavedCount();
    if (!savedSection.hidden) {
      const refreshResponse = await fetch("/account/saved");
      if (refreshResponse.ok) {
        const refreshed = await refreshResponse.json();
        syncSavedState(refreshed);
        renderSaved(refreshed.saved, refreshed.programs || [], refreshed.competitions || []);
      }
    }
  } catch (err) {
    console.error(err);
  } finally {
    button.disabled = false;
  }
}

async function toggleSavedProgram(programId, button) {
  if (!currentUser) {
    openAuthModal("login", "Log in to save summer programs to your account.");
    return;
  }

  const isSaved = savedProgramIds.has(programId);
  button.disabled = true;
  try {
    if (isSaved) {
      const response = await fetch(`/account/saved/programs/${encodeURIComponent(programId)}`, {
        method: "DELETE",
      });
      if (response.ok) {
        savedProgramIds.delete(programId);
      }
    } else {
      const response = await fetch(`/account/saved/programs/${encodeURIComponent(programId)}`, {
        method: "POST",
      });
      if (response.ok) {
        savedProgramIds.add(programId);
      }
    }
    applySavedButtonState(button, savedProgramIds.has(programId));
    updateSavedCount();
    if (!savedSection.hidden) {
      const refreshResponse = await fetch("/account/saved");
      if (refreshResponse.ok) {
        const refreshed = await refreshResponse.json();
        syncSavedState(refreshed);
        renderSaved(refreshed.saved, refreshed.programs || [], refreshed.competitions || []);
      }
    }
  } catch (err) {
    console.error(err);
  } finally {
    button.disabled = false;
  }
}

function applySavedButtonState(button, isSaved) {
  button.classList.toggle("is-saved", isSaved);
  button.textContent = isSaved ? "Saved" : "Save";
}

/* ---------- Preview funnel (3 questions -> 3 teaser matches) ---------- */

function wirePreviewForm() {
  const form = document.getElementById("preview-form");
  if (!form) {
    return;
  }
  form.addEventListener("submit", handlePreviewSubmit);
  document.getElementById("preview-complete-btn")?.addEventListener("click", prefillFromPreview);
  document.getElementById("preview-account-pitch-btn")?.addEventListener("click", () => openAuthModal("signup"));
}

function updatePreviewAccountPitch() {
  const pitch = document.getElementById("preview-account-pitch");
  if (!pitch) {
    return;
  }
  const resultsVisible = !document.getElementById("preview-results")?.hidden;
  pitch.hidden = !resultsVisible || currentUser !== null;
}

function showPreviewError(message) {
  const el = document.getElementById("preview-error");
  el.textContent = message;
  el.hidden = false;
}

async function handlePreviewSubmit(event) {
  event.preventDefault();
  const errorEl = document.getElementById("preview-error");
  errorEl.hidden = true;

  const gpa = parseFloat(document.getElementById("preview-gpa").value);
  const gradeLevel = document.getElementById("preview-grade").value;
  const field = document.getElementById("preview-field").value;
  if (Number.isNaN(gpa) || gpa < 0 || gpa > 4) {
    showPreviewError("Enter your GPA on a 4.0 scale.");
    return;
  }
  if (!gradeLevel || !field) {
    showPreviewError("Pick your grade level and main academic interest.");
    return;
  }

  const submit = document.getElementById("preview-submit");
  submit.disabled = true;
  try {
    const response = await fetch("/match/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gpa, grade_level: gradeLevel, intended_majors: [field] }),
    });
    if (!response.ok) {
      showPreviewError("The preview did not go through. Check your entries and try again.");
      return;
    }
    renderPreviewResults(await response.json());
  } catch (err) {
    showPreviewError("The preview did not go through. Check your connection and try again.");
    console.error(err);
  } finally {
    submit.disabled = false;
  }
}

function renderPreviewResults(data) {
  const wrap = document.getElementById("preview-results");
  const cards = document.getElementById("preview-cards");
  const total = document.getElementById("preview-total");
  cards.innerHTML = "";

  if (!data.results.length) {
    showPreviewError(
      "No preview matches for those three answers. Try another interest, or build the full profile for the complete search."
    );
    wrap.hidden = true;
    updatePreviewAccountPitch();
    return;
  }

  for (const result of data.results) {
    cards.appendChild(buildPreviewCard(result));
  }
  const remaining = data.total_matches - data.results.length;
  total.textContent =
    remaining > 0
      ? `${data.total_matches} scholarships match those three answers. Finish your profile to see the other ${remaining} with citizenship and state checks applied.`
      : "Finish your profile to confirm eligibility and add summer programs and competitions.";
  wrap.hidden = false;
  updatePreviewAccountPitch();
  wrap.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function buildPreviewCard(result) {
  const card = document.createElement("article");
  card.className = "preview-card";

  const title = document.createElement("h3");
  title.textContent = result.scholarship_name;
  card.appendChild(title);

  const sponsor = document.createElement("p");
  sponsor.className = "preview-card-sponsor";
  sponsor.textContent = result.sponsor;
  card.appendChild(sponsor);

  const award = document.createElement("p");
  award.className = "preview-card-award";
  award.textContent = formatAward(result.award_amount);
  card.appendChild(award);

  const reason = (result.match_reasons || []).find(
    (r) => r.startsWith("Field of study overlap") || r.startsWith("Open to all fields")
  );
  if (reason) {
    const why = document.createElement("p");
    why.className = "preview-card-reason";
    why.textContent = reason;
    card.appendChild(why);
  }
  return card;
}

function prefillFromPreview() {
  const gpa = document.getElementById("preview-gpa").value;
  const gradeLevel = document.getElementById("preview-grade").value;
  const field = document.getElementById("preview-field").value;

  if (gpa) {
    document.getElementById("gpa").value = gpa;
  }
  if (gradeLevel) {
    const gradeSelect = document.getElementById("grade-level");
    gradeSelect.value = gradeLevel;
    gradeSelect.dispatchEvent(new Event("change", { bubbles: true }));
  }
  if (field) {
    for (const box of document.querySelectorAll('#fields-of-study input[type="checkbox"]')) {
      if (box.value === field && !box.checked) {
        box.checked = true;
        box.dispatchEvent(new Event("change", { bubbles: true }));
      }
    }
  }
  // The preview already answered step 1, so land the student on eligibility.
  goToFormStep(2);
  document.getElementById("profile-form").scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ---------- Multi-step profile form ---------- */

let currentFormStep = 1;
const FORM_STEP_COUNT = 3;

function wireFormSteps() {
  const next = document.getElementById("step-next-btn");
  const back = document.getElementById("step-back-btn");
  if (!next || !back) {
    return;
  }
  next.addEventListener("click", () => {
    const problems = validateFormStep(currentFormStep);
    if (problems.length > 0) {
      showFormStepError(problems);
      return;
    }
    goToFormStep(currentFormStep + 1);
  });
  back.addEventListener("click", () => goToFormStep(currentFormStep - 1));
  // The submit button is hidden on steps 1-2 but stays the form's default
  // button, so Enter in a field would implicitly submit and bypass the
  // per-step validation. Route it through the same "Next" path instead.
  form.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" || currentFormStep >= FORM_STEP_COUNT) {
      return;
    }
    if (event.target instanceof HTMLTextAreaElement) {
      return;
    }
    event.preventDefault();
    next.click();
  });
  for (const tab of document.querySelectorAll(".form-step-tab")) {
    tab.addEventListener("click", () => {
      const target = Number(tab.dataset.step);
      // Moving forward still validates each intermediate step.
      while (currentFormStep < target) {
        const problems = validateFormStep(currentFormStep);
        if (problems.length > 0) {
          showFormStepError(problems);
          return;
        }
        goToFormStep(currentFormStep + 1);
      }
      if (target < currentFormStep) {
        goToFormStep(target);
      }
    });
  }
}

function validateFormStep(step) {
  const problems = [];
  if (step === 1) {
    const gpa = parseFloat(document.getElementById("gpa").value);
    if (Number.isNaN(gpa) || gpa < 0 || gpa > 4) {
      problems.push("Enter your GPA on a 4.0 scale.");
    }
    if (!document.getElementById("grade-level").value) {
      problems.push("Select your grade level.");
    }
  } else if (step === 2) {
    if (!document.getElementById("citizenship").value) {
      problems.push("Select your citizenship status.");
    }
    if (!document.getElementById("state").value) {
      problems.push("Select your state.");
    }
    if (!document.getElementById("financial-need").value) {
      problems.push("Select your financial need level.");
    }
  }
  return problems;
}

function showFormStepError(problems) {
  const el = document.getElementById("form-step-error");
  el.replaceChildren();
  const intro = document.createElement("strong");
  intro.textContent = "Before continuing:";
  el.appendChild(intro);
  const list = document.createElement("ul");
  for (const problem of problems) {
    const li = document.createElement("li");
    li.textContent = problem;
    list.appendChild(li);
  }
  el.appendChild(list);
  el.hidden = false;
}

function goToFormStep(step) {
  currentFormStep = Math.min(Math.max(step, 1), FORM_STEP_COUNT);
  document.getElementById("form-step-error").hidden = true;
  for (const panel of document.querySelectorAll(".form-step")) {
    panel.hidden = Number(panel.dataset.step) !== currentFormStep;
  }
  for (const tab of document.querySelectorAll(".form-step-tab")) {
    const tabStep = Number(tab.dataset.step);
    tab.classList.toggle("is-current", tabStep === currentFormStep);
    tab.classList.toggle("is-done", tabStep < currentFormStep);
    if (tabStep === currentFormStep) {
      tab.setAttribute("aria-current", "step");
    } else {
      tab.removeAttribute("aria-current");
    }
  }
  document.getElementById("step-back-btn").hidden = currentFormStep === 1;
  document.getElementById("step-next-btn").hidden = currentFormStep === FORM_STEP_COUNT;
  document.getElementById("submit-btn").hidden = currentFormStep !== FORM_STEP_COUNT;
}

/* ---------- Form population (existing) ---------- */

function populateForm(vocab) {
  fillSelect("grade-level", vocab.grade_level);
  fillSelect("citizenship", vocab.citizenship);
  fillSelect("state", vocab.state);
  fillSelect("financial-need", vocab.financial_need_level);
  fillCheckboxes("fields-of-study", vocab.fields_of_study, "fields");
  fillCheckboxes("demographic-tags", vocab.demographic_tags, "demographics");
  fillSelect("preview-grade", vocab.grade_level);
  fillSelect("preview-field", vocab.fields_of_study);
  fillSelect("catalog-field", vocab.fields_of_study);
  applyProfileHelp();
}

function fillSelect(elementId, options) {
  const select = document.getElementById(elementId);
  const placeholderText = select.options[0]?.textContent || "Select...";
  select.replaceChildren();

  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = placeholderText;
  select.appendChild(placeholder);

  for (const opt of options) {
    const option = document.createElement("option");
    option.value = opt.value;
    option.textContent = opt.label;
    const helpText = selectOptionHelp(elementId, opt);
    if (helpText) {
      option.title = helpText;
    }
    select.appendChild(option);
  }
}

function fillCheckboxes(containerId, options, namePrefix) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  for (const opt of options) {
    const label = document.createElement("label");
    label.className = "checkbox-item";

    const input = document.createElement("input");
    input.type = "checkbox";
    input.name = namePrefix;
    input.value = opt.value;

    const helpText = checkboxOptionHelp(namePrefix, opt);
    if (helpText) {
      label.classList.add("has-tooltip", "option-tooltip");
      label.dataset.tooltip = helpText;
    }

    label.appendChild(input);
    label.appendChild(document.createTextNode(opt.label));
    container.appendChild(label);
  }
}

function applyProfileHelp() {
  for (const [id, helpText] of Object.entries(CRITERIA_HELP)) {
    const element = document.getElementById(id);
    const target = element?.closest(".field") || element;
    addTooltip(target, helpText);
  }
}

function addTooltip(target, helpText) {
  if (!target || !helpText) {
    return;
  }
  const label = target.querySelector("label, legend");
  const tooltipTarget = label || target;
  tooltipTarget.classList.add("has-tooltip");
  tooltipTarget.dataset.tooltip = helpText;

  if (label && !label.querySelector(".help-dot")) {
    const dot = document.createElement("span");
    dot.className = "help-dot";
    dot.textContent = "?";
    dot.title = helpText;
    dot.setAttribute("aria-hidden", "true");
    label.appendChild(dot);
  }
}

function checkboxOptionHelp(namePrefix, option) {
  if (namePrefix === "fields") {
    return `${option.label} creates field-fit points only when a scholarship lists this area or a broader approved parent area. Narrow requirements like computer science need that exact field selected.`;
  }
  if (namePrefix === "demographics") {
    return `${option.label} is used only as a positive signal for scholarships that mention this group. It never hides scholarships from you.`;
  }
  return "";
}

function selectOptionHelp(elementId, option) {
  if (elementId === "financial-need") {
    return `${option.label} financial need affects ranking only for scholarships that publish a need-based preference or requirement.`;
  }
  if (elementId === "grade-level") {
    return `${option.label} is used to screen out awards limited to other school levels. Broad sponsor rules are matched automatically.`;
  }
  if (elementId === "citizenship") {
    return `${option.label} is compared with published citizenship rules when those rules are verified.`;
  }
  if (elementId === "state") {
    return `${option.label} is compared with state-specific eligibility when a scholarship is not national.`;
  }
  return "";
}

function parseCommaList(value) {
  if (!value || !value.trim()) {
    return null;
  }
  return value
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function getCheckedValues(containerId) {
  const container = document.getElementById(containerId);
  return Array.from(container.querySelectorAll("input:checked")).map(
    (input) => input.value
  );
}

function buildProfile() {
  const gpa = parseFloat(document.getElementById("gpa").value);
  const gradeLevel = document.getElementById("grade-level").value;
  const citizenship = document.getElementById("citizenship").value;
  const state = document.getElementById("state").value;
  const financialNeed = document.getElementById("financial-need").value;
  const intendedMajors = getCheckedValues("fields-of-study");
  const demographicTags = getCheckedValues("demographic-tags");
  const targetSchools = parseCommaList(
    document.getElementById("target-schools").value
  );
  const activities = parseCommaList(document.getElementById("activities").value);

  if (Number.isNaN(gpa)) {
    return { error: "Enter a GPA between 0.0 and 4.0." };
  }
  if (!gradeLevel) {
    return { error: "Select your grade level." };
  }
  if (!citizenship) {
    return { error: "Select your citizenship status." };
  }
  if (!state) {
    return { error: "Select your state." };
  }
  if (!financialNeed) {
    return { error: "Select a financial need level." };
  }
  if (intendedMajors.length === 0) {
    return { error: "Select at least one field of study." };
  }

  const profile = {
    gpa,
    grade_level: gradeLevel,
    citizenship,
    state,
    financial_need_level: financialNeed,
    intended_majors: intendedMajors,
    demographic_tags: demographicTags,
    activities: activities || [],
  };

  if (targetSchools) {
    profile.target_schools = targetSchools;
  }

  return { profile };
}

function formatValidationErrors(detail) {
  if (!Array.isArray(detail)) {
    return "The profile could not be submitted. Check your entries and try again.";
  }

  const messages = detail.map((item) => {
    const field = item.loc ? item.loc[item.loc.length - 1] : "field";
    const label = fieldLabel(String(field));
    return `${label}: ${item.msg}`;
  });

  return messages.join(" ");
}

function fieldLabel(field) {
  const labels = {
    gpa: "GPA",
    grade_level: "Grade level",
    citizenship: "Citizenship",
    state: "State",
    financial_need_level: "Financial need level",
    intended_majors: "Fields of study",
    demographic_tags: "Demographic tags",
    target_schools: "Target schools",
    activities: "Activities",
  };
  return labels[field] || field.replace(/_/g, " ");
}

function extractError(data, fallback) {
  if (!data) {
    return fallback;
  }
  if (data.detail) {
    if (typeof data.detail === "string") {
      return data.detail;
    }
    if (data.detail.error) {
      return data.detail.error;
    }
    if (Array.isArray(data.detail)) {
      return formatValidationErrors(data.detail);
    }
  }
  return fallback;
}

function showFormError(message) {
  formError.textContent = message;
  formError.hidden = false;
}

function hideFormError() {
  formError.hidden = true;
  formError.textContent = "";
}

function setLoading(isLoading) {
  loadingEl.hidden = !isLoading;
  submitBtn.disabled = isLoading;
  if (isLoading) {
    resultsContainer.innerHTML = "";
    resultsEmpty.hidden = true;
    resultsFilters.hidden = true;
    programsContainer.innerHTML = "";
    programsEmpty.hidden = true;
    programsSearchPanel.hidden = true;
    lastPrograms = null;
    competitionsContainer.innerHTML = "";
    competitionsEmpty.hidden = true;
    competitionsSearchPanel.hidden = true;
    lastCompetitions = null;
    lastNearMisses.scholarships = [];
    lastNearMisses.programs = [];
    lastNearMisses.competitions = [];
    resetAllLaneWindows();
    resetQuickAppliesWindow();
    updateOpportunityTabCounts();
  }
}

async function runMatchFlow(profile) {
  const response = await fetch("/match", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (response.status === 422) {
    const data = await response.json();
    const err = new Error("validation");
    err.validationDetail = data.detail;
    throw err;
  }
  if (!response.ok) {
    throw new Error(`Match request failed (${response.status})`);
  }
  const payload = await response.json();
  lastSubmittedProfile = profile;
  lastResults = payload.matches;
  lastNearMisses.scholarships = payload.near_misses || [];
  renderResults(lastResults);
  updateOpportunityTabCounts();
  await activateOpportunityView("scholarships");
  loadPrograms(profile);
  loadCompetitions(profile);
}

async function handleSubmit(event) {
  event.preventDefault();
  hideFormError();

  const built = buildProfile();
  if (built.error) {
    showFormError(built.error);
    return;
  }

  resultsSection.hidden = false;
  programsSection.hidden = true;
  competitionsSection.hidden = true;
  savedSection.hidden = true;
  setOpportunityTabsVisible(false);
  setLoading(true);

  try {
    await runMatchFlow(built.profile);
    saveProfileSilently(built.profile);
  } catch (err) {
    if (err.validationDetail) {
      showFormError(formatValidationErrors(err.validationDetail));
    } else {
      showFormError(
        "The match request did not go through. Check your connection and try again."
      );
      console.error(err);
    }
  } finally {
    setLoading(false);
  }
}

async function autoMatchFromSavedProfile() {
  if (!currentUser || lastResults) {
    return;
  }
  const built = buildProfile();
  if (built.error) {
    return; // incomplete saved profile: keep today's behavior silently
  }
  // "Pre-match state" differs when login happens from an open view (catalog,
  // saved list): snapshot what was visible so a failed match can put it back
  // instead of stranding the user with no tab bar.
  const prior = {
    results: resultsSection.hidden,
    programs: programsSection.hidden,
    competitions: competitionsSection.hidden,
    saved: savedSection.hidden,
    catalog: catalogSection.hidden,
    tabs: opportunityTabs ? opportunityTabs.hidden : true,
  };
  resultsSection.hidden = false;
  programsSection.hidden = true;
  competitionsSection.hidden = true;
  savedSection.hidden = true;
  catalogSection.hidden = true;
  setOpportunityTabsVisible(false);
  setLoading(true);
  try {
    await runMatchFlow(built.profile);
  } catch (err) {
    console.error(err);
    resultsSection.hidden = prior.results; // degrade to pre-match state, no toast
    programsSection.hidden = prior.programs;
    competitionsSection.hidden = prior.competitions;
    savedSection.hidden = prior.saved;
    catalogSection.hidden = prior.catalog;
    setOpportunityTabsVisible(!prior.tabs);
  } finally {
    setLoading(false);
  }
}

function renderResults(results) {
  resultsContainer.innerHTML = "";
  renderQuickApplies();

  if (results.length === 0) {
    resultsSummary.textContent = "";
    resultsFilters.hidden = true;
    resultsEmpty.hidden = false;
    if (lastNearMisses.scholarships.length > 0) {
      resultsContainer.appendChild(
        buildNearMissGroup("scholarships", lastNearMisses.scholarships)
      );
    }
    return;
  }

  resultsFilters.hidden = false;

  const filtered = sortResults(applyResultFilters(results));

  if (filtered.length === 0) {
    resultsEmpty.hidden = true;
    resultsSummary.textContent = `0 of ${results.length} matches shown with the current filters.`;
    if (scholarshipSearchQuery) {
      resultsContainer.appendChild(noResultsMessage(scholarshipSearchQuery, "scholarship"));
    } else {
      const note = document.createElement("div");
      note.className = "results-empty panel";
      note.innerHTML =
        "<h3>No matches with these filters</h3><p>Loosen a filter or use <strong>Clear filters</strong> to see all matches again.</p>";
      resultsContainer.appendChild(note);
    }
    if (lastNearMisses.scholarships.length > 0) {
      resultsContainer.appendChild(
        buildNearMissGroup("scholarships", lastNearMisses.scholarships)
      );
    }
    return;
  }

  resultsEmpty.hidden = true;
  const visible = filtered.slice(0, laneVisibleCounts.scholarships);
  const regular = visible.filter((r) => !r.requires_special_check);
  const special = visible.filter((r) => r.requires_special_check);
  const strong = regular.filter((r) => r.match_tier === "strong");
  const possible = regular.filter((r) => r.match_tier === "possible");

  const shownAll = filtered.length === results.length && visible.length === filtered.length;
  resultsSummary.textContent = shownAll
    ? `${results.length} scholarship${results.length === 1 ? "" : "s"} matched your profile.`
    : visible.length === filtered.length
    ? `Showing ${filtered.length} of ${results.length} matched scholarships.`
    : `Showing ${visible.length} of ${filtered.length} matched scholarships.`;

  if (strong.length > 0) {
    resultsContainer.appendChild(buildTierSection("Strong matches", strong, "strong"));
  }
  if (possible.length > 0) {
    resultsContainer.appendChild(
      buildTierSection("Possible matches", possible, "possible")
    );
  }
  if (special.length > 0) {
    resultsContainer.appendChild(
      buildTierSection(
        "Special opportunities to check",
        special,
        "special",
        "These may be worthwhile, but they require a niche condition like a nomination, membership, finalist status, or affiliation that this profile cannot verify yet."
      )
    );
  }
  if (filtered.length > laneVisibleCounts.scholarships) {
    resultsContainer.appendChild(
      buildLaneShowMoreButton("scholarships", filtered.length - laneVisibleCounts.scholarships)
    );
  }
  if (lastNearMisses.scholarships.length > 0) {
    resultsContainer.appendChild(
      buildNearMissGroup("scholarships", lastNearMisses.scholarships)
    );
  }
}

function buildTierSection(title, matches, tierClass, description = "") {
  const section = document.createElement("div");
  section.className = "tier-section";

  const heading = document.createElement("h3");
  heading.className = `tier-heading ${
    tierClass === "possible" || tierClass === "special" ? tierClass : ""
  }`;
  heading.innerHTML = `${escapeHtml(title)} <span class="tier-count">${matches.length}</span>`;
  section.appendChild(heading);

  if (description) {
    const note = document.createElement("p");
    note.className = "tier-note";
    note.textContent = description;
    section.appendChild(note);
  }

  for (const [index, match] of matches.entries()) {
    const card = buildCard(matchToCard(match), tierClass);
    card.classList.add("match-card-enter");
    card.style.setProperty("--card-delay", `${Math.min(index * 42, 252)}ms`);
    section.appendChild(card);
  }

  return section;
}

/* ---------- Summer programs ---------- */

async function loadPrograms(profile) {
  try {
    const response = await fetch("/programs/match", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    if (!response.ok) {
      lastPrograms = [];
      lastNearMisses.programs = [];
      updateOpportunityTabCounts();
      return;
    }
    const payload = await response.json();
    const programs = payload.matches;
    lastPrograms = programs;
    lastNearMisses.programs = payload.near_misses || [];
    updateOpportunityTabCounts();
    renderPrograms(programs);
    if (activeOpportunityView === "programs") {
      programsSection.hidden = false;
    }
  } catch (err) {
    lastPrograms = [];
    lastNearMisses.programs = [];
    updateOpportunityTabCounts();
    console.error(err);
  }
}

function renderPrograms(programs) {
  programsContainer.innerHTML = "";
  lastPrograms = programs;
  updateOpportunityTabCounts();
  renderQuickApplies();

  if (programs.length === 0) {
    programsSummary.textContent = "";
    programsSearchPanel.hidden = true;
    programsEmpty.hidden = false;
    if (lastNearMisses.programs.length > 0) {
      programsContainer.appendChild(buildNearMissGroup("programs", lastNearMisses.programs));
    }
    return;
  }

  programsSearchPanel.hidden = false;
  programsEmpty.hidden = true;

  const filtered = sortPrograms(applyProgramFilters(programs));
  if (filtered.length === 0) {
    programsSummary.textContent = `0 of ${programs.length} matched programs shown.`;
    programsEmpty.hidden = true;
    if (programSearchQuery) {
      programsContainer.appendChild(noResultsMessage(programSearchQuery, "summer program"));
    } else {
      const note = document.createElement("div");
      note.className = "results-empty panel";
      note.innerHTML =
        "<h3>No matches with these filters</h3><p>Loosen a filter or use <strong>Clear filters</strong> to see all matches again.</p>";
      programsContainer.appendChild(note);
    }
    if (lastNearMisses.programs.length > 0) {
      programsContainer.appendChild(buildNearMissGroup("programs", lastNearMisses.programs));
    }
    return;
  }

  const visible = filtered.slice(0, laneVisibleCounts.programs);
  const regular = visible.filter((p) => !p.requires_special_check);
  const special = visible.filter((p) => p.requires_special_check);
  const strong = regular.filter((p) => p.match_tier === "strong");
  const possible = regular.filter((p) => p.match_tier === "possible");
  const shownAll = filtered.length === programs.length && visible.length === filtered.length;
  programsSummary.textContent = shownAll
    ? `${programs.length} program${programs.length === 1 ? "" : "s"} matched your profile.`
    : visible.length === filtered.length
    ? `Showing ${filtered.length} of ${programs.length} matched programs.`
    : `Showing ${visible.length} of ${filtered.length} matched programs.`;

  if (strong.length > 0) {
    programsContainer.appendChild(buildProgramTierSection("Strong fits", strong, "strong"));
  }
  if (possible.length > 0) {
    programsContainer.appendChild(
      buildProgramTierSection("Possible fits", possible, "possible")
    );
  }
  if (special.length > 0) {
    programsContainer.appendChild(
      buildProgramTierSection(
        "Special programs to check",
        special,
        "special",
        "These programs may fit, but they require a condition like school nomination, a special application channel, or another gate this profile cannot verify yet."
      )
    );
  }
  if (filtered.length > laneVisibleCounts.programs) {
    programsContainer.appendChild(
      buildLaneShowMoreButton("programs", filtered.length - laneVisibleCounts.programs)
    );
  }
  if (lastNearMisses.programs.length > 0) {
    programsContainer.appendChild(buildNearMissGroup("programs", lastNearMisses.programs));
  }
}

async function loadCompetitions(profile) {
  try {
    const response = await fetch("/competitions/match", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    if (!response.ok) {
      lastCompetitions = [];
      lastNearMisses.competitions = [];
      updateOpportunityTabCounts();
      return;
    }
    const payload = await response.json();
    const competitions = payload.matches;
    lastCompetitions = competitions;
    lastNearMisses.competitions = payload.near_misses || [];
    updateOpportunityTabCounts();
    renderCompetitions(competitions);
    if (activeOpportunityView === "competitions") {
      competitionsSection.hidden = false;
    }
  } catch (err) {
    lastCompetitions = [];
    lastNearMisses.competitions = [];
    updateOpportunityTabCounts();
    console.error(err);
  }
}

function renderCompetitions(competitions) {
  competitionsContainer.innerHTML = "";
  lastCompetitions = competitions;
  updateOpportunityTabCounts();
  renderQuickApplies();

  if (competitions.length === 0) {
    competitionsSummary.textContent = "";
    competitionsSearchPanel.hidden = true;
    competitionsEmpty.hidden = false;
    if (lastNearMisses.competitions.length > 0) {
      competitionsContainer.appendChild(
        buildNearMissGroup("competitions", lastNearMisses.competitions)
      );
    }
    return;
  }

  competitionsSearchPanel.hidden = false;
  competitionsEmpty.hidden = true;

  const filtered = sortCompetitions(applyCompetitionFilters(competitions));
  if (filtered.length === 0) {
    competitionsSummary.textContent = `0 of ${competitions.length} matched competitions shown.`;
    competitionsEmpty.hidden = true;
    if (competitionSearchQuery) {
      competitionsContainer.appendChild(noResultsMessage(competitionSearchQuery, "competition"));
    } else {
      const note = document.createElement("div");
      note.className = "results-empty panel";
      note.innerHTML =
        "<h3>No matches with these filters</h3><p>Loosen a filter or use <strong>Clear filters</strong> to see all matches again.</p>";
      competitionsContainer.appendChild(note);
    }
    if (lastNearMisses.competitions.length > 0) {
      competitionsContainer.appendChild(
        buildNearMissGroup("competitions", lastNearMisses.competitions)
      );
    }
    return;
  }

  const visible = filtered.slice(0, laneVisibleCounts.competitions);
  const regular = visible.filter((c) => !c.requires_special_check);
  const special = visible.filter((c) => c.requires_special_check);
  const strong = regular.filter((c) => c.match_tier === "strong");
  const possible = regular.filter((c) => c.match_tier === "possible");
  const shownAll = filtered.length === competitions.length && visible.length === filtered.length;
  competitionsSummary.textContent = shownAll
    ? `${competitions.length} competition${competitions.length === 1 ? "" : "s"} matched your profile.`
    : visible.length === filtered.length
    ? `Showing ${filtered.length} of ${competitions.length} matched competitions.`
    : `Showing ${visible.length} of ${filtered.length} matched competitions.`;

  if (strong.length > 0) {
    competitionsContainer.appendChild(
      buildCompetitionTierSection("Strong fits", strong, "strong")
    );
  }
  if (possible.length > 0) {
    competitionsContainer.appendChild(
      buildCompetitionTierSection("Possible fits", possible, "possible")
    );
  }
  if (special.length > 0) {
    competitionsContainer.appendChild(
      buildCompetitionTierSection(
        "Special competitions to check",
        special,
        "special",
        "These competitions may fit, but they require a condition like school nomination, membership, or another gate this profile cannot verify yet."
      )
    );
  }
  if (filtered.length > laneVisibleCounts.competitions) {
    competitionsContainer.appendChild(
      buildLaneShowMoreButton("competitions", filtered.length - laneVisibleCounts.competitions)
    );
  }
  if (lastNearMisses.competitions.length > 0) {
    competitionsContainer.appendChild(
      buildNearMissGroup("competitions", lastNearMisses.competitions)
    );
  }
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url} request failed (${response.status})`);
  }
  return response.json();
}

async function ensureCatalogData(kinds = ["scholarships", "programs", "competitions"]) {
  const requests = [];
  if (kinds.includes("scholarships") && catalogScholarships === null) {
    if (!catalogScholarshipsPromise) {
      catalogScholarshipsPromise = fetchJson("/scholarships")
        .then((scholarships) => {
          catalogScholarships = scholarships;
          updateOpportunityTabCounts();
        })
        .finally(() => {
          catalogScholarshipsPromise = null;
        });
    }
    requests.push(catalogScholarshipsPromise);
  }
  if (kinds.includes("programs") && catalogPrograms === null) {
    if (!catalogProgramsPromise) {
      catalogProgramsPromise = fetchJson("/programs")
        .then((programs) => {
          catalogPrograms = programs;
          updateOpportunityTabCounts();
        })
        .finally(() => {
          catalogProgramsPromise = null;
        });
    }
    requests.push(catalogProgramsPromise);
  }
  if (kinds.includes("competitions") && catalogCompetitions === null) {
    if (!catalogCompetitionsPromise) {
      catalogCompetitionsPromise = fetchJson("/competitions")
        .then((competitions) => {
          catalogCompetitions = competitions;
          updateOpportunityTabCounts();
        })
        .finally(() => {
          catalogCompetitionsPromise = null;
        });
    }
    requests.push(catalogCompetitionsPromise);
  }
  await Promise.all(requests);
}

async function showCatalogView() {
  catalogSection.hidden = false;
  if (catalogScholarships === null || catalogPrograms === null || catalogCompetitions === null) {
    catalogSummary.textContent = "Loading the full catalog...";
    catalogEmpty.hidden = true;
    catalogContainer.innerHTML = "";
    try {
      await ensureCatalogData();
    } catch (err) {
      catalogSummary.textContent = "The catalog could not be loaded.";
      catalogEmpty.hidden = false;
      catalogContainer.innerHTML = "";
      console.error(err);
      return;
    }
  }
  renderCatalog();
}

function wireCatalogFilters() {
  catalogField?.addEventListener("change", () => {
    catalogFieldFilter = catalogField.value;
    resetCatalogWindow();
    renderCatalog();
  });
  catalogSortSelect?.addEventListener("change", () => {
    catalogSort = catalogSortSelect.value;
    resetCatalogWindow();
    renderCatalog();
  });
  catalogNoEssayCheck?.addEventListener("change", () => {
    catalogNoEssay = catalogNoEssayCheck.checked;
    resetCatalogWindow();
    renderCatalog();
  });
  catalogVerifiedOnlyCheck?.addEventListener("change", () => {
    catalogVerifiedOnly = catalogVerifiedOnlyCheck.checked;
    resetCatalogWindow();
    renderCatalog();
  });
  catalogClear?.addEventListener("click", resetCatalogFilters);
}

function resetCatalogFilters() {
  catalogFieldFilter = "";
  catalogSort = "name";
  catalogNoEssay = false;
  catalogVerifiedOnly = false;
  catalogSearchQuery = "";
  if (catalogField) catalogField.value = "";
  if (catalogSortSelect) catalogSortSelect.value = "name";
  if (catalogNoEssayCheck) catalogNoEssayCheck.checked = false;
  if (catalogVerifiedOnlyCheck) catalogVerifiedOnlyCheck.checked = false;
  if (catalogSearch) catalogSearch.value = "";
  resetCatalogWindow();
  renderCatalog();
}

// Catalog items are raw dataset records (scholarship / program / competition),
// all of which carry name, eligibility, verified, deadline, estimated_deadline.
function catalogItemFields(item) {
  return (item.eligibility && item.eligibility.fields_of_study) || [];
}

function catalogItemPassesFilters(item) {
  if (catalogFieldFilter) {
    // As a discovery filter, "Field of study" surfaces entries that target that
    // field. Open-to-all entries (no listed fields) stay under "All fields" so
    // picking a field actually narrows the list.
    if (!catalogItemFields(item).includes(catalogFieldFilter)) {
      return false;
    }
  }
  if (catalogNoEssay && item.eligibility && item.eligibility.essay_required) {
    return false;
  }
  if (catalogVerifiedOnly && item.verified !== true) {
    return false;
  }
  return true;
}

function catalogAwardValue(item) {
  return typeof item.award_amount === "number" ? item.award_amount : -1;
}

function catalogDeadlineValue(item) {
  const parsed = parseRealDeadline(item.deadline);
  // Unknown/rolling deadlines sort last so the soonest real dates lead.
  return parsed ? parsed.getTime() : Number.POSITIVE_INFINITY;
}

function sortCatalogItems(items) {
  const arr = [...items];
  const byName = (a, b) => String(a.name || "").localeCompare(String(b.name || ""));
  if (catalogSort === "award") {
    arr.sort((a, b) => catalogAwardValue(b) - catalogAwardValue(a) || byName(a, b));
  } else if (catalogSort === "deadline") {
    arr.sort((a, b) => catalogDeadlineValue(a) - catalogDeadlineValue(b) || byName(a, b));
  } else {
    arr.sort(byName);
  }
  return arr;
}

function catalogFiltersActive() {
  return Boolean(
    catalogSearchQuery || catalogFieldFilter || catalogNoEssay || catalogVerifiedOnly
  );
}

function updateCatalogKindCounts() {
  const counts = {
    scholarships: catalogScholarships ? catalogScholarships.length : null,
    programs: catalogPrograms ? catalogPrograms.length : null,
    competitions: catalogCompetitions ? catalogCompetitions.length : null,
  };
  const all =
    counts.scholarships !== null && counts.programs !== null && counts.competitions !== null
      ? counts.scholarships + counts.programs + counts.competitions
      : null;
  const set = (kind, value) => {
    const el = document.getElementById(`catalog-kind-count-${kind}`);
    if (el) {
      el.textContent = value === null ? "" : String(value);
    }
  };
  set("all", all);
  set("scholarships", counts.scholarships);
  set("programs", counts.programs);
  set("competitions", counts.competitions);
}

function renderCatalog() {
  catalogContainer.innerHTML = "";
  if (catalogScholarships === null || catalogPrograms === null || catalogCompetitions === null) {
    return;
  }
  updateCatalogKindCounts();
  const wantKind = (kind) => catalogKindFilter === "all" || catalogKindFilter === kind;
  const filterAndSort = (list, searchValuesFn) =>
    sortCatalogItems(
      list.filter(
        (item) =>
          itemMatchesSearch(searchValuesFn(item), catalogSearchQuery) &&
          catalogItemPassesFilters(item)
      )
    );
  const scholarships = !wantKind("scholarships")
    ? []
    : filterAndSort(catalogScholarships, scholarshipSearchValues);
  const programs = !wantKind("programs")
    ? []
    : filterAndSort(catalogPrograms, programSearchValues);
  const competitions = !wantKind("competitions")
    ? []
    : filterAndSort(catalogCompetitions, competitionSearchValues);
  const kindTotal =
    (wantKind("scholarships") ? catalogScholarships.length : 0) +
    (wantKind("programs") ? catalogPrograms.length : 0) +
    (wantKind("competitions") ? catalogCompetitions.length : 0);
  const shown = scholarships.length + programs.length + competitions.length;

  const kindLabel = {
    all: "catalog opportunities",
    scholarships: "scholarships",
    programs: "summer programs",
    competitions: "competitions",
  }[catalogKindFilter];
  // Mirror the lane summaries: the second number is what passed the filters,
  // the first is what the 30-per-kind batching windows actually render.
  const visibleShown =
    Math.min(scholarships.length, catalogVisibleCounts.scholarships) +
    Math.min(programs.length, catalogVisibleCounts.programs) +
    Math.min(competitions.length, catalogVisibleCounts.competitions);
  catalogSummary.textContent = !catalogFiltersActive()
    ? `${kindTotal} ${kindLabel} available to browse.`
    : visibleShown === shown
    ? `Showing ${shown} of ${kindTotal} ${kindLabel}.`
    : `Showing ${visibleShown} of ${shown} filtered ${kindLabel}.`;

  if (shown === 0) {
    catalogEmpty.hidden = true;
    if (catalogSearchQuery) {
      catalogContainer.appendChild(noResultsMessage(catalogSearchQuery, "catalog"));
    } else {
      // Emptiness came from the filter panel, not the search box. The
      // "no results for your search" copy would render a bare `for ""`.
      const note = document.createElement("div");
      note.className = "results-empty panel";
      note.innerHTML =
        "<h3>No catalog results with these filters</h3><p>Loosen a filter or use <strong>Clear filters</strong> to browse the full catalog again.</p>";
      catalogContainer.appendChild(note);
    }
    return;
  }

  catalogEmpty.hidden = true;
  if (scholarships.length > 0) {
    catalogContainer.appendChild(
      buildCatalogScholarshipSection(
        scholarships.slice(0, catalogVisibleCounts.scholarships),
        scholarships.length
      )
    );
    if (scholarships.length > catalogVisibleCounts.scholarships) {
      catalogContainer.appendChild(
        buildShowMoreButton("scholarships", scholarships.length - catalogVisibleCounts.scholarships)
      );
    }
  }
  if (programs.length > 0) {
    catalogContainer.appendChild(
      buildCatalogProgramSection(programs.slice(0, catalogVisibleCounts.programs), programs.length)
    );
    if (programs.length > catalogVisibleCounts.programs) {
      catalogContainer.appendChild(
        buildShowMoreButton("programs", programs.length - catalogVisibleCounts.programs)
      );
    }
  }
  if (competitions.length > 0) {
    catalogContainer.appendChild(
      buildCatalogCompetitionSection(
        competitions.slice(0, catalogVisibleCounts.competitions),
        competitions.length
      )
    );
    if (competitions.length > catalogVisibleCounts.competitions) {
      catalogContainer.appendChild(
        buildShowMoreButton("competitions", competitions.length - catalogVisibleCounts.competitions)
      );
    }
  }
}

function buildCatalogScholarshipSection(scholarships, totalCount) {
  const count = totalCount ?? scholarships.length;
  const section = document.createElement("div");
  section.className = "tier-section";
  const heading = document.createElement("h3");
  heading.className = "tier-heading";
  heading.innerHTML = `All scholarships <span class="tier-count">${count}</span>`;
  section.appendChild(heading);
  for (const [index, scholarship] of scholarships.entries()) {
    const card = scholarshipToCard(scholarship);
    card.catalog_context = true;
    const element = buildCard(card, "catalog");
    element.classList.add("match-card-enter");
    element.style.setProperty("--card-delay", `${Math.min(index * 24, 180)}ms`);
    section.appendChild(element);
  }
  return section;
}

function buildCatalogProgramSection(programs, totalCount) {
  const count = totalCount ?? programs.length;
  const section = document.createElement("div");
  section.className = "tier-section";
  const heading = document.createElement("h3");
  heading.className = "tier-heading";
  heading.innerHTML = `All summer programs <span class="tier-count">${count}</span>`;
  section.appendChild(heading);
  for (const [index, program] of programs.entries()) {
    const element = buildProgramCard(program, { catalogContext: true });
    element.classList.add("match-card-enter");
    element.style.setProperty("--card-delay", `${Math.min(index * 24, 180)}ms`);
    section.appendChild(element);
  }
  return section;
}

function buildCatalogCompetitionSection(competitions, totalCount) {
  const count = totalCount ?? competitions.length;
  const section = document.createElement("div");
  section.className = "tier-section";
  const heading = document.createElement("h3");
  heading.className = "tier-heading";
  heading.innerHTML = `All competitions <span class="tier-count">${count}</span>`;
  section.appendChild(heading);
  for (const [index, competition] of competitions.entries()) {
    const element = buildCompetitionCard(competition, { catalogContext: true });
    element.classList.add("match-card-enter");
    element.style.setProperty("--card-delay", `${Math.min(index * 24, 180)}ms`);
    section.appendChild(element);
  }
  return section;
}

function buildCompetitionTierSection(title, competitions, tierClass, description = "") {
  const section = document.createElement("div");
  section.className = "tier-section";

  const heading = document.createElement("h3");
  heading.className = `tier-heading ${
    tierClass === "possible" || tierClass === "special" ? tierClass : ""
  }`;
  heading.innerHTML = `${escapeHtml(title)} <span class="tier-count">${competitions.length}</span>`;
  section.appendChild(heading);

  if (description) {
    const note = document.createElement("p");
    note.className = "tier-note";
    note.textContent = description;
    section.appendChild(note);
  }

  for (const [index, competition] of competitions.entries()) {
    const element = buildCompetitionCard(competition);
    element.classList.add("match-card-enter");
    element.style.setProperty("--card-delay", `${Math.min(index * 24, 180)}ms`);
    section.appendChild(element);
  }
  return section;
}

function buildProgramTierSection(title, programs, tierClass, description = "") {
  const section = document.createElement("div");
  section.className = "tier-section";

  const heading = document.createElement("h3");
  heading.className = `tier-heading ${
    tierClass === "possible" || tierClass === "special" ? tierClass : ""
  }`;
  heading.innerHTML = `${escapeHtml(title)} <span class="tier-count">${programs.length}</span>`;
  section.appendChild(heading);

  if (description) {
    const note = document.createElement("p");
    note.className = "tier-note";
    note.textContent = description;
    section.appendChild(note);
  }

  programs.forEach((program, index) => {
    const card = buildProgramCard(program);
    card.classList.add("match-card-enter");
    card.style.setProperty("--card-delay", `${Math.min(index * 42, 252)}ms`);
    section.appendChild(card);
  });

  return section;
}

function programStatValue(value) {
  if (!value || value === "VERIFY" || String(value).startsWith("VERIFY")) {
    return "Not listed";
  }
  return value;
}

function buildProgramStatRow(program) {
  const row = document.createElement("div");
  row.className = "card-stats";

  const cost = document.createElement("div");
  cost.className = "stat";
  if (program.cost_category === "free" || program.cost_category === "stipend") {
    cost.classList.add("stat-award");
  }
  cost.innerHTML =
    '<span class="stat-label">Cost</span>' +
    `<span class="stat-value">${escapeHtml(programStatValue(program.cost))}</span>`;
  row.appendChild(cost);

  const selectivity = document.createElement("div");
  selectivity.className = "stat";
  selectivity.innerHTML =
    '<span class="stat-label">Selectivity</span>' +
    `<span class="stat-value">${escapeHtml(programStatValue(program.selectivity))}</span>`;
  row.appendChild(selectivity);

  const dates = document.createElement("div");
  dates.className = "stat";
  dates.innerHTML =
    '<span class="stat-label">Dates</span>' +
    `<span class="stat-value">${escapeHtml(programStatValue(program.program_dates))}</span>`;
  row.appendChild(dates);

  const dl = deadlineParts(program.deadline, program.estimated_deadline);
  const apply = document.createElement("div");
  apply.className = "stat stat-deadline";
  apply.innerHTML =
    '<span class="stat-label">Apply by</span>' +
    `<span class="stat-value">${escapeHtml(dl.value)}</span>` +
    (dl.note ? `<span class="stat-note">${escapeHtml(dl.note)}</span>` : "");
  row.appendChild(apply);

  return row;
}

// A free competition just says "Free" on the card. The dataset keeps the full
// sourcing prose ("Free to enter; no fee, confirmed on the official rules
// page...") because that is our verification evidence, and the opportunity page
// still shows it in full. A card is not the place to read a paragraph.
function competitionCostValue(competition) {
  if (competition.cost_category === "free") {
    return "Free";
  }
  return programStatValue(competition.cost);
}

function buildCompetitionStatRow(competition) {
  const row = document.createElement("div");
  row.className = "card-stats";

  const cost = document.createElement("div");
  cost.className = "stat";
  if (competition.cost_category === "free" || competition.cost_category === "stipend") {
    cost.classList.add("stat-award");
  }
  cost.innerHTML =
    '<span class="stat-label">Cost</span>' +
    `<span class="stat-value">${escapeHtml(competitionCostValue(competition))}</span>`;
  row.appendChild(cost);

  const recognition = document.createElement("div");
  recognition.className = "stat";
  recognition.innerHTML =
    '<span class="stat-label">Recognition</span>' +
    `<span class="stat-value">${escapeHtml(programStatValue(competition.recognition))}</span>`;
  row.appendChild(recognition);

  const dates = document.createElement("div");
  dates.className = "stat";
  dates.innerHTML =
    '<span class="stat-label">Dates</span>' +
    `<span class="stat-value">${escapeHtml(programStatValue(competition.competition_dates))}</span>`;
  row.appendChild(dates);

  const dl = deadlineParts(competition.deadline, competition.estimated_deadline);
  const apply = document.createElement("div");
  apply.className = "stat stat-deadline";
  apply.innerHTML =
    '<span class="stat-label">Register by</span>' +
    `<span class="stat-value">${escapeHtml(dl.value)}</span>` +
    (dl.note ? `<span class="stat-note">${escapeHtml(dl.note)}</span>` : "");
  row.appendChild(apply);

  return row;
}

function makeCardTitle(tag, kindPath, item) {
  const title = document.createElement(tag);
  title.className = "card-title";
  const link = document.createElement("a");
  link.className = "card-title-link";
  link.href = `/${kindPath}/${encodeURIComponent(item.id)}`;
  link.textContent = item.name;
  title.appendChild(link);
  return title;
}

function buildCompetitionCard(competition, options = {}) {
  const competitionId = competition.competition_id || competition.id;
  const specialRequirements =
    competition.special_requirements || competition.eligibility?.special_requirements || [];
  const requiresSpecialCheck =
    Boolean(competition.requires_special_check) || specialRequirements.length > 0;
  const tierClass = options.catalogContext
    ? "catalog"
    : options.savedContext
    ? "saved"
    : requiresSpecialCheck
    ? "special"
    : competition.match_tier === "possible"
    ? "possible"
    : "strong";
  const article = document.createElement("article");
  article.className = `match-card ${tierClass}`;

  const pathBar = document.createElement("div");
  pathBar.className = "path-bar";
  pathBar.setAttribute("aria-hidden", "true");

  const body = document.createElement("div");
  body.className = "card-body";

  const header = document.createElement("div");
  header.className = "card-header";
  const headline = document.createElement("div");
  headline.className = "card-headline";

  const title = makeCardTitle("h4", "competitions", { ...competition, id: competitionId });
  headline.appendChild(title);

  if (competition.host) {
    const host = document.createElement("p");
    host.className = "card-sponsor";
    host.textContent = competition.host;
    headline.appendChild(host);
  }

  const formatLabel =
    competition.participation_format &&
    !String(competition.participation_format).startsWith("VERIFY")
      ? competition.participation_format.charAt(0).toUpperCase() +
        competition.participation_format.slice(1)
      : null;
  const metaParts = [competition.category, formatLabel, competition.location].filter(
    (part) => part && part !== "VERIFY" && !String(part).startsWith("VERIFY")
  );
  if (metaParts.length > 0) {
    const meta = document.createElement("p");
    meta.className = "card-program-meta";
    meta.textContent = metaParts.join(" · ");
    headline.appendChild(meta);
  }
  header.appendChild(headline);

  if (typeof competition.score === "number") {
    header.appendChild(buildFitRing(competition.score, tierClass));
  }

  body.appendChild(header);
  body.appendChild(buildCompetitionStatRow(competition));

  const provenance = buildVerificationSource(competition);
  if (provenance) {
    body.appendChild(provenance);
  }

  if (competition.match_reasons && competition.match_reasons.length > 0) {
    body.appendChild(buildReasons(competition.match_reasons));
  }

  if (requiresSpecialCheck) {
    const badges = document.createElement("div");
    badges.className = "badge-row";
    if (options.catalogContext) {
      badges.appendChild(makeBadge("Full catalog · not personalized", "badge-catalog"));
    }
    badges.appendChild(makeBadge("Special eligibility", "badge-special"));
    body.appendChild(badges);
  } else if (options.catalogContext) {
    const badges = document.createElement("div");
    badges.className = "badge-row";
    badges.appendChild(makeBadge("Full catalog · not personalized", "badge-catalog"));
    body.appendChild(badges);
  }

  if (specialRequirements.length > 0) {
    body.appendChild(buildSpecialRequirements(specialRequirements));
  }

  const steps = competition.application_requirements || [];
  if (steps.length > 0) {
    body.appendChild(buildProgramSteps(steps));
  }

  const footer = document.createElement("div");
  footer.className = "card-footer";
  const link = document.createElement("a");
  link.className = "card-link";
  link.href = competition.url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = requiresSpecialCheck ? "Check competition page" : "View competition";
  footer.appendChild(link);

  if (competitionId) {
    const actions = document.createElement("div");
    actions.className = "card-actions";
    const saveBtn = document.createElement("button");
    saveBtn.type = "button";
    saveBtn.className = "btn-save";
    applySavedButtonState(saveBtn, savedCompetitionIds.has(competitionId));
    saveBtn.addEventListener("click", () => toggleSavedCompetition(competitionId, saveBtn));
    actions.appendChild(saveBtn);
    footer.appendChild(actions);
  }
  body.appendChild(footer);

  article.appendChild(pathBar);
  article.appendChild(body);
  return article;
}

function buildProgramSteps(steps) {
  const wrap = document.createElement("div");
  wrap.className = "reasons program-steps";

  const heading = document.createElement("p");
  heading.className = "reasons-heading";
  heading.textContent = "Application steps";
  wrap.appendChild(heading);

  const list = document.createElement("ul");
  list.className = "reason-list";
  for (const step of steps) {
    const li = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = step.label;
    li.appendChild(title);
    if (step.details) {
      const details = document.createElement("span");
      details.className = "tracker-task-details";
      details.textContent = ` ${step.details}`;
      li.appendChild(details);
    }
    if (step.source_url) {
      li.appendChild(document.createTextNode(" "));
      const source = document.createElement("a");
      source.href = step.source_url;
      source.target = "_blank";
      source.rel = "noopener noreferrer";
      source.textContent = "Source";
      li.appendChild(source);
    }
    list.appendChild(li);
  }
  wrap.appendChild(list);
  return wrap;
}

function buildProgramCard(program, options = {}) {
  const programId = program.program_id || program.id;
  const specialRequirements =
    program.special_requirements || program.eligibility?.special_requirements || [];
  const requiresSpecialCheck =
    Boolean(program.requires_special_check) || specialRequirements.length > 0;
  const tierClass = options.catalogContext
    ? "catalog"
    : options.savedContext
    ? "saved"
    : requiresSpecialCheck
    ? "special"
    : program.match_tier === "possible"
    ? "possible"
    : "strong";
  const article = document.createElement("article");
  article.className = `match-card ${tierClass}`;

  const pathBar = document.createElement("div");
  pathBar.className = "path-bar";
  pathBar.setAttribute("aria-hidden", "true");

  const body = document.createElement("div");
  body.className = "card-body";

  const header = document.createElement("div");
  header.className = "card-header";
  const headline = document.createElement("div");
  headline.className = "card-headline";

  const title = makeCardTitle("h4", "programs", { ...program, id: programId });
  headline.appendChild(title);

  if (program.host) {
    const host = document.createElement("p");
    host.className = "card-sponsor";
    host.textContent = program.host;
    headline.appendChild(host);
  }

  const formatLabel =
    program.program_format && !String(program.program_format).startsWith("VERIFY")
      ? program.program_format.charAt(0).toUpperCase() + program.program_format.slice(1)
      : null;
  const metaParts = [program.subject, formatLabel, program.location].filter(
    (part) => part && part !== "VERIFY" && !String(part).startsWith("VERIFY")
  );
  if (metaParts.length > 0) {
    const meta = document.createElement("p");
    meta.className = "card-program-meta";
    meta.textContent = metaParts.join(" · ");
    headline.appendChild(meta);
  }
  header.appendChild(headline);

  if (typeof program.score === "number") {
    header.appendChild(buildFitRing(program.score, tierClass));
  }

  body.appendChild(header);
  body.appendChild(buildProgramStatRow(program));

  const provenance = buildVerificationSource(program);
  if (provenance) {
    body.appendChild(provenance);
  }

  if (program.match_reasons && program.match_reasons.length > 0) {
    body.appendChild(buildReasons(program.match_reasons));
  }

  if (requiresSpecialCheck) {
    const badges = document.createElement("div");
    badges.className = "badge-row";
    if (options.catalogContext) {
      badges.appendChild(makeBadge("Full catalog · not personalized", "badge-catalog"));
    }
    badges.appendChild(makeBadge("Special eligibility", "badge-special"));
    body.appendChild(badges);
  } else if (options.catalogContext) {
    const badges = document.createElement("div");
    badges.className = "badge-row";
    badges.appendChild(makeBadge("Full catalog · not personalized", "badge-catalog"));
    body.appendChild(badges);
  }

  if (specialRequirements.length > 0) {
    body.appendChild(buildSpecialRequirements(specialRequirements));
  }

  const steps = program.application_requirements || [];
  if (steps.length > 0) {
    body.appendChild(buildProgramSteps(steps));
  }

  const footer = document.createElement("div");
  footer.className = "card-footer";
  const link = document.createElement("a");
  link.className = "card-link";
  link.href = program.url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = requiresSpecialCheck ? "Check program page" : "View program";
  footer.appendChild(link);

  const adviceLoading = document.createElement("div");
  adviceLoading.className = "essay-advice-loading";
  adviceLoading.hidden = true;
  adviceLoading.innerHTML =
    '<div class="loading-spinner" aria-hidden="true"></div><p>Writing application advice for this program...</p>';

  const adviceError = document.createElement("div");
  adviceError.className = "essay-advice-error";
  adviceError.hidden = true;
  adviceError.setAttribute("role", "alert");

  const advicePanel = document.createElement("div");
  advicePanel.className = "essay-advice-panel";
  advicePanel.hidden = true;

  if (programId) {
    const actions = document.createElement("div");
    actions.className = "card-actions";
    const saveBtn = document.createElement("button");
    saveBtn.type = "button";
    saveBtn.className = "btn-save";
    applySavedButtonState(saveBtn, savedProgramIds.has(programId));
    saveBtn.addEventListener("click", () => toggleSavedProgram(programId, saveBtn));
    actions.appendChild(saveBtn);

    if (AI_ENABLED) {
      const adviceBtn = document.createElement("button");
      adviceBtn.type = "button";
      adviceBtn.className = "btn-secondary";
      adviceBtn.textContent = "Get application advice";
      adviceBtn.addEventListener("click", () =>
        handleProgramAdvice(programId, adviceBtn, advicePanel, adviceLoading, adviceError)
      );
      actions.appendChild(adviceBtn);
    }

    footer.appendChild(actions);
  }
  body.appendChild(footer);
  body.appendChild(adviceLoading);
  body.appendChild(adviceError);
  body.appendChild(advicePanel);

  article.appendChild(pathBar);
  article.appendChild(body);
  return article;
}

function matchToCard(match) {
  return {
    scholarship_id: match.scholarship_id,
    name: match.scholarship_name,
    sponsor: match.sponsor,
    award_amount: match.award_amount,
    deadline: match.deadline,
    estimated_deadline: match.estimated_deadline,
    url: match.url,
    verified: match.verified,
    verification_source_url: match.verification_source_url,
    last_verified_at: match.last_verified_at,
    closing_soon: match.closing_soon,
    score: match.score,
    score_breakdown: match.score_breakdown,
    eligible_schools: match.eligible_schools || [],
    requires_special_check: Boolean(match.requires_special_check),
    special_requirements: match.special_requirements || [],
    match_reasons: match.match_reasons || [],
    application_requirements: match.application_requirements || [],
  };
}

function scholarshipToCard(scholarship) {
  return {
    scholarship_id: scholarship.id,
    name: scholarship.name,
    sponsor: scholarship.sponsor,
    description: scholarship.description,
    award_amount: scholarship.award_amount,
    deadline: scholarship.deadline,
    estimated_deadline: scholarship.estimated_deadline,
    url: scholarship.url,
    verified: scholarship.verified,
    verification_source_url: scholarship.verification?.source_url || null,
    last_verified_at: scholarship.verification?.last_verified_at || null,
    closing_soon: computeClosingSoon(scholarship.deadline),
    eligible_schools: (scholarship.eligibility?.eligible_schools || []).map((s) => s.name),
    requires_special_check: Boolean(scholarship.eligibility?.special_requirements?.length),
    special_requirements: scholarship.eligibility?.special_requirements || [],
    application_requirements: scholarship.application_requirements || [],
    score: null,
    match_reasons: [],
  };
}

function computeClosingSoon(deadline) {
  // parseRealDeadline handles the rolling/VERIFY/invalid sentinels and parses
  // to local midnight. The bare Date(string) constructor parsed to UTC
  // midnight, letting this badge disagree with the plan timeline's "Due in N
  // days" by a day at the window edges in any non-UTC timezone.
  const target = parseRealDeadline(deadline);
  if (!target) {
    return false;
  }
  const diffDays = (target - new Date()) / (1000 * 60 * 60 * 24);
  return diffDays >= 0 && diffDays <= 30;
}

// Turns raw enum tokens that leak into reason strings (e.g. "high_school_senior")
// into readable text without disturbing the rest of the sentence.
function humanizeReason(text) {
  return String(text).replace(/[a-z0-9]+(?:_[a-z0-9]+)+/gi, (token) => token.replace(/_/g, " "));
}

function deadlineParts(deadline, estimated) {
  if (deadline === "rolling") {
    return { value: "Rolling", note: "Applications accepted anytime" };
  }
  if (!deadline || deadline === "VERIFY" || String(deadline).startsWith("VERIFY")) {
    if (estimated) {
      // A past estimate is last cycle's closed date; showing it as an upcoming
      // deadline reads as "already passed." Present it honestly instead: the new
      // date is not announced yet (these are annual awards that reopen).
      if (isPastDate(estimated)) {
        return {
          value: "Not yet announced",
          note: `Last cycle closed ${formatMonthYear(estimated)}; check sponsor site`,
        };
      }
      return { value: formatVerifiedDate(estimated), note: "Estimated; confirm on sponsor site" };
    }
    return { value: "Not listed", note: "Confirm on sponsor site" };
  }
  return { value: formatVerifiedDate(deadline), note: "" };
}

function isPastDate(isoDate) {
  const parsed = parseRealDeadline(isoDate);
  if (!parsed) {
    return false;
  }
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return parsed < today;
}

function formatMonthYear(isoDate) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(isoDate || ""));
  if (!match) {
    return isoDate;
  }
  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ];
  return `${months[Number(match[2]) - 1]} ${match[1]}`;
}

// Circular fit gauge: gives every match a single, scannable anchor and fills
// the horizontal space the old flat layout left empty.
function buildFitRing(score, tierClass) {
  const pct = Math.max(0, Math.min(100, Math.round(score)));
  const r = 26;
  const circ = Number((2 * Math.PI * r).toFixed(2));
  const dash = Number(((pct / 100) * circ).toFixed(2));
  const label =
    tierClass === "special"
      ? "Check eligibility"
      : tierClass === "possible"
      ? "Possible fit"
      : "Strong fit";

  const wrap = document.createElement("div");
  wrap.className = "fit-ring";
  wrap.setAttribute("role", "img");
  wrap.setAttribute("aria-label", `Fit score ${pct} out of 100 \u2014 ${label}`);
  wrap.innerHTML =
    '<div class="fit-ring-dial">' +
    '<svg class="fit-ring-svg" viewBox="0 0 64 64" aria-hidden="true">' +
    `<circle class="fit-ring-track" cx="32" cy="32" r="${r}"></circle>` +
    `<circle class="fit-ring-value" cx="32" cy="32" r="${r}" transform="rotate(-90 32 32)" style="--circ:${circ};--dash:${dash}"></circle>` +
    "</svg>" +
    '<div class="fit-ring-num"><strong>0</strong><span>fit</span></div>' +
    "</div>" +
    `<span class="fit-ring-label">${label}</span>`;

  const numEl = wrap.querySelector(".fit-ring-num strong");
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    numEl.textContent = String(pct);
  } else {
    const start = performance.now();
    const duration = 850;
    const step = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      numEl.textContent = String(Math.round(eased * pct));
      if (t < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }
  return wrap;
}

function buildStatRow(card) {
  const row = document.createElement("div");
  row.className = "card-stats";

  const award = document.createElement("div");
  award.className = "stat stat-award";
  award.innerHTML =
    '<span class="stat-label">Award</span>' +
    `<span class="stat-value">${escapeHtml(formatAward(card.award_amount))}</span>`;
  row.appendChild(award);

  const dl = deadlineParts(card.deadline, card.estimated_deadline);
  const deadline = document.createElement("div");
  deadline.className = "stat stat-deadline";
  if (card.closing_soon) {
    deadline.classList.add("stat-urgent");
    if (!dl.note) dl.note = "Closing soon";
  }
  deadline.innerHTML =
    '<span class="stat-label">Deadline</span>' +
    `<span class="stat-value">${escapeHtml(dl.value)}</span>` +
    (dl.note ? `<span class="stat-note">${escapeHtml(dl.note)}</span>` : "");
  row.appendChild(deadline);

  return row;
}

// Humanized, scannable reasons. Long lists collapse to the top few with a
// toggle so the card stays calm instead of dumping a wall of bullets.
function buildReasons(reasons) {
  const wrap = document.createElement("div");
  wrap.className = "reasons";

  const heading = document.createElement("p");
  heading.className = "reasons-heading";
  heading.textContent = "Why this matched";
  wrap.appendChild(heading);

  const list = document.createElement("ul");
  list.className = "reason-list";
  const VISIBLE = 4;
  reasons.forEach((reason, index) => {
    const li = document.createElement("li");
    li.textContent = humanizeReason(reason);
    if (index >= VISIBLE) li.classList.add("reason-hidden");
    list.appendChild(li);
  });
  wrap.appendChild(list);

  if (reasons.length > VISIBLE) {
    const hidden = reasons.length - VISIBLE;
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "reasons-toggle";
    toggle.textContent = `Show ${hidden} more reason${hidden === 1 ? "" : "s"}`;
    toggle.addEventListener("click", () => {
      const open = wrap.classList.toggle("reasons-open");
      toggle.textContent = open
        ? "Show fewer reasons"
        : `Show ${hidden} more reason${hidden === 1 ? "" : "s"}`;
    });
    wrap.appendChild(toggle);
  }
  return wrap;
}

function buildSpecialRequirements(requirements) {
  const wrap = document.createElement("div");
  wrap.className = "special-requirements";

  const heading = document.createElement("p");
  heading.className = "special-requirements-heading";
  heading.textContent = "Special eligibility to verify";
  wrap.appendChild(heading);

  const list = document.createElement("ul");
  list.className = "special-requirements-list";
  for (const requirement of requirements) {
    const li = document.createElement("li");
    const label = document.createElement("strong");
    label.textContent = requirement.label || "Extra eligibility check";
    li.appendChild(label);
    if (requirement.details) {
      li.appendChild(document.createTextNode(`: ${requirement.details}`));
    }
    list.appendChild(li);
  }
  wrap.appendChild(list);

  return wrap;
}

function buildCard(card, tierClass) {
  const article = document.createElement("article");
  article.className = `match-card ${tierClass}`;

  const pathBar = document.createElement("div");
  pathBar.className = "path-bar";
  pathBar.setAttribute("aria-hidden", "true");

  const body = document.createElement("div");
  body.className = "card-body";

  const header = document.createElement("div");
  header.className = "card-header";

  const headline = document.createElement("div");
  headline.className = "card-headline";

  const title = makeCardTitle("h4", "scholarships", { ...card, id: card.scholarship_id });
  headline.appendChild(title);

  if (card.sponsor) {
    const sponsor = document.createElement("p");
    sponsor.className = "card-sponsor";
    sponsor.textContent = card.sponsor;
    headline.appendChild(sponsor);
  }
  header.appendChild(headline);

  if (typeof card.score === "number") {
    header.appendChild(buildFitRing(card.score, tierClass));
  }

  const stats = buildStatRow(card);

  const badges = document.createElement("div");
  badges.className = "badge-row";
  if (card.catalog_context) {
    badges.appendChild(makeBadge("Full catalog · not personalized", "badge-catalog"));
  }
  if (card.closing_soon) {
    badges.appendChild(makeBadge("Closing soon", "badge-closing"));
  }
  if (!card.verified) {
    badges.appendChild(makeBadge("Unverified data", "badge-unverified"));
  }
  if (card.requires_special_check) {
    badges.appendChild(makeBadge("Special eligibility", "badge-special"));
  }
  if (card.eligible_schools && card.eligible_schools.length > 0) {
    const targetMatched = card.score_breakdown && card.score_breakdown.target_school > 0;
    if (targetMatched) {
      badges.appendChild(makeBadge("At your target school", "badge-school-match"));
    } else {
      badges.appendChild(
        makeBadge("Only at " + schoolBadgeLabel(card.eligible_schools), "badge-school")
      );
    }
  }

  body.appendChild(header);
  body.appendChild(stats);
  const provenance = buildVerificationSource(card);
  if (provenance) {
    body.appendChild(provenance);
  }
  const breakdown = card.score_breakdown ? buildScoreBreakdown(card.score_breakdown) : null;
  if (breakdown) {
    body.appendChild(breakdown);
  }
  if (badges.childElementCount > 0) {
    body.appendChild(badges);
  }

  if (card.special_requirements && card.special_requirements.length > 0) {
    body.appendChild(buildSpecialRequirements(card.special_requirements));
  }

  if (card.match_reasons && card.match_reasons.length > 0) {
    body.appendChild(buildReasons(card.match_reasons));
  }

  const link = document.createElement("a");
  link.className = "card-link";
  link.href = card.url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = card.requires_special_check ? "Check sponsor page" : "View and apply";

  const footer = document.createElement("div");
  footer.className = "card-footer";
  footer.appendChild(link);

  const actions = document.createElement("div");
  actions.className = "card-actions";

  const saveBtn = document.createElement("button");
  saveBtn.type = "button";
  saveBtn.className = "btn-save";
  applySavedButtonState(saveBtn, savedIds.has(card.scholarship_id));
  saveBtn.addEventListener("click", () => toggleSaved(card.scholarship_id, saveBtn));
  actions.appendChild(saveBtn);

  const adviceBtn = document.createElement("button");
  adviceBtn.type = "button";
  adviceBtn.className = "btn-secondary";
  adviceBtn.textContent = "Get essay advice";

  const adviceLoading = document.createElement("div");
  adviceLoading.className = "essay-advice-loading";
  adviceLoading.hidden = true;
  adviceLoading.innerHTML =
    '<div class="loading-spinner" aria-hidden="true"></div><p>Writing essay advice for this scholarship...</p>';

  const adviceError = document.createElement("div");
  adviceError.className = "essay-advice-error";
  adviceError.hidden = true;
  adviceError.setAttribute("role", "alert");

  const advicePanel = document.createElement("div");
  advicePanel.className = "essay-advice-panel";
  advicePanel.hidden = true;

  if (AI_ENABLED) {
    adviceBtn.addEventListener("click", () =>
      handleEssayAdvice(card.scholarship_id, adviceBtn, advicePanel, adviceLoading, adviceError)
    );
    actions.appendChild(adviceBtn);
  }

  const reviewBtn = document.createElement("button");
  reviewBtn.type = "button";
  reviewBtn.className = "btn-secondary";
  reviewBtn.textContent = "Review my draft";

  const reviewForm = document.createElement("div");
  reviewForm.className = "essay-review-form";
  reviewForm.hidden = true;

  const reviewInput = document.createElement("textarea");
  reviewInput.className = "essay-review-input";
  reviewInput.rows = 8;
  reviewInput.maxLength = 8000;
  reviewInput.placeholder =
    "Paste your draft essay here, then click Get feedback. Your profile answers are included automatically.";

  const reviewSubmit = document.createElement("button");
  reviewSubmit.type = "button";
  reviewSubmit.className = "btn-primary";
  reviewSubmit.textContent = "Get feedback";

  reviewForm.appendChild(reviewInput);
  reviewForm.appendChild(reviewSubmit);

  const reviewLoading = document.createElement("div");
  reviewLoading.className = "essay-advice-loading";
  reviewLoading.hidden = true;
  reviewLoading.innerHTML =
    '<div class="loading-spinner" aria-hidden="true"></div><p>Reviewing your draft for this scholarship...</p>';

  const reviewError = document.createElement("div");
  reviewError.className = "essay-advice-error";
  reviewError.hidden = true;
  reviewError.setAttribute("role", "alert");

  const reviewPanel = document.createElement("div");
  reviewPanel.className = "essay-advice-panel";
  reviewPanel.hidden = true;

  if (AI_ENABLED) {
    reviewBtn.addEventListener("click", () => {
      reviewForm.hidden = !reviewForm.hidden;
      if (!reviewForm.hidden) {
        reviewInput.focus();
      }
    });
    reviewSubmit.addEventListener("click", () =>
      handleEssayReview(
        card.scholarship_id,
        reviewInput,
        reviewSubmit,
        reviewPanel,
        reviewLoading,
        reviewError
      )
    );
    actions.appendChild(reviewBtn);
  }

  footer.appendChild(actions);
  body.appendChild(footer);
  body.appendChild(adviceLoading);
  body.appendChild(adviceError);
  body.appendChild(advicePanel);
  body.appendChild(reviewForm);
  body.appendChild(reviewLoading);
  body.appendChild(reviewError);
  body.appendChild(reviewPanel);

  article.appendChild(pathBar);
  article.appendChild(body);
  return article;
}

// Breaks the single fit score into its contributing parts so the "transparent
// scoring" promise is visible, not just claimed. Only non-zero parts are shown.
function buildScoreBreakdown(breakdown) {
  const parts = [
    ["Field of study", breakdown.field_of_study],
    ["Background", breakdown.demographics],
    ["Target school", breakdown.target_school],
    ["Activities", breakdown.activities],
    ["Financial need", breakdown.financial_need],
  ].filter(([, value]) => value > 0);
  if (parts.length === 0) {
    return null;
  }
  const wrap = document.createElement("div");
  wrap.className = "score-breakdown";
  for (const [label, value] of parts) {
    const chip = document.createElement("span");
    chip.className = "score-chip";
    chip.textContent = `${label} +${value}`;
    wrap.appendChild(chip);
  }
  return wrap;
}

// A fact audit older than this is flagged for re-verification. Sponsor pages
// change over a cycle, so a stale audit date should prompt a fresh check.
const STALE_VERIFICATION_DAYS = 90;

// Parse a "YYYY-MM-DD" date as UTC to avoid local-timezone off-by-one errors.
function parseIsoDateUTC(isoDate) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(isoDate || ""));
  if (!match) {
    return null;
  }
  return Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
}

function verificationAgeDays(isoDate) {
  const then = parseIsoDateUTC(isoDate);
  if (then === null) {
    return null;
  }
  return Math.floor((Date.now() - then) / 86400000);
}

function formatVerifiedDate(isoDate) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(isoDate || ""));
  if (!match) {
    return isoDate;
  }
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${months[Number(match[2]) - 1]} ${Number(match[3])}, ${match[1]}`;
}

function httpUrlHref(value) {
  if (!value) {
    return null;
  }
  try {
    const parsed = new URL(String(value));
    return parsed.protocol === "http:" || parsed.protocol === "https:" ? parsed.href : null;
  } catch {
    return null;
  }
}

function buildVerificationSource(card) {
  if (!card.verification_source_url && !card.last_verified_at) {
    return null;
  }
  const wrap = document.createElement("div");
  wrap.className = "verification-source";
  const sourceUrl = card.verification_source_url ? String(card.verification_source_url) : "";
  const sourceHref = httpUrlHref(sourceUrl);
  let stale = false;
  if (card.last_verified_at) {
    const ageDays = verificationAgeDays(card.last_verified_at);
    stale = ageDays !== null && ageDays > STALE_VERIFICATION_DAYS;
    const date = document.createElement("span");
    date.textContent = `Verified ${formatVerifiedDate(card.last_verified_at)}`;
    wrap.appendChild(date);
    if (stale) {
      wrap.classList.add("verification-stale");
      const flag = document.createElement("span");
      flag.className = "verification-stale-flag";
      flag.textContent = "Re-verify on source";
      wrap.appendChild(flag);
    }
  } else if (sourceUrl) {
    const source = document.createElement("span");
    source.textContent = "Official source on file";
    wrap.appendChild(source);
  }
  if (sourceHref) {
    const link = document.createElement("a");
    link.href = sourceHref;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = stale
      ? "Re-check on sponsor page"
      : card.last_verified_at
      ? "View verified source"
      : "View sponsor page";
    wrap.appendChild(link);
  } else if (sourceUrl) {
    const sourceText = document.createElement("span");
    sourceText.textContent = sourceUrl;
    wrap.appendChild(sourceText);
  }
  return wrap;
}

function schoolBadgeLabel(schools) {
  if (schools.length === 1) {
    return schools[0];
  }
  return `${schools[0]} +${schools.length - 1}`;
}

function makeBadge(text, className) {
  const span = document.createElement("span");
  span.className = `badge ${className}`;
  span.textContent = text;
  return span;
}

function formatAward(amount) {
  if (typeof amount === "number") {
    return `$${amount.toLocaleString()}`;
  }
  return String(amount);
}

function formatDeadline(deadline, estimated) {
  if (deadline === "rolling") {
    return "Rolling";
  }
  if (!deadline || deadline === "VERIFY" || String(deadline).startsWith("VERIFY")) {
    return estimated
      ? `~${estimated} (estimated; confirm official date)`
      : "Confirm on sponsor site";
  }
  return deadline;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Explicit, one-time consent before any inputs (profile, résumé, essay text,
// which include sensitive fields) are sent to Anthropic's third-party API.
function ensureAiConsent() {
  if (localStorage.getItem("ai_consent") === "yes") {
    return true;
  }
  const ok = window.confirm(
    "This feature sends your inputs, including your profile details and any résumé or " +
      "essay text you provide, to Anthropic's API to generate AI guidance. Your data is " +
      "processed there to produce the result and is not stored by this app. Continue?"
  );
  if (ok) {
    localStorage.setItem("ai_consent", "yes");
  }
  return ok;
}

async function handleEssayAdvice(scholarshipId, button, panel, loading, errorEl) {
  if (!lastSubmittedProfile) {
    errorEl.textContent =
      "Submit your profile first so essay advice can use your current answers.";
    errorEl.hidden = false;
    panel.hidden = true;
    return;
  }

  if (!ensureAiConsent()) {
    return;
  }

  errorEl.hidden = true;
  panel.hidden = true;
  loading.hidden = false;
  button.disabled = true;

  try {
    const response = await fetch("/essay-advice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student: lastSubmittedProfile,
        scholarship_id: scholarshipId,
      }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const message =
        data.detail?.error ||
        (typeof data.detail === "string" ? data.detail : null) ||
        "Essay advice could not be loaded. Try again in a few minutes.";
      errorEl.textContent = message;
      errorEl.hidden = false;
      return;
    }

    panel.innerHTML = "";
    const heading = document.createElement("h5");
    heading.className = "essay-advice-heading";
    heading.textContent = "Essay advice";
    const content = document.createElement("div");
    content.className = "essay-advice-content";
    content.textContent = data.advice;
    panel.appendChild(heading);
    panel.appendChild(content);
    panel.hidden = false;
  } catch (err) {
    errorEl.textContent =
      "Essay advice could not be loaded. Check your connection and try again.";
    errorEl.hidden = false;
    console.error(err);
  } finally {
    loading.hidden = true;
    button.disabled = false;
  }
}

async function handleEssayReview(scholarshipId, input, button, panel, loading, errorEl) {
  if (!lastSubmittedProfile) {
    errorEl.textContent =
      "Submit your profile first so feedback can use your current answers.";
    errorEl.hidden = false;
    panel.hidden = true;
    return;
  }

  const draft = input.value.trim();
  if (!draft) {
    errorEl.textContent = "Paste your draft essay before asking for feedback.";
    errorEl.hidden = false;
    panel.hidden = true;
    return;
  }

  if (!ensureAiConsent()) {
    return;
  }

  errorEl.hidden = true;
  panel.hidden = true;
  loading.hidden = false;
  button.disabled = true;

  try {
    const response = await fetch("/essay-review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student: lastSubmittedProfile,
        scholarship_id: scholarshipId,
        draft,
      }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const message =
        data.detail?.error ||
        (typeof data.detail === "string" ? data.detail : null) ||
        "Feedback could not be loaded. Try again in a few minutes.";
      errorEl.textContent = message;
      errorEl.hidden = false;
      return;
    }

    panel.innerHTML = "";
    const heading = document.createElement("h5");
    heading.className = "essay-advice-heading";
    heading.textContent = "Draft feedback";
    const content = document.createElement("div");
    content.className = "essay-advice-content";
    content.textContent = data.feedback;
    panel.appendChild(heading);
    panel.appendChild(content);
    panel.hidden = false;
  } catch (err) {
    errorEl.textContent =
      "Feedback could not be loaded. Check your connection and try again.";
    errorEl.hidden = false;
    console.error(err);
  } finally {
    loading.hidden = true;
    button.disabled = false;
  }
}

async function handleProgramAdvice(programId, button, panel, loading, errorEl) {
  if (!lastSubmittedProfile) {
    errorEl.textContent =
      "Submit your profile first so application advice can use your current answers.";
    errorEl.hidden = false;
    panel.hidden = true;
    return;
  }

  if (!ensureAiConsent()) {
    return;
  }

  errorEl.hidden = true;
  panel.hidden = true;
  loading.hidden = false;
  button.disabled = true;

  try {
    const response = await fetch("/program-advice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student: lastSubmittedProfile,
        program_id: programId,
      }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const message =
        data.detail?.error ||
        (typeof data.detail === "string" ? data.detail : null) ||
        "Application advice could not be loaded. Try again in a few minutes.";
      errorEl.textContent = message;
      errorEl.hidden = false;
      return;
    }

    panel.innerHTML = "";
    const heading = document.createElement("h5");
    heading.className = "essay-advice-heading";
    heading.textContent = "Application advice";
    const content = document.createElement("div");
    content.className = "essay-advice-content";
    content.textContent = data.advice;
    panel.appendChild(heading);
    panel.appendChild(content);
    panel.hidden = false;
  } catch (err) {
    errorEl.textContent =
      "Application advice could not be loaded. Check your connection and try again.";
    errorEl.hidden = false;
    console.error(err);
  } finally {
    loading.hidden = true;
    button.disabled = false;
  }
}

// ---- Phase 1: the World layer (decorative; Save-Data aware) --------------
(function initWorldLayer() {
  var saveData =
    document.documentElement.classList.contains("save-data") ||
    (navigator.connection && navigator.connection.saveData === true);
  var worldStageRequested = false;
  window.__ensureWorldStage = function () {
    if (worldStageRequested || saveData) return;
    worldStageRequested = true;
    var link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/static/css/world.css?v=20260721-3";
    link.addEventListener(
      "load",
      function () {
        document.documentElement.classList.add("world-ready");
      },
      { once: true }
    );
    document.head.appendChild(link);
  };
  if (!saveData) {
    var plates = document.querySelectorAll(
      ".world-plate img[data-src], .world-dusk img[data-src], .teaser-painting img[data-src]"
    );
    plates.forEach(function (img) {
      // Creatures are display:none below 1200px; do not hydrate what cannot
      // show (loading=lazy would likely skip the fetch, but be explicit).
      if (getComputedStyle(img).display === "none") return;
      img.addEventListener(
        "load",
        function () {
          img.classList.add("world-loaded");
        },
        { once: true }
      );
      if (img.dataset.srcset) img.srcset = img.dataset.srcset;
      img.src = img.dataset.src;
    });
  }
  var fireflies = document.querySelectorAll(".fireflies");
  if (
    fireflies.length &&
    "IntersectionObserver" in window &&
    !window.matchMedia("(prefers-reduced-motion: reduce)").matches
  ) {
    var fireflyObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        entry.target.classList.toggle("fireflies-live", entry.isIntersecting);
      });
    });
    fireflies.forEach(function (el) {
      fireflyObserver.observe(el);
    });
  }
})();
