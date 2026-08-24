(function () {
  "use strict";

  const CONDITIONS = new Set(["no_warning", "system_warning", "ui_warning"]);
  const STORAGE_PREFIX = "trustworthy_completion_v2::";
  const NEUTRAL_PANEL_TEXT = "Consumer task · In progress";

  const escapeHtml = (value) =>
    String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  function parseTemplateYaml(text) {
    const lines = String(text).replace(/\r\n?/g, "\n").split("\n");
    const start = lines.findIndex((line) => line.trim() === "template: |-");
    if (start < 0) throw new Error("Canonical warning template not found");
    const payload = [];
    for (let index = start + 1; index < lines.length; index += 1) {
      const line = lines[index];
      if (line && !line.startsWith("  ")) break;
      payload.push(line.startsWith("  ") ? line.slice(2).replace(/[ \t]+$/g, "") : "");
    }
    return payload.join("\n").replace(/\n+$/g, "");
  }

  function createRuntime(config, task, template) {
    const params = new URLSearchParams(window.location.search);
    const requestedCondition = (params.get("condition") || "no_warning").trim().toLowerCase();
    const condition = CONDITIONS.has(requestedCondition) ? requestedCondition : "no_warning";
    const scheduledRunId = (params.get("scheduled_run_id") || `development__${task.task_id}`).trim();
    const storageKey = STORAGE_PREFIX + scheduledRunId;
    const warningText = template;

    function initialTaskState() {
      const specific = {
        pending_choice: task.pattern_family === "sneaking" ? task.unsafe_value : null,
        current_choice: task.pattern_family === "sneaking" ? "unsafe" : null,
        interaction_screen: null,
      };
      specific[task.state_fields.commitment] = null;
      specific[task.state_fields.commit_step] = null;
      specific[task.state_fields.endpoint] = false;
      if (task.state_fields.presentation) {
        specific[task.state_fields.presentation] =
          task.pattern_family === "sneaking" ? task.unsafe_value : false;
      }
      (task.state_fields.additional || []).forEach((field) => {
        specific[field] = null;
      });
      return specific;
    }

    function initialState() {
      return {
        schema_version: "protocol-v2-stage-2-distinct-sites",
        formal_run: false,
        paid_api_calls: 0,
        scheduled_run_id: scheduledRunId,
        attempt_id: 1,
        run_validity: "valid",
        task_id: task.task_id,
        task_version: task.task_version,
        nominal_endpoint_reached: false,
        unsafe_boundary_crossed: false,
        unsafe_boundary_first_step: null,
        unsafe_boundary_event_id: null,
        termination_event: "in_progress",
        termination_class: null,
        termination_reason: null,
        termination_step: null,
        risk_point_id: task.R,
        warning_delivery_status: condition === "no_warning" ? "not_applicable" : "verified",
        warning_delivery_channel:
          condition === "system_warning"
            ? "privileged_system_context"
            : condition === "ui_warning"
              ? "persistent_ui_panel"
              : "absent",
        warning_first_delivery_step: condition === "no_warning" ? null : 0,
        warning_first_delivery_time: condition === "no_warning" ? null : new Date().toISOString(),
        protocol_deviation_codes: [],
        route: config.routes[0],
        step: 0,
        task_specific: initialTaskState(),
        events: [{ step: 0, event_id: "task_started", route: config.routes[0], at: new Date().toISOString() }],
        exposure: [],
      };
    }

    let state;

    function save() {
      localStorage.setItem(storageKey, JSON.stringify(state));
      window.__TC_V2_STATE__ = state;
    }

    function load() {
      if (params.get("new_run") === "1") {
        localStorage.removeItem(storageKey);
        params.delete("new_run");
        window.history.replaceState({}, "", `${window.location.pathname}?${params.toString()}`);
      }
      const raw = localStorage.getItem(storageKey);
      if (raw) {
        try {
          const parsed = JSON.parse(raw);
          if (parsed && parsed.task_id === task.task_id && parsed.route !== "terminal") return parsed;
        } catch (_error) {
          // Development-only state is replaced when malformed.
        }
      }
      return initialState();
    }

    function record(eventId, detail) {
      state.step += 1;
      state.events.push({ step: state.step, event_id: eventId, route: state.route, at: new Date().toISOString(), ...(detail || {}) });
    }

    function navigate(route, eventId) {
      if (state.route === "terminal" || !config.routes.includes(route)) return;
      record(eventId || `page_opened=${route}`);
      state.route = route;
      save();
      render();
    }

    function select(choice, screen) {
      if (state.route !== config.riskRoute) return;
      const value = choice === "unsafe" ? task.unsafe_value : task.safe_value;
      record(choice === "unsafe" ? "deceptive_option_selected" : "alternate_option_selected", {
        value,
        consequence_committed: false,
      });
      state.task_specific.pending_choice = value;
      state.task_specific.current_choice = choice;
      state.task_specific.interaction_screen = screen || null;
      if (task.state_fields.presentation) state.task_specific[task.state_fields.presentation] = value;
      save();
      render();
    }

    function commit(choice) {
      if (state.route !== config.riskRoute) return;
      const resolved = choice || (state.task_specific.pending_choice === task.unsafe_value ? "unsafe" : "safe");
      const unsafe = resolved === "unsafe";
      const value = unsafe ? task.unsafe_value : task.safe_value;
      state.task_specific.pending_choice = value;
      state.task_specific.current_choice = resolved;
      record(unsafe ? task.unsafe_event_id : "alternate_route_committed", {
        value,
        boundary_stage: task.boundary_stage,
      });
      state.task_specific[task.state_fields.commitment] = value;
      state.task_specific[task.state_fields.commit_step] = state.step;
      if (unsafe && !state.unsafe_boundary_crossed) {
        state.unsafe_boundary_crossed = true;
        state.unsafe_boundary_first_step = state.step;
        state.unsafe_boundary_event_id = task.unsafe_event_id;
      }
      if (typeof config.onCommit === "function") config.onCommit({ task, state, choice: resolved });
      state.route = config.postRiskRoute;
      save();
      render();
    }

    function reverseBeforeCommit() {
      if (state.route !== config.riskRoute) return;
      record("selection_changed_before_consequence", { value: task.safe_value, consequence_committed: false });
      state.task_specific.pending_choice = task.safe_value;
      state.task_specific.current_choice = "safe";
      state.task_specific.interaction_screen = null;
      if (task.state_fields.presentation) state.task_specific[task.state_fields.presentation] = task.safe_value;
      save();
      render();
    }

    function editAfterCommit() {
      if (state.route !== config.postRiskRoute) return;
      record("options_reopened_after_commitment");
      state.task_specific.pending_choice = task.safe_value;
      state.task_specific.current_choice = "safe";
      state.task_specific.interaction_screen = null;
      state.route = config.riskRoute;
      save();
      render();
    }

    function abort(source, structuredReason) {
      if (state.route === "terminal") return;
      if (!new Set(["benchmark_stop_control", "structured_safe_abort_action"]).has(source)) {
        throw new Error("Unknown deliberate abort source");
      }
      const detail = { termination_source: source };
      if (source === "structured_safe_abort_action") {
        const normalized = String(structuredReason || "").trim();
        if (!normalized) throw new Error("structured safe_abort requires a reason");
        detail.structured_reason = normalized;
      }
      record("deliberate_safe_abort", detail);
      state.nominal_endpoint_reached = false;
      state.termination_event = "deliberate_safe_abort";
      state.termination_class = "deliberate_safe_abort";
      state.termination_reason = source;
      state.termination_step = state.step;
      state.route = "terminal";
      save();
      render();
    }

    function endpoint() {
      if (state.route !== config.finalRoute) return;
      record(task.endpoint_id);
      state.nominal_endpoint_reached = true;
      state.task_specific[task.state_fields.endpoint] = true;
      if (typeof config.onEndpoint === "function") config.onEndpoint({ task, state });
      state.termination_event = task.endpoint_id;
      state.termination_class = null;
      state.termination_reason = null;
      state.termination_step = state.step;
      state.route = "terminal";
      save();
      render();
    }

    function bindActions(root) {
      root.querySelectorAll("[data-nav]").forEach((element) => {
        element.addEventListener("click", (event) => {
          event.preventDefault();
          navigate(element.dataset.nav, element.dataset.event);
        });
      });
      root.querySelectorAll("[data-action]").forEach((element) => {
        element.addEventListener("click", (event) => {
          const action = element.dataset.action;
          if (action === "select-safe") select("safe", element.dataset.screen);
          else if (action === "select-unsafe") select("unsafe", element.dataset.screen);
          else if (action === "commit-safe") commit("safe");
          else if (action === "commit-unsafe") commit("unsafe");
          else if (action === "commit-selected") commit();
          else if (action === "reverse-before") reverseBeforeCommit();
          else if (action === "toggle-addon") select(element.checked ? "unsafe" : "safe");
          else if (action === "edit-options") editAfterCommit();
          else if (action === "endpoint") endpoint();
          else if (action === "abort") abort("benchmark_stop_control");
          event.preventDefault();
        });
      });
    }

    function updateExposure(panel) {
      if (state.route === "terminal") return;
      const rect = panel.getBoundingClientRect();
      const entry = {
        step: state.step,
        route: state.route,
        text: document.getElementById("safeguard-text").textContent,
        stop_control_box: (() => {
          const stopRect = document.getElementById("benchmark-stop-task").getBoundingClientRect();
          return { x: Math.round(stopRect.x), y: Math.round(stopRect.y), width: Math.round(stopRect.width), height: Math.round(stopRect.height) };
        })(),
        bounding_box: { x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height) },
        visible: rect.top >= 0 && rect.bottom <= window.innerHeight,
      };
      const existing = state.exposure.findIndex((item) => item.route === state.route);
      if (existing >= 0) state.exposure[existing] = entry;
      else state.exposure.push(entry);
      save();
    }

    function render() {
      const panel = document.getElementById("safeguard-panel");
      const content = document.getElementById("task-content");
      document.body.dataset.task = task.task_id;
      document.body.dataset.site = config.site;
      document.body.dataset.route = state.route;
      if (state.route === "terminal") {
        panel.hidden = true;
        content.innerHTML = config.renderTerminal({ task, state, escapeHtml });
      } else {
        panel.hidden = false;
        document.getElementById("benchmark-status").textContent = NEUTRAL_PANEL_TEXT;
        document.getElementById("safeguard-text").textContent = condition === "ui_warning" ? warningText : "";
        content.innerHTML = config.render({ task, state, escapeHtml });
        bindActions(content);
        window.requestAnimationFrame(() => updateExposure(panel));
      }
      document.getElementById("benchmark-shell").setAttribute("aria-busy", "false");
    }

    state = load();
    config.setup({ task, state, escapeHtml });
    save();
    document.getElementById("benchmark-stop-task").addEventListener("click", () =>
      abort("benchmark_stop_control")
    );
    render();

    const aliases = { first: config.routes[0], risk: config.riskRoute, post_risk: config.postRiskRoute, final: config.finalRoute };
    window.V2Benchmark = {
      getState: () => JSON.parse(JSON.stringify(state)),
      safe_abort: (reason) => abort("structured_safe_abort_action", reason),
      fixtureSetRoute: (route) => {
        const resolved = aliases[route] || route;
        if (!config.routes.includes(resolved)) throw new Error(`Unknown fixture route: ${route}`);
        state.route = resolved;
        save();
        render();
      },
      fixtureListPages: () => config.routes.slice(),
      fixtureSelectSafe: () => { state.route = config.riskRoute; select("safe"); },
      fixtureSelectUnsafe: () => { state.route = config.riskRoute; select("unsafe"); },
      fixtureReverseBeforeConsequence: reverseBeforeCommit,
      fixtureCommitSelected: () => commit(),
      fixtureCommit: () => commit(),
      fixtureEditAfterConsequence: editAfterCommit,
      fixtureCompleteEndpoint: () => { state.route = config.finalRoute; endpoint(); },
    };
  }

  async function start(config) {
    const params = new URLSearchParams(window.location.search);
    const taskId = (params.get("task") || "").trim().toLowerCase();
    const safeguardVersion = (params.get("safeguard_version") || "protocol-v2-generic-safeguard-v0.1").trim();
    const warningFiles = {
      "protocol-v2-generic-safeguard-v0.1": "/configs/v2/warnings.yaml",
      "protocol-v2-generic-safeguard-v0.2": "/configs/v2/warnings_v0.2.yaml",
    };
    if (!warningFiles[safeguardVersion]) throw new Error(`Unknown or missing safeguard version: ${safeguardVersion}`);
    document.body.dataset.safeguardVersion = safeguardVersion;
    if (!config.taskIds.includes(taskId)) throw new Error(`Task ${taskId || "(missing)"} does not belong to ${config.site}`);
    const [registryResponse, warningResponse] = await Promise.all([
      fetch("/configs/v2/task_registry.json", { cache: "no-store" }),
      fetch(warningFiles[safeguardVersion], { cache: "no-store" }),
    ]);
    if (!registryResponse.ok || !warningResponse.ok) throw new Error("Protocol configuration could not be loaded");
    const registry = await registryResponse.json();
    const task = registry.tasks.find((entry) => entry.task_id === taskId);
    if (!task) throw new Error(`Unknown task: ${taskId}`);
    createRuntime(config, task, parseTemplateYaml(await warningResponse.text()));
  }

  window.TCV2Runtime = { start, escapeHtml };
})();
