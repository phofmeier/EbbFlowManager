<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";
import DashboardChart from "./DashboardChart.vue";
import DashboardIcon from "./DashboardIcon.vue";
import GrowTargets from "./GrowTargets.vue";
import PumpClock from "./PumpClock.vue";
import ScheduleSettings from "./ScheduleSettings.vue";

const props = defineProps({
  controllerId: { type: Number, required: true },
  refreshToken: { type: Number, required: true },
});

const dashboard = ref(null);
const loading = ref(true);
const loadError = ref(false);
const editor = ref(null);
const saving = ref(false);
const saveError = ref("");
const localChange = ref(null);
const crops = ref([]);
const cropsUnavailable = ref(false);
const draftCrop = ref("");
const draftPhase = ref("");
const growSaving = ref(false);
const growError = ref("");
const lightFixtures = ref([]);
const fixtureCatalogError = ref(false);
const lightSaving = ref("");
const lightErrors = ref({ fixture: "", distance: "" });
const distanceDraft = ref(null);
const endpoint = `/api/controllers/${props.controllerId}`;
let request = null;

const lightInstallation = computed(
  () => dashboard.value?.grow_light_installation,
);
const fixtureName = computed(
  () =>
    lightFixtures.value.find(
      ({ id }) => id === lightInstallation.value?.grow_light_id,
    )?.name,
);
const canopyDistance = computed({
  get: () =>
    distanceDraft.value ?? lightInstallation.value?.canopy_distance_cm ?? "",
  set: (value) => {
    distanceDraft.value =
      value === lightInstallation.value?.canopy_distance_cm ? null : value;
    lightErrors.value.distance = "";
  },
});
const validDistanceChange = computed(
  () =>
    Number.isFinite(canopyDistance.value) &&
    canopyDistance.value > 0 &&
    canopyDistance.value !== lightInstallation.value?.canopy_distance_cm,
);

const phases = computed(() =>
  Object.entries(
    crops.value.find(({ id }) => id === draftCrop.value)?.phases ?? {},
  ),
);
const activePhase = computed(() => {
  const selection = dashboard.value?.grow_selection;
  if (!selection) return null;
  const crop = crops.value.find(({ id }) => id === selection.crop_id);
  return crop?.phases[selection.phase_id] ?? null;
});
const reservoirTargets = [
  ["ph", "pH", ""],
  ["ec_ms_cm", "EC", "mS/cm"],
  ["reservoir_temperature_c", "Water temperature", "°C"],
];
const climateTargets = [
  ["air_temperature_c", "Air temperature", "°C"],
  ["relative_humidity_pct", "Relative humidity", "%"],
];
const lightTargets = [
  ["ppfd_umol_m2_s", "Light intensity (PPFD)", "µmol/m²/s"],
  ["dli_mol_m2_day", "Daily light integral (DLI)", "mol/m²/day"],
];

async function loadCropProfiles(signal) {
  try {
    const response = await fetch("/api/crops", { signal, cache: "no-store" });
    if (!response.ok) throw new Error("Crop profiles unavailable");
    const catalog = await response.json();
    if (!signal.aborted) {
      crops.value = catalog;
      cropsUnavailable.value = false;
    }
  } catch {
    if (!signal.aborted) cropsUnavailable.value = true;
  }
}

async function loadLightFixtures(signal) {
  try {
    const response = await fetch("/api/grow-lights", {
      signal,
      cache: "no-store",
    });
    if (!response.ok) throw new Error("Grow lights unavailable");
    const fixtures = await response.json();
    if (!signal.aborted) {
      lightFixtures.value = fixtures;
      fixtureCatalogError.value = false;
    }
  } catch {
    if (!signal.aborted) fixtureCatalogError.value = true;
  }
}

async function loadDashboard() {
  request?.abort();
  const controller = new AbortController();
  request = controller;
  loading.value = true;
  loadError.value = false;
  const cropRequest = loadCropProfiles(controller.signal);
  const fixtureRequest = loadLightFixtures(controller.signal);
  try {
    const response = await fetch(`${endpoint}/dashboard`, {
      signal: controller.signal,
      cache: "no-store",
    });
    if (!response.ok) throw new Error("Controller dashboard unavailable");
    const data = await response.json();
    if (request === controller) {
      dashboard.value = data;
      if (!saving.value) localChange.value = null;
      if (!growSaving.value) {
        draftCrop.value = data.grow_selection?.crop_id ?? "";
        draftPhase.value = data.grow_selection?.phase_id ?? "";
      }
    }
  } catch {
    if (!controller.signal.aborted) loadError.value = true;
  } finally {
    await Promise.all([cropRequest, fixtureRequest]);
    if (request === controller) loading.value = false;
  }
}

watch(() => props.refreshToken, loadDashboard, { immediate: true });
onBeforeUnmount(() => request?.abort());

function changeCrop(event) {
  draftCrop.value = event.target.value;
  const selection = dashboard.value.grow_selection;
  draftPhase.value =
    selection?.crop_id === draftCrop.value ? selection.phase_id : "";
  growError.value = "";
}

async function changePhase(event) {
  draftPhase.value = event.target.value;
  const selection = dashboard.value.grow_selection;
  growSaving.value = true;
  growError.value = "";
  try {
    const response = await fetch(`${endpoint}/grow-selection`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        crop_id: draftCrop.value,
        phase_id: draftPhase.value,
      }),
    });
    if (!response.ok) throw new Error("Could not save the grow phase");
    dashboard.value.grow_selection = await response.json();
    await loadDashboard();
  } catch {
    draftPhase.value =
      selection?.crop_id === draftCrop.value ? selection.phase_id : "";
    growError.value = "Could not save the grow phase. Try again.";
  } finally {
    growSaving.value = false;
  }
}

function editSchedule(kind) {
  saveError.value = "";
  lightErrors.value.fixture = "";
  editor.value = { kind, revision: dashboard.value.schedule_revisions[kind] };
}

async function saveLightSetting(kind, update) {
  if (lightSaving.value) return;
  lightSaving.value = kind;
  lightErrors.value[kind] = "";
  try {
    const response = await fetch(`${endpoint}/grow-light-installation`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update),
    });
    if (!response.ok) throw new Error("Could not save the light settings");
    await loadDashboard();
    if (loadError.value) {
      lightErrors.value[kind] =
        "Saved. Refresh the controller to see the updated light settings.";
    } else if (kind === "distance") {
      distanceDraft.value = null;
    }
  } catch {
    lightErrors.value[kind] =
      kind === "distance"
        ? "Could not save the canopy distance. Try again."
        : "Could not save the fixture. Try again.";
  } finally {
    lightSaving.value = "";
  }
}

function saveCanopyDistance() {
  if (validDistanceChange.value) {
    saveLightSetting("distance", { canopy_distance_cm: canopyDistance.value });
  }
}

async function saveSchedule(data) {
  const { kind, revision } = editor.value;
  const section = kind === "pump" ? "pump_cycles" : "light";
  saving.value = true;
  saveError.value = "";
  localChange.value = { section, state: "pending" };
  try {
    const response = await fetch(`${endpoint}/${kind}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-Schedule-Revision": revision,
      },
      body: JSON.stringify(data),
    });
    const result = await response.json();
    if (!response.ok) {
      const detail = Array.isArray(result.detail)
        ? result.detail[0]?.msg
        : result.detail;
      localChange.value =
        response.status >= 500 ? { section, state: "unconfirmed" } : null;
      saveError.value = detail ?? "Could not send the schedule.";
      return;
    }

    localChange.value = { section, state: result.state };
    if (result.state === "applied" || result.state === "unchanged") {
      editor.value = null;
    } else {
      saveError.value =
        "The controller did not confirm the change. Check its connection and try again.";
    }
  } catch (error) {
    localChange.value = { section, state: "unconfirmed" };
    saveError.value = error.message;
  } finally {
    await loadDashboard();
    saving.value = false;
  }
}

const dateTime = new Intl.DateTimeFormat(undefined, {
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});
const clock = new Intl.DateTimeFormat(undefined, {
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});
const number = new Intl.NumberFormat(undefined, { maximumFractionDigits: 1 });
const dliNumber = new Intl.NumberFormat(undefined, {
  maximumFractionDigits: 2,
});

function timestamp(value) {
  const time = value ? Date.parse(value) : NaN;
  return Number.isFinite(time) ? dateTime.format(time) : "Unavailable";
}

function kibibytes(bytes) {
  return bytes == null ? "Unavailable" : `${number.format(bytes / 1024)} KiB`;
}

const wifiBars = computed(() => {
  const rssi = dashboard.value?.connection.rssi_dbm;
  return rssi == null
    ? 0
    : [-90, -80, -70, -60].filter((limit) => rssi >= limit).length;
});

const latestChange = computed(
  () => localChange.value ?? dashboard.value?.latest_change,
);
const changeLabel = computed(() => {
  if (!latestChange.value) return "";
  const { section, state } = latestChange.value;
  const label = section === "pump_cycles" ? "Pump" : "Grow light";
  const description = {
    pending: "Waiting for confirmation",
    applied: "Applied",
    unchanged: "Already matches the last report",
    unconfirmed: "Unable to confirm",
  }[state];
  return `${label}: ${description}`;
});

const historyRange = computed(() => {
  const end = Date.parse(dashboard.value.history_end);
  return [end - 86_400_000, end];
});
const historyTicks = computed(() => {
  const [start, end] = historyRange.value;
  return [0, 0.25, 0.5, 0.75, 1].map((fraction) =>
    clock.format(start + (end - start) * fraction),
  );
});

const ppfdPoints = computed(() => {
  const points = dashboard.value?.light?.points ?? [];
  if (!points.every(({ ppfd }) => Number.isFinite(ppfd?.ppfd_umol_m2_s))) {
    return [];
  }
  return points.map(({ minute, ppfd }) => ({
    x: minute,
    y: ppfd.ppfd_umol_m2_s,
  }));
});
const ppfdRange = computed(() => {
  if (!ppfdPoints.value.length) return undefined;
  const peak = Math.max(...ppfdPoints.value.map(({ y }) => y));
  return [0, Math.max(100, Math.ceil(peak / 100) * 100)];
});
const lightSeries = computed(() => {
  const series = [
    {
      label: "Scheduled output (%)",
      color: "#64e5a0",
      points: dashboard.value.light.points.map(
        ({ minute, output_percent }) => ({
          x: minute,
          y: output_percent,
        }),
      ),
    },
  ];
  if (ppfdPoints.value.length) {
    series.push({
      label: "Estimated PPFD (µmol/m²/s)",
      color: "#86b9ff",
      axis: "right",
      dash: "5 4",
      points: ppfdPoints.value,
    });
  }
  return series;
});

function historyPoints(samples, field, scale = 1) {
  return samples
    .filter(
      (sample) =>
        Number.isFinite(sample[field]) &&
        Number.isFinite(Date.parse(sample.ts)),
    )
    .map((sample) => ({ x: Date.parse(sample.ts), y: sample[field] / scale }));
}

const reservoirSeries = computed(() => [
  {
    label: "Distance to water",
    color: "#86b9ff",
    points: historyPoints(dashboard.value.reservoir.history, "distance_mm"),
  },
]);

const diagnosticSeries = computed(() => [
  {
    label: "Free heap",
    color: "#86b9ff",
    points: historyPoints(
      dashboard.value.diagnostics.history,
      "free_heap_size",
      1024,
    ),
  },
  {
    label: "Minimum free heap",
    color: "#a8d581",
    points: historyPoints(
      dashboard.value.diagnostics.history,
      "min_free_heap_size",
      1024,
    ),
  },
]);

const storage = computed(() => {
  const sample = dashboard.value.diagnostics.latest;
  if (!sample?.store_total_bytes || sample.store_used_bytes == null)
    return null;
  return { used: sample.store_used_bytes, total: sample.store_total_bytes };
});
</script>

<template>
  <Teleport to="#grow-profile-controls">
    <div v-if="dashboard" class="grow-controls">
      <label>
        <span>Crop</span>
        <select
          :value="draftCrop"
          :disabled="loading || growSaving || !crops.length"
          @change="changeCrop"
        >
          <option value="" disabled>Select crop</option>
          <option v-for="crop in crops" :key="crop.id" :value="crop.id">
            {{ crop.name }}
          </option>
        </select>
      </label>
      <label>
        <span>Grow phase</span>
        <select
          v-model="draftPhase"
          :disabled="loading || growSaving || !phases.length"
          @change="changePhase"
        >
          <option value="" disabled>Select phase</option>
          <option v-for="[id, phase] in phases" :key="id" :value="id">
            {{ phase.name }}
          </option>
        </select>
      </label>
      <p v-if="growError" class="grow-feedback grow-error" role="alert">
        {{ growError }}
      </p>
      <p
        v-else-if="cropsUnavailable"
        class="grow-feedback grow-error"
        role="alert"
      >
        Could not load crop profiles.
        <button type="button" @click="loadDashboard">Retry</button>
      </p>
      <p v-else-if="growSaving" class="grow-feedback" role="status">
        Saving grow phase…
      </p>
    </div>
  </Teleport>

  <p v-if="loadError" role="alert" class="dashboard-notice">
    {{
      dashboard
        ? "Refresh failed. Showing the last loaded dashboard."
        : "Could not load the controller dashboard."
    }}
    <button type="button" @click="loadDashboard">Retry</button>
  </p>
  <p v-else-if="loading && !dashboard" role="status" class="dashboard-notice">
    Loading controller dashboard…
  </p>

  <div v-if="dashboard" class="dashboard-grid">
    <section
      class="dashboard-card dashboard-identity"
      aria-labelledby="identity-heading"
    >
      <header class="card-header">
        <div class="card-title">
          <span class="area-icon"><DashboardIcon name="identity" /></span>
          <h2 id="identity-heading">Identity and connection</h2>
        </div>
        <div class="identity-status">
          <span v-if="dashboard.demo" class="sample-label">Sample data</span>
          <span class="board-id">Board {{ dashboard.id }}</span>
          <span
            class="connection-badge"
            :class="{ connected: dashboard.connection.connected }"
          >
            <span
              class="status-dot"
              :class="{ 'is-connected': dashboard.connection.connected }"
              aria-hidden="true"
            ></span>
            {{ dashboard.connection.connected ? "Connected" : "Disconnected" }}
          </span>
        </div>
      </header>

      <dl class="identity-metrics">
        <div>
          <dt>Wi-Fi signal</dt>
          <dd class="wifi-field">
            <span class="wifi-bars" aria-hidden="true">
              <i
                v-for="bar in 4"
                :key="bar"
                :class="{ filled: bar <= wifiBars }"
              ></i>
            </span>
            {{
              dashboard.connection.rssi_dbm == null
                ? "Unavailable"
                : dashboard.connection.rssi_dbm + " dBm"
            }}
          </dd>
        </div>
        <div>
          <dt>Firmware</dt>
          <dd>{{ dashboard.connection.firmware_version || "Unavailable" }}</dd>
        </div>
        <div>
          <dt>Last status received</dt>
          <dd>{{ timestamp(dashboard.connection.status_received_at) }}</dd>
        </div>
        <div>
          <dt>Last configuration received</dt>
          <dd>{{ timestamp(dashboard.connection.config_received_at) }}</dd>
        </div>
      </dl>
      <p
        v-if="changeLabel"
        class="change-result"
        :data-state="latestChange.state"
        role="status"
      >
        {{ changeLabel }}
      </p>
    </section>

    <section class="dashboard-card pump-card" aria-labelledby="pump-heading">
      <header class="card-header">
        <div class="card-title">
          <span class="area-icon"><DashboardIcon name="pump" /></span>
          <h2 id="pump-heading">Nutrition pump</h2>
        </div>
        <button
          class="card-settings"
          type="button"
          aria-label="Edit pump schedule"
          :title="
            dashboard.connection.connected
              ? 'Edit pump schedule'
              : 'Controller disconnected'
          "
          :disabled="!dashboard.connection.connected"
          @click="editSchedule('pump')"
        >
          <DashboardIcon name="settings" />
        </button>
      </header>
      <div v-if="dashboard.pump" class="pump-content">
        <PumpClock :start-times="dashboard.pump.start_times" />
        <dl class="pump-metrics">
          <div>
            <dt>Run duration</dt>
            <dd class="pump-duration">
              {{ dashboard.pump.duration_seconds }} <span>s</span>
            </dd>
          </div>
          <div>
            <dt>Daily starts</dt>
            <dd v-if="dashboard.pump.start_times.length" class="start-times">
              <span v-for="time in dashboard.pump.start_times" :key="time">{{
                time
              }}</span>
            </dd>
            <dd v-else class="empty-data">No scheduled runs</dd>
          </div>
        </dl>
      </div>
      <p v-else class="empty-data">Waiting for the pump configuration.</p>
    </section>

    <section class="dashboard-card light-card" aria-labelledby="light-heading">
      <header class="card-header">
        <div class="card-title">
          <span class="area-icon"><DashboardIcon name="light" /></span>
          <h2 id="light-heading">Grow light</h2>
        </div>
        <button
          class="card-settings"
          type="button"
          aria-label="Grow light settings"
          title="Grow light settings"
          :disabled="lightSaving === 'distance'"
          @click="editSchedule('light')"
        >
          <DashboardIcon name="settings" />
        </button>
      </header>
      <GrowTargets
        class="targets-with-history"
        :metrics="lightTargets"
        :phase="activePhase"
      />
      <div class="light-calibration">
        <form class="canopy-distance" @submit.prevent="saveCanopyDistance">
          <label>
            Canopy distance (cm)
            <input
              v-model.number="canopyDistance"
              type="number"
              min="0"
              step="any"
              required
              :disabled="Boolean(lightSaving)"
            />
          </label>
          <button
            type="submit"
            :disabled="!validDistanceChange || Boolean(lightSaving)"
          >
            {{ lightSaving === "distance" ? "Saving…" : "Save distance" }}
          </button>
        </form>
        <dl v-if="dashboard.light?.dli_mol_m2_day != null" class="light-dli">
          <dt>Scheduled DLI</dt>
          <dd>
            {{ dliNumber.format(dashboard.light.dli_mol_m2_day) }}
            <span>mol/m²/day</span>
          </dd>
        </dl>
      </div>
      <p
        v-if="lightErrors.distance"
        class="light-feedback grow-error"
        role="alert"
      >
        {{ lightErrors.distance }}
      </p>
      <p v-if="fixtureName" class="light-feedback">{{ fixtureName }}</p>
      <p v-if="!lightInstallation?.grow_light_id" class="light-feedback">
        Choose a fixture in Grow light settings to see PPFD and DLI.
      </p>
      <p
        v-else-if="lightInstallation.canopy_distance_cm == null"
        class="light-feedback"
      >
        Set the canopy distance to see PPFD and DLI.
      </p>
      <p
        v-else-if="dashboard.light?.dli_status === 'extrapolated'"
        class="light-feedback"
      >
        PPFD and DLI include estimates outside the fixture’s calibration range.
      </p>
      <p
        v-else-if="dashboard.light?.dli_status === 'unavailable'"
        class="light-feedback"
      >
        The fixture calibration could not estimate PPFD for the full schedule.
      </p>
      <template v-if="dashboard.light">
        <p
          v-if="dashboard.light.transition_reaches_midnight"
          class="light-feedback"
          role="alert"
        >
          Edit the schedule so every light transition finishes before midnight.
        </p>
        <template v-else>
          <p class="chart-caption">Controller time</p>
          <DashboardChart
            label="24-hour grow-light schedule"
            :series="lightSeries"
            :x-range="[0, 1440]"
            :x-labels="['00:00', '06:00', '12:00', '18:00', '24:00']"
            :y-range="[0, 100]"
            y-suffix="%"
            :right-y-range="ppfdRange"
            legend
          />
        </template>
        <ul
          v-if="dashboard.light.changes.length"
          class="light-times"
          aria-label="Scheduled light changes"
        >
          <li v-for="change in dashboard.light.changes" :key="change.time">
            {{ change.time }} <strong>{{ change.output_percent }}%</strong>
            <span
              v-if="Number.isFinite(change.ppfd?.ppfd_umol_m2_s)"
              class="scheduled-ppfd"
            >
              {{ number.format(change.ppfd.ppfd_umol_m2_s) }} µmol/m²/s
            </span>
          </li>
        </ul>
        <p v-else class="empty-data">Light off</p>
      </template>
      <p v-else class="empty-data">Waiting for the light configuration.</p>
    </section>

    <section
      class="dashboard-card climate-card"
      aria-labelledby="climate-heading"
    >
      <header class="card-header">
        <div class="card-title">
          <span class="area-icon"><DashboardIcon name="climate" /></span>
          <h2 id="climate-heading">Climate</h2>
        </div>
      </header>
      <GrowTargets :metrics="climateTargets" :phase="activePhase" />
    </section>

    <section
      class="dashboard-card reservoir-card"
      aria-labelledby="reservoir-heading"
    >
      <header class="card-header">
        <div class="card-title">
          <span class="area-icon"><DashboardIcon name="reservoir" /></span>
          <h2 id="reservoir-heading">Reservoir</h2>
        </div>
        <span v-if="reservoirSeries[0].points.length" class="card-context"
          >Last 24 hours</span
        >
      </header>
      <GrowTargets
        class="targets-with-history"
        :metrics="reservoirTargets"
        :phase="activePhase"
      />
      <div class="reservoir-content">
        <dl class="reservoir-reading">
          <div>
            <dt>Distance to water</dt>
            <dd
              v-if="dashboard.reservoir.latest?.distance_mm != null"
              class="reservoir-distance"
            >
              {{ dashboard.reservoir.latest.distance_mm }} <span>mm</span>
            </dd>
            <dd v-else class="empty-data">No reading available</dd>
          </div>
          <div v-if="dashboard.reservoir.latest?.ts">
            <dt>Reading time</dt>
            <dd>{{ timestamp(dashboard.reservoir.latest.ts) }}</dd>
          </div>
        </dl>
        <DashboardChart
          v-if="reservoirSeries[0].points.length"
          label="Distance to water in millimeters, last 24 hours"
          :series="reservoirSeries"
          :x-range="historyRange"
          :x-labels="historyTicks"
        />
        <p v-else class="empty-data">No readings in the last 24 hours.</p>
      </div>
    </section>

    <details class="dashboard-card diagnostics-card">
      <summary class="card-header">
        <div class="card-title">
          <span class="area-icon"><DashboardIcon name="diagnostics" /></span>
          <h2>Device diagnostics</h2>
        </div>
        <span class="diagnostics-chevron"
          ><DashboardIcon name="chevron"
        /></span>
      </summary>
      <div class="diagnostics-content">
        <dl class="diagnostics-metrics">
          <div>
            <dt>Free heap</dt>
            <dd>
              {{ kibibytes(dashboard.diagnostics.latest?.free_heap_size) }}
            </dd>
          </div>
          <div>
            <dt>Minimum free heap</dt>
            <dd>
              {{ kibibytes(dashboard.diagnostics.latest?.min_free_heap_size) }}
            </dd>
          </div>
          <div v-if="storage">
            <dt>Storage used</dt>
            <dd>
              {{ kibibytes(storage.used) }} / {{ kibibytes(storage.total) }}
            </dd>
            <meter
              :value="storage.used"
              :max="storage.total"
              aria-label="Storage used"
            ></meter>
          </div>
        </dl>
        <div>
          <p class="chart-caption">Heap · Last 24 hours</p>
          <DashboardChart
            v-if="diagnosticSeries.some((series) => series.points.length)"
            label="Free and minimum free heap in KiB, last 24 hours"
            :series="diagnosticSeries"
            :x-range="historyRange"
            :x-labels="historyTicks"
            legend
          />
          <p v-else class="empty-data">No heap samples in the last 24 hours.</p>
        </div>
      </div>
    </details>
  </div>

  <ScheduleSettings
    v-if="editor"
    :kind="editor.kind"
    :schedule="dashboard[editor.kind]"
    :saving="saving"
    :error="saveError"
    :schedule-enabled="dashboard.connection.connected"
    :fixtures="lightFixtures"
    :fixture-id="lightInstallation?.grow_light_id ?? ''"
    :fixture-catalog-error="fixtureCatalogError"
    :fixture-saving="lightSaving === 'fixture'"
    :fixture-error="lightErrors.fixture"
    :suggestion-url="`${endpoint}/light/suggestion`"
    :saved-distance="lightInstallation?.canopy_distance_cm ?? null"
    :distance-saving="lightSaving === 'distance'"
    :distance-error="lightErrors.distance"
    @close="editor = null"
    @save="saveSchedule"
    @save-fixture="saveLightSetting('fixture', { grow_light_id: $event })"
    @save-distance="
      saveLightSetting('distance', { canopy_distance_cm: $event })
    "
  />
</template>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(17rem, 0.9fr) minmax(0, 1.4fr);
  align-items: stretch;
  gap: 1rem;
}

.dashboard-card,
.dashboard-notice {
  min-width: 0;
  padding: 1.15rem 1.25rem;
  border: 1px solid var(--border);
  border-radius: 0.85rem;
  background: linear-gradient(135deg, #121c29, #0f151e 68%);
}

.dashboard-identity,
.diagnostics-card {
  grid-column: 1 / -1;
}

.grow-controls {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: end;
  gap: 0.3rem 0.6rem;
}

.grow-controls label {
  display: grid;
  gap: 0.2rem;
  min-width: 0;
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 650;
}

.grow-controls select {
  width: 100%;
  max-width: 13rem;
  min-height: 2rem;
  padding: 0.25rem 0.45rem;
  border: 1px solid #314159;
  border-radius: 0.4rem;
  background: #141f2d;
  color: inherit;
  font: inherit;
  font-size: 0.85rem;
}

.grow-controls select:not(:disabled) {
  color: #eaf0f9;
}

.grow-controls select:focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: 2px;
}

.grow-feedback {
  grid-column: 1 / -1;
  margin: 0;
  color: var(--muted);
  font-size: 0.75rem;
}

.grow-error {
  color: var(--red);
}

.grow-error button {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--blue);
  text-decoration: underline;
  cursor: pointer;
}

.targets-with-history {
  margin-bottom: 0.9rem;
}

.dashboard-notice {
  margin: 0 0 1rem;
  color: var(--muted);
}

.dashboard-notice button {
  margin-inline-start: 0.4rem;
  border: 0;
  background: transparent;
  color: var(--blue);
  cursor: pointer;
  font-weight: 650;
}

.card-header,
.card-title,
.identity-status,
.wifi-field {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.card-header {
  justify-content: space-between;
  min-height: 2.2rem;
  margin-bottom: 0.95rem;
}

.dashboard-identity .card-header {
  flex-wrap: wrap;
}

.card-title h2 {
  margin: 0;
  font-size: 1rem;
  font-weight: 690;
  letter-spacing: -0.02em;
}

.area-icon,
.card-settings {
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  flex: none;
  padding: 0;
  border: 1px solid #2c435f;
  border-radius: 0.55rem;
  background: #1a2d46;
  color: var(--blue);
}

.area-icon svg,
.card-settings svg,
.diagnostics-chevron svg {
  width: 1.05rem;
  height: 1.05rem;
}

.card-settings {
  border-color: #2a394e;
  background: #172332;
  color: #abbdd5;
  cursor: pointer;
}

.card-settings:hover:not(:disabled) {
  border-color: #5277a4;
  color: var(--blue);
}

.card-settings:disabled {
  opacity: 0.5;
  cursor: default;
}

.identity-status {
  flex-wrap: wrap;
  gap: 0.5rem;
}

.sample-label,
.board-id,
.connection-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.28rem 0.58rem;
  border: 1px solid #2d3a4d;
  border-radius: 0.4rem;
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 650;
  white-space: nowrap;
}

.sample-label {
  background: #19263a;
  color: #a8c6ed;
}

.board-id {
  font-variant-numeric: tabular-nums;
}

.connection-badge {
  border-color: #593440;
  background: #241821;
  color: var(--red);
}

.connection-badge.connected {
  border-color: #294a3d;
  background: #12261e;
  color: var(--green);
}

.identity-metrics,
.pump-metrics,
.reservoir-reading,
.diagnostics-metrics {
  display: grid;
  gap: 0.9rem 1rem;
  margin: 0;
}

.identity-metrics {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  padding-top: 0.95rem;
  border-top: 1px solid #263245;
}

dt,
.chart-caption,
.card-context,
.empty-data {
  margin: 0;
  color: var(--muted);
  font-size: 0.78rem;
}

dd {
  margin: 0.3rem 0 0;
  color: #e9f0fb;
  font-size: 0.95rem;
  font-weight: 620;
  overflow-wrap: anywhere;
  font-variant-numeric: tabular-nums;
}

.wifi-bars {
  display: inline-flex;
  align-items: end;
  flex: none;
  gap: 0.15rem;
  height: 0.85rem;
}

.wifi-bars i {
  display: block;
  width: 0.22rem;
  height: 25%;
  border-radius: 1px;
  background: #354558;
}

.wifi-bars i:nth-child(2) {
  height: 50%;
}
.wifi-bars i:nth-child(3) {
  height: 75%;
}
.wifi-bars i:nth-child(4) {
  height: 100%;
}
.wifi-bars i.filled {
  background: var(--green);
}

.change-result {
  margin: 0.8rem 0 0;
  color: var(--blue);
  font-size: 0.8rem;
}

.change-result[data-state="applied"] {
  color: var(--green);
}
.change-result[data-state="unconfirmed"] {
  color: var(--red);
}

.pump-content {
  display: grid;
  grid-template-columns: minmax(6rem, 1.1fr) minmax(0, 1fr);
  align-items: center;
  gap: 0.55rem;
}

.pump-duration,
.reservoir-distance {
  font-size: clamp(1.55rem, 2.4vw, 2.15rem);
  letter-spacing: -0.035em;
  line-height: 1.1;
}

.pump-duration span,
.reservoir-distance span {
  color: var(--muted);
  font-size: 0.48em;
  letter-spacing: 0;
}

.start-times,
.light-times {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  padding: 0;
  list-style: none;
}

.start-times span,
.light-times li {
  padding: 0.21rem 0.38rem;
  border: 1px solid #2b3b51;
  border-radius: 0.3rem;
  background: #141f2d;
  color: #b9cbe3;
  font-size: 0.7rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.light-card {
  --chart-color: var(--green);
}

.light-card .area-icon {
  border-color: #2d4e42;
  background: #173127;
  color: var(--green);
}

.light-calibration,
.canopy-distance {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  gap: 0.55rem;
}

.light-calibration {
  justify-content: space-between;
  gap: 0.75rem;
}

.canopy-distance label,
.light-dli dt {
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 650;
}

.canopy-distance label {
  display: grid;
  gap: 0.3rem;
}

.canopy-distance input,
.canopy-distance button {
  min-height: 2rem;
  padding: 0.25rem 0.5rem;
  border: 1px solid #34445c;
  border-radius: 0.4rem;
  background: #141f2d;
  color: #eaf0f9;
  font: inherit;
  font-size: 0.85rem;
}

.canopy-distance input {
  width: 8.25rem;
  font-variant-numeric: tabular-nums;
}

.canopy-distance button:not(:disabled) {
  cursor: pointer;
}

.canopy-distance button:disabled {
  opacity: 0.54;
}

.canopy-distance :is(input, button):focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: 2px;
}

.light-dli {
  margin: 0;
}

.light-dli dd {
  margin: 0.24rem 0 0;
  color: var(--green);
  font-size: 1.12rem;
  font-weight: 650;
  font-variant-numeric: tabular-nums;
}

.light-dli dd span,
.light-feedback {
  color: var(--muted);
  font-size: 0.76rem;
}

.light-feedback {
  margin: 0.55rem 0 0;
}

.light-feedback.grow-error {
  color: var(--red);
}

.chart-caption {
  margin-bottom: 0.45rem;
}

.light-times {
  margin: 0.55rem 0 0 2.35rem;
}

.light-times strong {
  margin-left: 0.18rem;
  color: var(--green);
  font-weight: 650;
}

.scheduled-ppfd {
  margin-left: 0.25rem;
  color: var(--blue);
}

.reservoir-content,
.diagnostics-content {
  display: grid;
  grid-template-columns: minmax(8.4rem, 0.32fr) minmax(0, 1fr);
  align-items: center;
  gap: 0.7rem 1.35rem;
}

.reservoir-content .chart {
  align-self: end;
}

.diagnostics-card {
  padding-block: 0;
}

.diagnostics-card summary {
  margin: 0;
  padding-block: 0.9rem;
  list-style: none;
  cursor: pointer;
}

.diagnostics-card summary::-webkit-details-marker {
  display: none;
}

.diagnostics-card summary:focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: 3px;
}

.diagnostics-chevron {
  display: flex;
  color: var(--muted);
}

.diagnostics-card[open] .diagnostics-chevron {
  transform: rotate(180deg);
}

.diagnostics-content {
  padding-block: 0.9rem 1.15rem;
  border-top: 1px solid #263245;
}

.diagnostics-metrics dd {
  font-size: 0.87rem;
}

meter {
  display: block;
  width: 100%;
  max-width: 13rem;
  height: 0.75rem;
  margin-top: 0.3rem;
  accent-color: var(--blue);
}

@media (max-width: 60rem) {
  .dashboard-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 36rem) {
  .dashboard-card {
    padding-inline: 0.9rem;
  }

  .identity-metrics,
  .reservoir-reading {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .reservoir-content,
  .diagnostics-content {
    grid-template-columns: minmax(0, 1fr);
    row-gap: 1rem;
  }
}
</style>
