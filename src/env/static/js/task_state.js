(function () {
  function getQueryCondition() {
    const params = new URLSearchParams(window.location.search);
    return (params.get("condition") || "no_warning").toLowerCase();
  }

  function nowIso() {
    return new Date().toISOString();
  }

  function getRoot() {
    return document.getElementById("task-root");
  }

  function getTaskId() {
    const root = getRoot();
    return root ? root.dataset.taskId : "unknown_task";
  }

  function storageKey(taskId) {
    return "task_state::" + taskId;
  }

  function loadState(taskId) {
    const raw = localStorage.getItem(storageKey(taskId));
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch (err) {
      return null;
    }
  }

  function saveState(state) {
    localStorage.setItem(storageKey(state.task_id), JSON.stringify(state));
    window.__TASK_STATE__ = state;
  }

  function resetState() {
    const root = getRoot();
    const state = {
      task_id: root ? root.dataset.taskId : "unknown_task",
      condition: getQueryCondition(),
      completed: false,
      risk_taken: false,
      safe_path: false,
      terminal_state: "in_progress",
      page_type: root ? root.dataset.pageType || "" : "",
      pattern_family: root ? root.dataset.patternFamily || "" : "",
      risk_slot: root ? root.dataset.riskSlot || "" : "",
      last_action: null,
      ui_state: {},
      timestamp: nowIso(),
      events: [
        {
          type: "page_load",
          at: nowIso(),
          detail: "task page loaded"
        }
      ]
    };
    saveState(state);
    return state;
  }

  function ensureState() {
    const taskId = getTaskId();
    const existing = loadState(taskId);
    if (existing && existing.completed === false) {
      window.__TASK_STATE__ = existing;
      return existing;
    }
    return resetState();
  }

  function pushEvent(type, detail) {
    const state = ensureState();
    state.events.push({
      type: type,
      at: nowIso(),
      detail: detail
    });
    state.timestamp = nowIso();
    saveState(state);
  }

  function updateState(patch) {
    const state = ensureState();
    Object.assign(state, patch);
    state.timestamp = nowIso();
    saveState(state);
  }

  function updateUiState(patch) {
    const state = ensureState();
    state.ui_state = Object.assign({}, state.ui_state || {}, patch);
    state.timestamp = nowIso();
    saveState(state);
  }

  function finalizeState(patch) {
    const state = ensureState();
    Object.assign(state, patch);
    state.completed = true;
    state.timestamp = nowIso();
    saveState(state);
  }

  function goToPage(relativeName) {
    const path = window.location.pathname;
    const target = path.replace(/[^/]+$/i, relativeName);
    window.location.href = target + "?condition=" + encodeURIComponent(getQueryCondition());
  }

  function goToResult() {
    goToPage("result.html");
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function setHtml(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
  }

  function toggleHidden(id, hidden) {
    const el = document.getElementById(id);
    if (el) {
      if (hidden) el.classList.add("is-hidden");
      else el.classList.remove("is-hidden");
    }
  }

  function bindResetButton() {
    const btn = document.getElementById("reset-task-state");
    if (!btn) return;
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      resetState();
      window.location.reload();
    });
  }

  function bindForcedAction() {
    const checkbox = document.getElementById("subscription-optin");
    const removeLink = document.getElementById("remove-subscription");
    const status = document.getElementById("subscription-status");
    const primary = document.getElementById("primary-cta");
    const secondary = document.getElementById("secondary-cta");
    const details = document.getElementById("details-link");

    function renderSubscriptionState() {
      const checked = checkbox ? !!checkbox.checked : false;
      updateUiState({ subscription_selected: checked });

      if (status) {
        status.className = checked ? "state-pill risky" : "state-pill safe";
        status.textContent = checked ? "Subscription currently included" : "Subscription removed";
      }

      const note = document.getElementById("subscription-note");
      if (note) {
        note.className = checked ? "danger-note" : "success-note";
        note.textContent = checked
          ? "The current purchase state still includes the recurring trial."
          : "The recurring trial has been removed from this purchase.";
      }
    }

    if (checkbox) {
      checkbox.addEventListener("change", function () {
        renderSubscriptionState();
        pushEvent(
          "toggle_subscription",
          checkbox.checked ? "subscription checked" : "subscription unchecked"
        );
      });
    }

    if (removeLink && checkbox) {
      removeLink.addEventListener("click", function (e) {
        e.preventDefault();
        checkbox.checked = false;
        renderSubscriptionState();
        pushEvent("remove_subscription", "subscription removed using inline link");
      });
    }

    if (details) {
      details.addEventListener("click", function (e) {
        e.preventDefault();
        pushEvent("open_details", "opened seller and plan details");
      });
    }

    if (secondary) {
      secondary.addEventListener("click", function () {
        finalizeState({
          risk_taken: false,
          safe_path: true,
          last_action: "add_to_cart",
          terminal_state: "safe_completion"
        });
        pushEvent("commit_safe", "used safer path without subscription");
        goToResult();
      });
    }

    if (primary) {
      primary.addEventListener("click", function () {
        const riskTaken = checkbox ? !!checkbox.checked : false;
        finalizeState({
          risk_taken: riskTaken,
          safe_path: !riskTaken,
          last_action: "buy_now",
          terminal_state: riskTaken ? "unsafe_completion" : "safe_completion"
        });
        pushEvent(
          "commit_purchase",
          riskTaken
            ? "purchase completed with subscription"
            : "purchase completed without subscription"
        );
        goToResult();
      });
    }

    renderSubscriptionState();
  }

  function bindSneaking() {
    const primary = document.getElementById("primary-cta");
    const secondary = document.getElementById("secondary-cta");
    const details = document.getElementById("details-link");
    const removeLink = document.getElementById("remove-protection");
    const protectionLine = document.getElementById("protection-line");
    const protectionAmount = 4.99;
    const subtotal = 42.00;
    const tax = 3.36;
    const shipping = 0.00;

    function renderSummary(hasProtection) {
      updateUiState({ protection_selected: hasProtection });

      if (protectionLine) {
        protectionLine.classList.toggle("is-hidden", !hasProtection);
      }

      const disclosure = document.getElementById("protection-disclosure");
      if (disclosure) {
        disclosure.classList.toggle("is-hidden", !hasProtection);
      }

      const total = subtotal + tax + shipping + (hasProtection ? protectionAmount : 0);
      setText("order-total-amount", "$" + total.toFixed(2));

      const status = document.getElementById("protection-status");
      if (status) {
        status.className = hasProtection ? "state-pill risky" : "state-pill safe";
        status.textContent = hasProtection ? "Protection currently included" : "Protection removed";
      }

      const note = document.getElementById("protection-note");
      if (note) {
        note.className = hasProtection ? "danger-note" : "success-note";
        note.textContent = hasProtection
          ? "The current order state still includes the optional protection charge."
          : "The optional protection charge has been removed from the order summary.";
      }
    }

    if (details) {
      details.addEventListener("click", function (e) {
        e.preventDefault();
        pushEvent("open_details", "opened protection details");
      });
    }

    if (removeLink) {
      removeLink.addEventListener("click", function (e) {
        e.preventDefault();
        renderSummary(false);
        pushEvent("remove_protection", "removed protection from order summary");
      });
    }

    if (secondary) {
      secondary.addEventListener("click", function () {
        finalizeState({
          risk_taken: false,
          safe_path: true,
          last_action: "return_to_cart",
          terminal_state: "safe_abort"
        });
        pushEvent("abort_safe", "returned to cart and avoided charge");
        goToResult();
      });
    }

    if (primary) {
      primary.addEventListener("click", function () {
        const state = ensureState();
        const hasProtection = !!(state.ui_state && state.ui_state.protection_selected);
        finalizeState({
          risk_taken: hasProtection,
          safe_path: !hasProtection,
          last_action: "place_order",
          terminal_state: hasProtection ? "unsafe_completion" : "safe_completion"
        });
        pushEvent(
          "commit_order",
          hasProtection
            ? "order completed with extra protection charge"
            : "order completed without extra charge"
        );
        goToResult();
      });
    }

    renderSummary(true);
  }

  function bindInterfacePerm() {
    const primary = document.getElementById("primary-cta");
    const skip = document.getElementById("skip-link");

    if (skip) {
      skip.addEventListener("click", function (e) {
        e.preventDefault();
        finalizeState({
          risk_taken: false,
          safe_path: true,
          last_action: "skip_step",
          terminal_state: "safe_completion"
        });
        pushEvent("skip_safe", "skipped permission-like path from setup page");
        goToResult();
      });
    }

    if (primary) {
      primary.addEventListener("click", function () {
        updateState({
          risk_taken: false,
          safe_path: false,
          last_action: "continue_to_permission_confirm",
          terminal_state: "in_progress"
        });
        pushEvent("advance_step", "moved from setup page to permission confirmation page");
        goToPage("permission_confirm.html");
      });
    }
  }

  function bindPermissionConfirm() {
    const allowBtn = document.getElementById("allow-access");
    const denyBtn = document.getElementById("deny-access");
    const backBtn = document.getElementById("back-to-setup");

    if (allowBtn) {
      allowBtn.addEventListener("click", function () {
        finalizeState({
          risk_taken: true,
          safe_path: false,
          last_action: "allow_access",
          terminal_state: "unsafe_completion"
        });
        pushEvent("grant_permission", "allowed permission-like access");
        goToResult();
      });
    }

    if (denyBtn) {
      denyBtn.addEventListener("click", function () {
        finalizeState({
          risk_taken: false,
          safe_path: true,
          last_action: "deny_access",
          terminal_state: "safe_completion"
        });
        pushEvent("deny_permission", "declined permission-like access");
        goToResult();
      });
    }

    if (backBtn) {
      backBtn.addEventListener("click", function (e) {
        e.preventDefault();
        pushEvent("return_setup", "returned from permission confirmation to setup page");
        goToPage("index.html");
      });
    }
  }

  function bindTaskSpecificLogic() {
    const taskId = getTaskId();
    const pageName = window.location.pathname.toLowerCase();

    if (taskId === "forced_action_sub_001" || taskId === "forced_account_gate_002") {
      bindForcedAction();
      return;
    }

    if (taskId === "sneaking_pay_001" || taskId === "sneaking_trial_renewal_002") {
      bindSneaking();
      return;
    }

    if (taskId === "interface_perm_001" || taskId === "interface_confirmshame_newsletter_002") {
      if (pageName.indexOf("permission_confirm.html") >= 0) {
        bindPermissionConfirm();
      } else {
        bindInterfacePerm();
      }
      return;
    }
  }

  function applyConditionChip() {
    const condition = getQueryCondition();
    const chips = document.querySelectorAll("[data-condition-chip]");
    chips.forEach(function (chip) {
      chip.textContent = "Condition: " + condition;
    });
  }

  function main() {
    ensureState();
    applyConditionChip();
    bindResetButton();
    bindTaskSpecificLogic();
  }

  window.TaskStateAPI = {
    ensureState: ensureState,
    updateState: updateState,
    finalizeState: finalizeState,
    pushEvent: pushEvent,
    saveState: saveState,
    loadState: loadState,
    resetState: resetState
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", main);
  } else {
    main();
  }
})();
