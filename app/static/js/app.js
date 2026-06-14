/**
 * Scholarships4U frontend. All state lives in memory (no browser storage).
 */

let vocabulary = null;
let lastSubmittedProfile = null;

const form = document.getElementById("profile-form");
const formError = document.getElementById("form-error");
const resultsSection = document.getElementById("results-section");
const resultsContainer = document.getElementById("results-container");
const resultsSummary = document.getElementById("results-summary");
const resultsEmpty = document.getElementById("results-empty");
const loadingEl = document.getElementById("loading");
const submitBtn = document.getElementById("submit-btn");

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
}

function populateForm(vocab) {
  fillSelect("grade-level", vocab.grade_level);
  fillSelect("citizenship", vocab.citizenship);
  fillSelect("state", vocab.state);
  fillSelect("financial-need", vocab.financial_need_level);
  fillCheckboxes("fields-of-study", vocab.fields_of_study, "fields");
  fillCheckboxes("demographic-tags", vocab.demographic_tags, "demographics");
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

    label.appendChild(input);
    label.appendChild(document.createTextNode(opt.label));
    container.appendChild(label);
  }
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
  }
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
  setLoading(true);

  try {
    const response = await fetch("/match", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(built.profile),
    });

    if (response.status === 422) {
      const data = await response.json();
      showFormError(formatValidationErrors(data.detail));
      setLoading(false);
      return;
    }

    if (!response.ok) {
      throw new Error(`Match request failed (${response.status})`);
    }

    const results = await response.json();
    lastSubmittedProfile = built.profile;
    renderResults(results);
  } catch (err) {
    showFormError(
      "The match request did not go through. Check your connection and try again."
    );
    console.error(err);
  } finally {
    setLoading(false);
  }
}

function renderResults(results) {
  resultsContainer.innerHTML = "";

  if (results.length === 0) {
    resultsSummary.textContent = "";
    resultsEmpty.hidden = false;
    return;
  }

  resultsEmpty.hidden = true;
  const strong = results.filter((r) => r.match_tier === "strong");
  const possible = results.filter((r) => r.match_tier === "possible");

  resultsSummary.textContent = `${results.length} scholarship${results.length === 1 ? "" : "s"} matched your profile.`;

  if (strong.length > 0) {
    resultsContainer.appendChild(buildTierSection("Strong matches", strong, "strong"));
  }
  if (possible.length > 0) {
    resultsContainer.appendChild(
      buildTierSection("Possible matches", possible, "possible")
    );
  }
}

function buildTierSection(title, matches, tierClass) {
  const section = document.createElement("div");
  section.className = "tier-section";

  const heading = document.createElement("h3");
  heading.className = `tier-heading ${tierClass === "possible" ? "possible" : ""}`;
  heading.textContent = title;
  section.appendChild(heading);

  for (const match of matches) {
    section.appendChild(buildCard(match, tierClass));
  }

  return section;
}

function buildCard(match, tierClass) {
  const card = document.createElement("article");
  card.className = `match-card ${tierClass}`;

  const pathBar = document.createElement("div");
  pathBar.className = "path-bar";
  pathBar.setAttribute("aria-hidden", "true");

  const body = document.createElement("div");
  body.className = "card-body";

  const top = document.createElement("div");
  top.className = "card-top";

  const title = document.createElement("h4");
  title.className = "card-title";
  title.textContent = match.scholarship_name;

  const score = document.createElement("span");
  score.className = "card-score";
  score.textContent = `Fit score: ${match.score}`;

  top.appendChild(title);
  top.appendChild(score);

  const meta = document.createElement("dl");
  meta.className = "card-meta";
  meta.innerHTML = `
    <div><dt>Sponsor</dt><dd>${escapeHtml(match.sponsor)}</dd></div>
    <div><dt>Award</dt><dd>${escapeHtml(formatAward(match.award_amount))}</dd></div>
    <div><dt>Deadline</dt><dd>${escapeHtml(formatDeadline(match.deadline))}</dd></div>
  `;

  const badges = document.createElement("div");
  badges.className = "badge-row";
  if (match.closing_soon) {
    badges.appendChild(makeBadge("Closing soon", "badge-closing"));
  }
  if (!match.verified) {
    badges.appendChild(makeBadge("Unverified data", "badge-unverified"));
  }

  const reasons = document.createElement("div");
  reasons.className = "reasons";
  const details = document.createElement("details");
  details.open = true;
  const summary = document.createElement("summary");
  summary.textContent = "Why this matched";
  const list = document.createElement("ul");
  for (const reason of match.match_reasons) {
    const li = document.createElement("li");
    li.textContent = reason;
    list.appendChild(li);
  }
  details.appendChild(summary);
  details.appendChild(list);
  reasons.appendChild(details);

  const link = document.createElement("a");
  link.className = "card-link";
  link.href = match.url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = "View and apply";

  const actions = document.createElement("div");
  actions.className = "card-actions";

  const adviceBtn = document.createElement("button");
  adviceBtn.type = "button";
  adviceBtn.className = "btn-secondary";
  adviceBtn.textContent = "Get essay advice";
  adviceBtn.addEventListener("click", () =>
    handleEssayAdvice(match.scholarship_id, adviceBtn, advicePanel, adviceLoading, adviceError)
  );

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

  actions.appendChild(adviceBtn);

  body.appendChild(top);
  body.appendChild(meta);
  if (badges.childElementCount > 0) {
    body.appendChild(badges);
  }
  body.appendChild(reasons);
  body.appendChild(link);
  body.appendChild(actions);
  body.appendChild(adviceLoading);
  body.appendChild(adviceError);
  body.appendChild(advicePanel);

  card.appendChild(pathBar);
  card.appendChild(body);
  return card;
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

function formatDeadline(deadline) {
  if (deadline === "rolling") {
    return "Rolling";
  }
  if (deadline === "VERIFY" || deadline.startsWith("VERIFY")) {
    return "Confirm on sponsor site";
  }
  return deadline;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

async function handleEssayAdvice(scholarshipId, button, panel, loading, errorEl) {
  if (!lastSubmittedProfile) {
    errorEl.textContent =
      "Submit your profile first so essay advice can use your current answers.";
    errorEl.hidden = false;
    panel.hidden = true;
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

    const data = await response.json();

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
