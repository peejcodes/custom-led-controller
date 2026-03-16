
(() => {
  const state = {
    snapshot: null,
    preview: null,
    activePage: "home",
    previewTimer: null,
    autosaveTimer: null,
    savePromise: null,
    patterns: [],
  };

  const refs = {};
  const qs = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const byId = (id) => document.getElementById(id);

  function cacheRefs() {
    [
      "statusText", "previewCanvas", "projectName", "activePatternName", "connectedCount", "totalLedCount",
      "heroPatternTitle", "heroMeta", "zoneCount", "segmentCount", "outputCount", "systemMode",
      "fps", "fpsValue", "speed", "speedValue", "brightness", "brightnessValue", "patternSelect",
      "patternSummaryTitle", "patternSummaryText", "homePalette", "paletteGrid", "controllers", "projectJson", "refreshProject", "saveProject",
      "resetProject", "applyJson", "addController", "addOutput", "addSegment", "addZone",
      "setupControllers", "setupOutputs", "setupSegments", "setupZones"
    ].forEach((id) => refs[id] = byId(id));
    refs.canvas = refs.previewCanvas;
    refs.ctx = refs.canvas?.getContext("2d") ?? null;
  }

  function safeText(id, value) {
    if (refs[id]) refs[id].textContent = value;
  }

  function setStatus(text) {
    safeText("statusText", text);
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  async function fetchJson(url, options = {}) {
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
      ...options,
    });
    if (!response.ok) {
      let message = `Request failed: ${response.status}`;
      try {
        const data = await response.json();
        message = data.detail || JSON.stringify(data);
      } catch {
        const text = await response.text();
        if (text) message = text;
      }
      throw new Error(message);
    }
    return response.json();
  }

  function rgbToHex(color) {
    const safe = color ?? { r: 0, g: 0, b: 0 };
    const toHex = (n) => Number(n ?? 0).toString(16).padStart(2, "0");
    return `#${toHex(safe.r)}${toHex(safe.g)}${toHex(safe.b)}`;
  }

  function hexToRgb(hex) {
    const normalized = String(hex || "#000000").replace("#", "").padEnd(6, "0").slice(0, 6);
    return {
      r: parseInt(normalized.slice(0, 2), 16),
      g: parseInt(normalized.slice(2, 4), 16),
      b: parseInt(normalized.slice(4, 6), 16),
    };
  }

  function titleCase(value) {
    const text = String(value || "");
    return text ? text[0].toUpperCase() + text.slice(1) : "—";
  }

  function slugify(value, fallback = "item") {
    return String(value || fallback)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 32) || fallback;
  }

  function uniqueId(prefix, existingIds) {
    let index = 1;
    let candidate = `${prefix}-${index}`;
    const used = new Set(existingIds || []);
    while (used.has(candidate)) {
      index += 1;
      candidate = `${prefix}-${index}`;
    }
    return candidate;
  }

  function setActivePage(pageName) {
    state.activePage = pageName;
    qs(".rail-button").forEach((button) => button.classList.toggle("active", button.dataset.page === pageName));
    qs(".page").forEach((page) => page.classList.toggle("active", page.dataset.page === pageName));
  }

  function projectCounts(project) {
    const controllers = Array.isArray(project?.controllers) ? project.controllers : [];
    const segments = Array.isArray(project?.segments) ? project.segments : [];
    const zones = Array.isArray(project?.zones) ? project.zones : [];

    const outputCount = controllers.reduce((sum, controller) => sum + ((controller.outputs || []).length), 0);
    const totalLeds = controllers.reduce(
      (sum, controller) => sum + (controller.outputs || []).reduce((acc, output) => acc + ((output.enabled ?? true) ? Number(output.led_count || 0) : 0), 0),
      0
    );

    return { totalLeds, outputCount, segmentCount: segments.length, zoneCount: zones.length };
  }

  function controllerMap(project) {
    return new Map((project.controllers || []).map((controller) => [controller.id, controller]));
  }

  function outputOptions(project) {
    const rows = [];
    (project.controllers || []).forEach((controller) => {
      (controller.outputs || []).forEach((output) => {
        rows.push({
          value: `${controller.id}::${output.id}`,
          label: `${controller.name} / ${output.name}`,
          controllerId: controller.id,
          outputId: output.id,
        });
      });
    });
    return rows;
  }

  function syncProjectEditor() {
    if (refs.projectJson && state.snapshot?.project) {
      refs.projectJson.value = JSON.stringify(state.snapshot.project, null, 2);
    }
  }

  function resizeCanvas() {
    if (!refs.canvas) return;
    const rect = refs.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const width = Math.max(300, Math.floor(rect.width * dpr));
    const height = Math.max(240, Math.floor(rect.height * dpr));
    if (refs.canvas.width !== width || refs.canvas.height !== height) {
      refs.canvas.width = width;
      refs.canvas.height = height;
    }
  }


  function activePatternDescriptor(patternId) {
    return (state.patterns || []).find((item) => item.id === patternId) || null;
  }

  function renderPatternSelector(project) {
    if (!refs.patternSelect) return;
    const selected = project?.playback?.pattern || "rainbow";
    const patterns = Array.isArray(state.patterns) && state.patterns.length
      ? state.patterns
      : [{ id: "rainbow", label: "Rainbow", summary: "Full-spectrum sweep", category: "Core" }];

    const groups = new Map();
    patterns.forEach((pattern) => {
      const category = pattern.category || "Patterns";
      if (!groups.has(category)) groups.set(category, []);
      groups.get(category).push(pattern);
    });

    refs.patternSelect.innerHTML = "";
    groups.forEach((items, category) => {
      const optgroup = document.createElement("optgroup");
      optgroup.label = category;
      items.forEach((pattern) => {
        const option = document.createElement("option");
        option.value = pattern.id;
        option.textContent = pattern.label;
        option.selected = pattern.id === selected;
        optgroup.appendChild(option);
      });
      refs.patternSelect.appendChild(optgroup);
    });

    const descriptor = activePatternDescriptor(selected);
    safeText("patternSummaryTitle", descriptor?.label || titleCase(selected));
    safeText("patternSummaryText", descriptor?.summary || "Pattern ready.");
  }

  async function loadPatterns() {
    state.patterns = await fetchJson("/api/patterns");
  }

  function updateHeader(snapshot) {
    const project = snapshot.project;
    const counts = projectCounts(project);
    const connected = (snapshot.controller_status || []).filter((item) => item.connected).length;
    const totalControllers = (project.controllers || []).length;
    const firstMode = project.controllers?.[0]?.mode || "mock";
    const descriptor = activePatternDescriptor(project.playback?.pattern || "");

    safeText("projectName", project.name || "Custom LED Controller");
    safeText("activePatternName", descriptor?.label || titleCase(project.playback?.pattern || "—"));
    safeText("connectedCount", `${connected} / ${totalControllers}`);
    safeText("totalLedCount", String(counts.totalLeds));
    safeText("heroPatternTitle", descriptor?.label || titleCase(project.playback?.pattern || "—"));
    safeText("heroMeta", `${totalControllers} controllers · ${counts.totalLeds} LEDs · ${counts.zoneCount} zones`);
    safeText("zoneCount", String(counts.zoneCount));
    safeText("segmentCount", String(counts.segmentCount));
    safeText("outputCount", String(counts.outputCount));
    safeText("systemMode", titleCase(firstMode));
  }

  async function persistProject(reason = "Saved.") {
    if (!state.snapshot?.project) return;
    if (state.savePromise) {
      return state.savePromise;
    }
    state.savePromise = fetchJson("/api/project", {
      method: "PUT",
      body: JSON.stringify(state.snapshot.project),
    }).then((snapshot) => {
      applyProjectToUI(snapshot);
      setStatus(reason);
      return snapshot;
    }).catch((error) => {
      setStatus(`Save failed: ${error.message}`);
      throw error;
    }).finally(() => {
      state.savePromise = null;
    });
    return state.savePromise;
  }

  function queueProjectSave(reason = "Updated.") {
    clearTimeout(state.autosaveTimer);
    state.autosaveTimer = window.setTimeout(() => persistProject(reason), 220);
  }

  function bindPlayback(project) {
    if (!project || !project.playback) return;

    const fps = refs.fps;
    const speed = refs.speed;
    const brightness = refs.brightness;

    if (fps) fps.value = clamp(Number(project.playback.fps ?? 30), 5, 60);
    if (speed) speed.value = clamp(Number(project.playback.speed ?? 1), 0.1, 10);
    if (brightness) brightness.value = clamp(Number(project.playback.brightness ?? 0.75), 0, 1);

    safeText("fpsValue", `${Number(project.playback.fps ?? 30)} FPS`);
    safeText("speedValue", `${Number(project.playback.speed ?? 1).toFixed(1)}x`);
    safeText("brightnessValue", Number(project.playback.brightness ?? 0.75).toFixed(2));

    renderPatternSelector(project);

    if (refs.patternSelect) {
      refs.patternSelect.onchange = () => {
        project.playback.pattern = refs.patternSelect.value;
        updateHeader(state.snapshot);
        renderPatternSelector(project);
        syncProjectEditor();
        queueProjectSave(`Selected ${activePatternDescriptor(project.playback.pattern)?.label || titleCase(project.playback.pattern)}.`);
      };
    }

    if (fps) {
      fps.oninput = () => {
        project.playback.fps = Number(fps.value);
        safeText("fpsValue", `${project.playback.fps} FPS`);
        syncProjectEditor();
        queueProjectSave("Frame rate updated.");
      };
    }

    if (speed) {
      speed.oninput = () => {
        project.playback.speed = Number(speed.value);
        safeText("speedValue", `${project.playback.speed.toFixed(1)}x`);
        syncProjectEditor();
        queueProjectSave("Speed updated.");
      };
    }

    if (brightness) {
      brightness.oninput = () => {
        project.playback.brightness = Number(brightness.value);
        safeText("brightnessValue", project.playback.brightness.toFixed(2));
        syncProjectEditor();
        queueProjectSave("Brightness updated.");
      };
    }
  }

  function renderHomePalette(project) {
    if (!refs.homePalette) return;
    refs.homePalette.innerHTML = "";
    (project.palette || []).forEach((slot) => {
      const chip = document.createElement("button");
      chip.className = "swatch-chip";
      chip.innerHTML = `<div class="swatch-color" style="background:${rgbToHex(slot.color)}"></div><strong>${slot.name || "Color"}</strong><span>${rgbToHex(slot.color).toUpperCase()}</span>`;
      chip.addEventListener("click", () => setActivePage("palette"));
      refs.homePalette.appendChild(chip);
    });
  }

  function renderPalette(project) {
    renderHomePalette(project);
    if (!refs.paletteGrid) return;
    refs.paletteGrid.innerHTML = "";
    (project.palette || []).forEach((slot) => {
      const card = document.createElement("div");
      card.className = "palette-card";
      card.innerHTML = `
        <div class="field-grid">
          <label class="form-field">
            <span>Slot name</span>
            <input type="text" value="${slot.name || ""}" />
          </label>
          <label class="form-field">
            <span>Color</span>
            <input type="color" value="${rgbToHex(slot.color)}" />
          </label>
        </div>
      `;
      const textInput = card.querySelector('input[type="text"]');
      const colorInput = card.querySelector('input[type="color"]');

      textInput?.addEventListener("input", () => {
        slot.name = textInput.value;
        renderHomePalette(project);
        syncProjectEditor();
        queueProjectSave("Palette updated.");
      });

      colorInput?.addEventListener("input", () => {
        slot.color = hexToRgb(colorInput.value);
        renderHomePalette(project);
        syncProjectEditor();
        queueProjectSave("Palette updated.");
      });

      refs.paletteGrid.appendChild(card);
    });
  }

  function renderControllers(snapshot) {
    if (!refs.controllers) return;
    refs.controllers.innerHTML = "";
    const statusById = new Map((snapshot.controller_status || []).map((item) => [item.controller_id, item]));

    (snapshot.project.controllers || []).forEach((controller) => {
      const status = statusById.get(controller.id);
      const card = document.createElement("div");
      card.className = "controller-card";

      const outputs = (controller.outputs || [])
        .map((output) => `<span class="output-pill">${output.name} · pin ${output.pin} · ${output.led_count} LEDs</span>`)
        .join("");

      card.innerHTML = `
        <div class="controller-head">
          <div>
            <h3>${controller.name}</h3>
            <div class="controller-meta">
              <div>${controller.id}</div>
              <div>${controller.mode} · ${controller.port} · ${controller.baudrate}</div>
            </div>
          </div>
          <div class="controller-actions">
            <button class="secondary" data-action="connect">Connect</button>
            <button class="secondary" data-action="disconnect">Disconnect</button>
          </div>
        </div>
        <div class="badge-row">
          <span class="badge ${status?.connected ? "good" : "offline"}">${status?.connected ? "Connected" : "Disconnected"}</span>
          <span class="badge">${(controller.outputs || []).length} outputs</span>
          <span class="badge">${(controller.outputs || []).reduce((sum, output) => sum + Number(output.led_count || 0), 0)} LEDs</span>
        </div>
        <div class="output-pill-row">${outputs || '<span class="badge offline">No outputs</span>'}</div>
      `;

      card.querySelector('[data-action="connect"]')?.addEventListener("click", async () => {
        try {
          setStatus(`Connecting ${controller.name}...`);
          await fetchJson(`/api/controllers/${controller.id}/connect`, { method: "POST" });
          await reloadSnapshot();
          setStatus(`Connected ${controller.name}.`);
        } catch (error) {
          setStatus(`Connect failed: ${error.message}`);
        }
      });

      card.querySelector('[data-action="disconnect"]')?.addEventListener("click", async () => {
        try {
          setStatus(`Disconnecting ${controller.name}...`);
          await fetchJson(`/api/controllers/${controller.id}/disconnect`, { method: "POST" });
          await reloadSnapshot();
          setStatus(`Disconnected ${controller.name}.`);
        } catch (error) {
          setStatus(`Disconnect failed: ${error.message}`);
        }
      });

      refs.controllers.appendChild(card);
    });
  }

  function renderSetup(project) {
    renderSetupControllers(project);
    renderSetupOutputs(project);
    renderSetupSegments(project);
    renderSetupZones(project);
  }

  function emptyState(text) {
    return `<div class="empty-state">${text}</div>`;
  }

  function renderSetupControllers(project) {
    const root = refs.setupControllers;
    if (!root) return;
    root.innerHTML = "";
    if (!(project.controllers || []).length) {
      root.innerHTML = emptyState("No controllers yet.");
      return;
    }

    project.controllers.forEach((controller) => {
      const card = document.createElement("div");
      card.className = "setup-card";
      card.innerHTML = `
        <div class="field-grid two">
          <label class="form-field"><span>Name</span><input data-field="name" type="text" value="${controller.name || ""}"></label>
          <label class="form-field"><span>ID</span><input data-field="id" type="text" value="${controller.id || ""}"></label>
          <label class="form-field"><span>Mode</span>
            <select data-field="mode">
              <option value="mock" ${controller.mode === "mock" ? "selected" : ""}>mock</option>
              <option value="serial" ${controller.mode === "serial" ? "selected" : ""}>serial</option>
            </select>
          </label>
          <label class="form-field"><span>Port</span><input data-field="port" type="text" value="${controller.port || ""}"></label>
          <label class="form-field"><span>Baudrate</span><input data-field="baudrate" type="number" min="9600" step="1" value="${controller.baudrate || 921600}"></label>
          <label class="form-check"><input data-field="enabled" type="checkbox" ${controller.enabled !== false ? "checked" : ""}> Enabled</label>
        </div>
        <div class="card-actions"><button class="danger" data-action="remove">Remove controller</button></div>
      `;

      card.querySelectorAll("[data-field]").forEach((input) => {
        input.addEventListener("input", () => {
          const field = input.dataset.field;
          controller[field] = input.type === "checkbox" ? input.checked : (input.type === "number" ? Number(input.value) : input.value);
          syncProjectEditor();
          queueProjectSave("Controller updated.");
        });
      });

      card.querySelector('[data-action="remove"]')?.addEventListener("click", () => {
        project.controllers = project.controllers.filter((item) => item !== controller);
        project.segments = project.segments.filter((segment) => segment.controller_id !== controller.id);
        project.zones = project.zones.map((zone) => ({ ...zone, segment_ids: (zone.segment_ids || []).filter((id) => project.segments.some((seg) => seg.id === id)) }));
        applyProjectToUI(state.snapshot);
        queueProjectSave("Controller removed.");
      });

      root.appendChild(card);
    });
  }

  function renderSetupOutputs(project) {
    const root = refs.setupOutputs;
    if (!root) return;
    root.innerHTML = "";
    const controllers = project.controllers || [];
    const rows = [];
    controllers.forEach((controller) => (controller.outputs || []).forEach((output) => rows.push({ controller, output })));

    if (!rows.length) {
      root.innerHTML = emptyState("No outputs yet.");
      return;
    }

    rows.forEach(({ controller, output }) => {
      const card = document.createElement("div");
      card.className = "setup-card";
      card.innerHTML = `
        <div class="field-grid two">
          <label class="form-field"><span>Controller</span>
            <select data-field="controllerId">
              ${(project.controllers || []).map((item) => `<option value="${item.id}" ${item.id === controller.id ? "selected" : ""}>${item.name}</option>`).join("")}
            </select>
          </label>
          <label class="form-field"><span>Name</span><input data-field="name" type="text" value="${output.name || ""}"></label>
          <label class="form-field"><span>ID</span><input data-field="id" type="text" value="${output.id || ""}"></label>
          <label class="form-field"><span>Pin</span><input data-field="pin" type="number" min="0" step="1" value="${output.pin}"></label>
          <label class="form-field"><span>LED count</span><input data-field="led_count" type="number" min="1" step="1" value="${output.led_count}"></label>
          <label class="form-check"><input data-field="enabled" type="checkbox" ${output.enabled !== false ? "checked" : ""}> Enabled</label>
        </div>
        <div class="card-actions"><button class="danger" data-action="remove">Remove output</button></div>
      `;

      card.querySelectorAll("[data-field]").forEach((input) => {
        input.addEventListener("input", () => {
          const field = input.dataset.field;
          if (field === "controllerId") {
            const nextController = (project.controllers || []).find((item) => item.id === input.value);
            if (nextController && nextController !== controller) {
              controller.outputs = (controller.outputs || []).filter((item) => item !== output);
              nextController.outputs = nextController.outputs || [];
              nextController.outputs.push(output);
              project.segments.forEach((segment) => {
                if (segment.output_id === output.id && segment.controller_id === controller.id) {
                  segment.controller_id = nextController.id;
                }
              });
              applyProjectToUI(state.snapshot);
              queueProjectSave("Output moved.");
            }
            return;
          }
          output[field] = input.type === "checkbox" ? input.checked : Number.isNaN(Number(input.value)) || input.type === "text" ? input.value : Number(input.value);
          syncProjectEditor();
          queueProjectSave("Output updated.");
        });
      });

      card.querySelector('[data-action="remove"]')?.addEventListener("click", () => {
        controller.outputs = (controller.outputs || []).filter((item) => item !== output);
        project.segments = project.segments.filter((segment) => !(segment.controller_id === controller.id && segment.output_id === output.id));
        project.zones = project.zones.map((zone) => ({ ...zone, segment_ids: (zone.segment_ids || []).filter((id) => project.segments.some((seg) => seg.id === id)) }));
        applyProjectToUI(state.snapshot);
        queueProjectSave("Output removed.");
      });

      root.appendChild(card);
    });
  }

  function renderSetupSegments(project) {
    const root = refs.setupSegments;
    if (!root) return;
    root.innerHTML = "";
    if (!(project.segments || []).length) {
      root.innerHTML = emptyState("No segments yet.");
      return;
    }

    const outputs = outputOptions(project);

    project.segments.forEach((segment) => {
      const card = document.createElement("div");
      card.className = "setup-card";
      const currentValue = `${segment.controller_id}::${segment.output_id}`;
      card.innerHTML = `
        <div class="field-grid two">
          <label class="form-field"><span>Name</span><input data-field="name" type="text" value="${segment.name || ""}"></label>
          <label class="form-field"><span>ID</span><input data-field="id" type="text" value="${segment.id || ""}"></label>
          <label class="form-field"><span>Output</span>
            <select data-field="outputRef">
              ${outputs.map((item) => `<option value="${item.value}" ${item.value === currentValue ? "selected" : ""}>${item.label}</option>`).join("")}
            </select>
          </label>
          <label class="form-field"><span>Start</span><input data-field="start" type="number" min="0" step="1" value="${segment.start}"></label>
          <label class="form-field"><span>Length</span><input data-field="length" type="number" min="1" step="1" value="${segment.length}"></label>
          <label class="form-check"><input data-field="reversed" type="checkbox" ${segment.reversed ? "checked" : ""}> Reversed</label>
        </div>
        <div class="card-actions"><button class="danger" data-action="remove">Remove segment</button></div>
      `;

      card.querySelectorAll("[data-field]").forEach((input) => {
        input.addEventListener("input", () => {
          const field = input.dataset.field;
          if (field === "outputRef") {
            const [controllerId, outputId] = String(input.value).split("::");
            segment.controller_id = controllerId;
            segment.output_id = outputId;
          } else {
            segment[field] = input.type === "checkbox" ? input.checked : (input.type === "number" ? Number(input.value) : input.value);
          }
          syncProjectEditor();
          queueProjectSave("Segment updated.");
        });
      });

      card.querySelector('[data-action="remove"]')?.addEventListener("click", () => {
        project.segments = project.segments.filter((item) => item !== segment);
        project.zones = project.zones.map((zone) => ({ ...zone, segment_ids: (zone.segment_ids || []).filter((id) => id !== segment.id) }));
        applyProjectToUI(state.snapshot);
        queueProjectSave("Segment removed.");
      });

      root.appendChild(card);
    });
  }

  function renderSetupZones(project) {
    const root = refs.setupZones;
    if (!root) return;
    root.innerHTML = "";
    if (!(project.zones || []).length) {
      root.innerHTML = emptyState("No zones yet.");
      return;
    }

    project.zones.forEach((zone) => {
      const card = document.createElement("div");
      card.className = "setup-card";
      card.innerHTML = `
        <div class="field-grid two">
          <label class="form-field"><span>Name</span><input data-field="name" type="text" value="${zone.name || ""}"></label>
          <label class="form-field"><span>ID</span><input data-field="id" type="text" value="${zone.id || ""}"></label>
        </div>
        <div class="segment-selector-grid">
          ${(project.segments || []).map((segment) => `
            <label class="segment-choice">
              <input data-segment-id="${segment.id}" type="checkbox" ${(zone.segment_ids || []).includes(segment.id) ? "checked" : ""}>
              <span>${segment.name}</span>
            </label>
          `).join("")}
        </div>
        <div class="card-actions"><button class="danger" data-action="remove">Remove zone</button></div>
      `;

      card.querySelectorAll("[data-field]").forEach((input) => {
        input.addEventListener("input", () => {
          zone[input.dataset.field] = input.value;
          syncProjectEditor();
          queueProjectSave("Zone updated.");
        });
      });

      card.querySelectorAll("[data-segment-id]").forEach((input) => {
        input.addEventListener("change", () => {
          const segId = input.dataset.segmentId;
          const set = new Set(zone.segment_ids || []);
          if (input.checked) set.add(segId); else set.delete(segId);
          zone.segment_ids = Array.from(set);
          syncProjectEditor();
          queueProjectSave("Zone updated.");
        });
      });

      card.querySelector('[data-action="remove"]')?.addEventListener("click", () => {
        project.zones = project.zones.filter((item) => item !== zone);
        applyProjectToUI(state.snapshot);
        queueProjectSave("Zone removed.");
      });

      root.appendChild(card);
    });
  }

  function bindSetupActions() {
    refs.addController?.addEventListener("click", () => {
      const project = state.snapshot?.project;
      if (!project) return;
      const controllerIds = (project.controllers || []).map((item) => item.id);
      const id = uniqueId("ctrl", controllerIds);
      project.controllers.push({
        id,
        name: `Controller ${project.controllers.length + 1}`,
        mode: "mock",
        port: "mock",
        baudrate: 921600,
        enabled: true,
        outputs: [],
      });
      applyProjectToUI(state.snapshot);
      queueProjectSave("Controller added.");
    });

    refs.addOutput?.addEventListener("click", () => {
      const project = state.snapshot?.project;
      if (!project || !(project.controllers || []).length) {
        setStatus("Add a controller first.");
        return;
      }
      const allOutputs = outputOptions(project).map((item) => item.outputId);
      const controller = project.controllers[0];
      controller.outputs.push({
        id: uniqueId("out", allOutputs),
        name: `Output ${controller.outputs.length + 1}`,
        pin: 2,
        led_count: 60,
        enabled: true,
      });
      applyProjectToUI(state.snapshot);
      queueProjectSave("Output added.");
    });

    refs.addSegment?.addEventListener("click", () => {
      const project = state.snapshot?.project;
      const outputs = outputOptions(project || {});
      if (!project || !outputs.length) {
        setStatus("Add an output first.");
        return;
      }
      const allIds = (project.segments || []).map((item) => item.id);
      const first = outputs[0];
      project.segments.push({
        id: uniqueId("seg", allIds),
        name: `Segment ${project.segments.length + 1}`,
        controller_id: first.controllerId,
        output_id: first.outputId,
        start: 0,
        length: 30,
        reversed: false,
      });
      applyProjectToUI(state.snapshot);
      queueProjectSave("Segment added.");
    });

    refs.addZone?.addEventListener("click", () => {
      const project = state.snapshot?.project;
      if (!project) return;
      const allIds = (project.zones || []).map((item) => item.id);
      project.zones.push({
        id: uniqueId("zone", allIds),
        name: `Zone ${project.zones.length + 1}`,
        segment_ids: [],
      });
      applyProjectToUI(state.snapshot);
      queueProjectSave("Zone added.");
    });
  }

  function applyProjectToUI(snapshot) {
    state.snapshot = snapshot;
    updateHeader(snapshot);
    bindPlayback(snapshot.project);
    renderPalette(snapshot.project);
    renderControllers(snapshot);
    renderSetup(snapshot.project);
    syncProjectEditor();
  }

  async function reloadSnapshot() {
    const snapshot = await fetchJson("/api/project");
    applyProjectToUI(snapshot);
  }

  async function saveProjectFromJsonEditor() {
    if (!refs.projectJson) return;
    try {
      const parsed = JSON.parse(refs.projectJson.value);
      const snapshot = await fetchJson("/api/project", {
        method: "PUT",
        body: JSON.stringify(parsed),
      });
      applyProjectToUI(snapshot);
      setStatus("Project JSON applied.");
    } catch (error) {
      setStatus(`Apply failed: ${error.message}`);
    }
  }

  async function resetProject() {
    try {
      const snapshot = await fetchJson("/api/project/reset", { method: "POST" });
      applyProjectToUI(snapshot);
      setStatus("Project reset to sample configuration.");
    } catch (error) {
      setStatus(`Reset failed: ${error.message}`);
    }
  }

  function roundRect(ctx, x, y, width, height, radius) {
    const r = Math.min(radius, width / 2, height / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + width, y, x + width, y + height, r);
    ctx.arcTo(x + width, y + height, x, y + height, r);
    ctx.arcTo(x, y + height, x, y, r);
    ctx.arcTo(x, y, x + width, y, r);
    ctx.closePath();
  }

  function drawPreview(preview) {
    if (!refs.canvas || !refs.ctx) return;
    resizeCanvas();

    const { canvas, ctx } = refs;
    const width = canvas.width;
    const height = canvas.height;
    const dpr = window.devicePixelRatio || 1;

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#08111b";
    ctx.fillRect(0, 0, width, height);

    const rows = [];
    (preview?.frames || []).forEach((controllerFrame) => {
      (controllerFrame.outputs || []).forEach((outputFrame) => {
        rows.push({ controllerId: controllerFrame.controller_id, ...outputFrame });
      });
    });

    if (!rows.length) {
      ctx.fillStyle = "#a8b5c8";
      ctx.font = `${14 * dpr}px sans-serif`;
      ctx.fillText("No preview data.", 20 * dpr, 28 * dpr);
      return;
    }

    const leftPad = 150 * dpr;
    const topPad = 20 * dpr;
    const rowGap = 12 * dpr;
    const rowHeight = Math.min(32 * dpr, Math.max(14 * dpr, (height - topPad * 2 - rowGap * (rows.length - 1)) / rows.length));
    const usableWidth = width - leftPad - 20 * dpr;

    rows.forEach((row, index) => {
      const y = topPad + index * (rowHeight + rowGap);
      ctx.fillStyle = "#96a4b7";
      ctx.font = `${12 * dpr}px sans-serif`;
      ctx.fillText(`${row.controllerId} / ${row.output_id}`, 16 * dpr, y + rowHeight * 0.68);

      const colors = row.colors || [];
      const ledWidth = usableWidth / Math.max(1, colors.length);

      roundRect(ctx, leftPad, y, usableWidth, rowHeight, 10 * dpr);
      ctx.save();
      ctx.clip();

      colors.forEach((color, colorIndex) => {
        ctx.fillStyle = `rgb(${color.r}, ${color.g}, ${color.b})`;
        ctx.fillRect(leftPad + colorIndex * ledWidth, y, Math.max(1, ledWidth), rowHeight);
      });

      ctx.restore();
      ctx.strokeStyle = "rgba(255,255,255,0.06)";
      ctx.lineWidth = 1 * dpr;
      roundRect(ctx, leftPad, y, usableWidth, rowHeight, 10 * dpr);
      ctx.stroke();
    });
  }

  async function tickPreview() {
    try {
      const preview = await fetchJson("/api/preview");
      state.preview = preview;
      drawPreview(preview);
    } catch (error) {
      console.error(error);
      setStatus(`Preview failed: ${error.message}`);
    } finally {
      clearTimeout(state.previewTimer);
      state.previewTimer = window.setTimeout(tickPreview, 220);
    }
  }

  function bindStaticActions() {
    qs(".rail-button").forEach((button) => {
      button.addEventListener("click", () => setActivePage(button.dataset.page));
    });

    qs("[data-goto]").forEach((button) => {
      button.addEventListener("click", () => setActivePage(button.dataset.goto));
    });

    refs.refreshProject?.addEventListener("click", async () => {
      try {
        await reloadSnapshot();
        setStatus("Reloaded project.");
      } catch (error) {
        setStatus(`Reload failed: ${error.message}`);
      }
    });

    refs.saveProject?.addEventListener("click", async () => {
      await persistProject("Project saved.");
    });

    refs.resetProject?.addEventListener("click", resetProject);
    refs.applyJson?.addEventListener("click", saveProjectFromJsonEditor);

    window.addEventListener("resize", () => drawPreview(state.preview));
  }

  async function init() {
    cacheRefs();
    bindStaticActions();
    bindSetupActions();
    resizeCanvas();
    setStatus("Loading…");

    try {
      await loadPatterns();
      await reloadSnapshot();
      setStatus("Loaded project.");
    } catch (error) {
      console.error(error);
      setStatus(`Initial load failed: ${error.message}`);
    }

    tickPreview();
  }

  window.addEventListener("DOMContentLoaded", init);
})();
