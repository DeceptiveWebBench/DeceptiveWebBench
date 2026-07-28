(function () {
  function normalizeCondition(value) {
    if (!value) return "no_warning";
    return String(value).trim().toLowerCase();
  }

  function getCondition() {
    const params = new URLSearchParams(window.location.search);
    const queryCondition = params.get("condition");
    if (queryCondition) return normalizeCondition(queryCondition);

    const root = document.getElementById("task-root");
    if (root && root.dataset.defaultCondition) {
      return normalizeCondition(root.dataset.defaultCondition);
    }

    return "no_warning";
  }

  function applyCondition() {
    const condition = getCondition();
    const root = document.getElementById("task-root");
    const uiWarnings = document.querySelectorAll("[data-warning-channel='ui']");
    const chips = document.querySelectorAll("[data-condition-chip]");
    const riskAnchors = document.querySelectorAll("[data-risk-anchor='true']");

    if (root) {
      root.setAttribute("data-active-condition", condition);
    }

    uiWarnings.forEach(function (el) {
      if (condition === "ui_warning") {
        el.classList.remove("is-hidden");
      } else {
        el.classList.add("is-hidden");
      }
    });

    chips.forEach(function (chip) {
      chip.textContent = "Condition: " + condition;
    });

    riskAnchors.forEach(function (el) {
      if (condition === "ui_warning") {
        el.classList.add("risk-highlight");
      } else {
        el.classList.remove("risk-highlight");
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyCondition);
  } else {
    applyCondition();
  }
})();
