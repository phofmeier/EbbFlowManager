<script setup>
import { computed, onBeforeUnmount, onMounted, ref, useId, watch } from "vue";
import DashboardIcon from "./DashboardIcon.vue";

const props = defineProps({
  kind: { type: String, required: true },
  schedule: { type: Object, default: null },
  saving: { type: Boolean, required: true },
  error: { type: String, default: "" },
  scheduleEnabled: { type: Boolean, default: true },
  fixtures: { type: Array, default: () => [] },
  fixtureId: { type: String, default: "" },
  fixtureCatalogError: { type: Boolean, default: false },
  fixtureSaving: { type: Boolean, default: false },
  fixtureError: { type: String, default: "" },
  suggestionUrl: { type: String, required: true },
  savedDistance: { type: Number, default: null },
  distanceSaving: { type: Boolean, default: false },
  distanceError: { type: String, default: "" },
});
const emit = defineEmits(["save", "save-fixture", "save-distance", "close"]);

const dialog = ref(null);
const scheduleFormId = useId();
const isPump = computed(() => props.kind === "pump");
const title = computed(() =>
  isPump.value ? "Edit pump schedule" : "Grow light settings",
);
const calculating = ref(false);
const savingAnything = computed(
  () =>
    props.saving ||
    props.fixtureSaving ||
    props.distanceSaving ||
    calculating.value,
);
const draftFixture = ref(props.fixtureId);
const targets = ref({
  canopy_distance_cm: props.savedDistance ?? "",
  max_ppfd_umol_m2_s: "",
  dli_mol_m2_day: "",
  rise_time_minutes: "",
});
const suggestion = ref(null);
const suggestionError = ref("");
const targetNumber = new Intl.NumberFormat(undefined, {
  maximumFractionDigits: 2,
});
const fixtureReady = computed(
  () => Boolean(props.fixtureId) && draftFixture.value === props.fixtureId,
);
const validDistance = computed(
  () =>
    Number.isFinite(targets.value.canopy_distance_cm) &&
    targets.value.canopy_distance_cm > 0,
);
const distanceChanged = computed(
  () =>
    validDistance.value &&
    targets.value.canopy_distance_cm !== props.savedDistance,
);
const canCalculate = computed(() => fixtureReady.value && validDistance.value);
watch(
  () => props.savedDistance,
  (distance) => {
    targets.value.canopy_distance_cm = distance ?? "";
  },
);
watch(
  () => props.fixtureId,
  (id) => {
    draftFixture.value = id;
    suggestion.value = null;
    suggestionError.value = "";
  },
);
const limit = computed(() => (isPump.value ? 24 : 10));
const duration = ref(props.schedule?.duration_seconds ?? 0);
const rowError = ref("");
let nextRowId = 0;
const rows = ref(
  isPump.value
    ? (props.schedule?.start_times ?? []).map((time) => ({
        key: nextRowId++,
        time,
      }))
    : (props.schedule?.changes ?? []).map((change) => ({
        key: nextRowId++,
        ...change,
        initialOutputPercent: change.output_percent,
      })),
);
watch(rows, () => (suggestion.value = null), { deep: true, flush: "sync" });

onMounted(() => dialog.value.showModal());
onBeforeUnmount(() => dialog.value?.close());

function addRow() {
  rows.value.push({
    key: nextRowId++,
    time: "",
    output_percent: 0,
    transition_minutes: 0,
  });
}

async function calculateSchedule() {
  if (savingAnything.value || !canCalculate.value) return;
  calculating.value = true;
  suggestionError.value = "";
  try {
    const response = await fetch(props.suggestionUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(targets.value),
    });
    const result = await response.json();
    if (!response.ok) {
      const detail = Array.isArray(result.detail)
        ? result.detail[0]?.msg
        : result.detail;
      throw new Error(detail ?? "Could not calculate the schedule.");
    }
    rows.value = result.schedule.changes.map((change) => ({
      key: nextRowId++,
      ...change,
    }));
    rowError.value = "";
    suggestion.value = result;
  } catch (error) {
    suggestionError.value = error.message;
  } finally {
    calculating.value = false;
  }
}

function submit() {
  if (savingAnything.value || !props.scheduleEnabled) return;
  rowError.value = "";
  const starts = rows.value.map(({ time }) => time);
  if (new Set(starts).size !== starts.length) {
    rowError.value = "Enter a different time for each row.";
    return;
  }

  emit(
    "save",
    isPump.value
      ? { duration_seconds: Number(duration.value), start_times: starts }
      : {
          changes: rows.value.map((row) => ({
            time: row.time,
            output_percent:
              row.output_percent === row.initialOutputPercent
                ? (row.output_percent_exact ?? Number(row.output_percent))
                : Number(row.output_percent),
            transition_minutes: Number(row.transition_minutes),
          })),
        },
  );
}
</script>

<template>
  <dialog
    ref="dialog"
    class="settings-dialog"
    aria-labelledby="settings-title"
    @close="emit('close')"
    @cancel="savingAnything && $event.preventDefault()"
  >
    <div class="settings-content">
      <header class="settings-header">
        <h2 id="settings-title">{{ title }}</h2>
        <button
          class="settings-icon-button"
          aria-label="Close settings"
          type="button"
          :disabled="savingAnything"
          @click="dialog.close()"
        >
          <DashboardIcon name="close" />
        </button>
      </header>

      <div class="settings-body">
        <form
          v-if="!isPump"
          class="fixture-settings"
          @submit.prevent="emit('save-fixture', draftFixture)"
        >
          <fieldset :disabled="savingAnything || !fixtures.length">
            <label>
              Light fixture
              <select v-model="draftFixture" required>
                <option value="" disabled>Select a fixture</option>
                <option
                  v-for="fixture in fixtures"
                  :key="fixture.id"
                  :value="fixture.id"
                >
                  {{ fixture.name }}
                </option>
              </select>
            </label>
            <button
              class="settings-secondary"
              type="submit"
              :disabled="!draftFixture || draftFixture === fixtureId"
            >
              {{ fixtureSaving ? "Saving…" : "Save fixture" }}
            </button>
          </fieldset>
          <p
            v-if="fixtureError || fixtureCatalogError"
            class="form-error"
            role="alert"
          >
            {{
              fixtureError ||
              "Could not load the fixture catalog. Refresh the controller to retry."
            }}
          </p>
        </form>

        <form
          v-if="!isPump"
          class="schedule-calculator"
          @submit.prevent="calculateSchedule"
          @input="suggestionError = ''"
        >
          <fieldset :disabled="savingAnything">
            <legend>Calculate from targets</legend>
            <div class="target-fields">
              <label>
                Canopy distance (cm)
                <input
                  v-model.number="targets.canopy_distance_cm"
                  type="number"
                  min="0"
                  step="any"
                  required
                />
              </label>
              <label>
                Max PPFD (µmol/m²/s)
                <input
                  v-model.number="targets.max_ppfd_umol_m2_s"
                  type="number"
                  min="0"
                  step="any"
                  required
                />
              </label>
              <label>
                DLI (mol/m²/day)
                <input
                  v-model.number="targets.dli_mol_m2_day"
                  type="number"
                  min="0"
                  step="any"
                  required
                />
              </label>
              <label>
                Rise time (min)
                <input
                  v-model.number="targets.rise_time_minutes"
                  type="number"
                  min="0"
                  max="255"
                  step="1"
                  required
                />
              </label>
            </div>
            <div class="calculator-actions">
              <button
                class="settings-secondary"
                type="submit"
                :disabled="!canCalculate"
              >
                {{ calculating ? "Calculating…" : "Calculate schedule" }}
              </button>
              <button
                class="settings-secondary"
                type="button"
                :disabled="!distanceChanged"
                @click="emit('save-distance', targets.canopy_distance_cm)"
              >
                {{ distanceSaving ? "Saving…" : "Save distance" }}
              </button>
            </div>
          </fieldset>
          <p v-if="!fixtureReady" class="calculator-feedback">
            Save a light fixture before calculating.
          </p>
          <p v-if="distanceChanged" class="calculator-feedback">
            Save distance to update the controller’s Grow light panel.
          </p>
          <p
            v-if="suggestionError || distanceError"
            class="form-error"
            role="alert"
          >
            {{ suggestionError || distanceError }}
          </p>
          <p v-if="suggestion" class="calculator-feedback" role="status">
            At {{ targetNumber.format(suggestion.canopy_distance_cm) }} cm,
            draft peak
            {{ targetNumber.format(suggestion.peak_ppfd_umol_m2_s) }} µmol/m²/s
            · DLI
            {{ targetNumber.format(suggestion.dli_mol_m2_day) }} mol/m²/day.
            <span v-if="suggestion.dli_status === 'extrapolated'">
              Includes extrapolated PPFD.
            </span>
          </p>
        </form>

        <form :id="scheduleFormId" @submit.prevent="submit">
          <p v-if="!scheduleEnabled" class="schedule-unavailable">
            Schedule saving is unavailable while the controller is disconnected.
          </p>
          <fieldset :disabled="savingAnything || !scheduleEnabled">
            <label v-if="isPump" class="settings-duration">
              Run duration (seconds)
              <input
                v-model.number="duration"
                type="number"
                min="0"
                max="65535"
                step="1"
                required
                autofocus
              />
            </label>

            <div class="schedule-fields">
              <div
                class="schedule-row"
                :class="{ 'is-light': !isPump }"
                v-for="(row, index) in rows"
                :key="row.key"
              >
                <label>
                  {{ isPump ? "Start time" : "Change time" }}
                  <input
                    v-model="row.time"
                    type="text"
                    autocomplete="off"
                    maxlength="5"
                    pattern="(?:[01][0-9]|2[0-3]):[0-5][0-9]"
                    placeholder="HH:mm"
                    title="24-hour time, for example 13:28"
                    required
                  />
                </label>
                <template v-if="!isPump">
                  <label>
                    Output (%)
                    <input
                      v-model.number="row.output_percent"
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      required
                    />
                  </label>
                  <label>
                    Transition (min)
                    <input
                      v-model.number="row.transition_minutes"
                      type="number"
                      min="0"
                      max="255"
                      step="1"
                      required
                    />
                  </label>
                </template>
                <button
                  class="settings-icon-button remove-time"
                  type="button"
                  :aria-label="'Remove time ' + (index + 1)"
                  @click="rows.splice(index, 1)"
                >
                  <DashboardIcon name="close" />
                </button>
              </div>
              <p v-if="!rows.length" class="empty-schedule">
                {{
                  isPump
                    ? "No scheduled pump runs."
                    : "The light is off with no scheduled changes."
                }}
              </p>
            </div>
            <button
              class="add-time"
              type="button"
              :disabled="rows.length >= limit"
              @click="addRow"
            >
              {{ isPump ? "+ Add start time" : "+ Add light change" }}
            </button>
          </fieldset>
          <p v-if="rowError || error" class="form-error" role="alert">
            {{ rowError || error }}
          </p>
        </form>
      </div>

      <footer class="settings-actions">
        <button
          class="settings-secondary"
          type="button"
          :disabled="savingAnything"
          @click="dialog.close()"
        >
          Cancel
        </button>
        <button
          class="settings-primary"
          type="submit"
          :form="scheduleFormId"
          :disabled="savingAnything || !scheduleEnabled"
        >
          {{ saving ? "Waiting for confirmation…" : "Save schedule" }}
        </button>
      </footer>
    </div>
  </dialog>
</template>

<style scoped>
.settings-dialog {
  width: min(34rem, calc(100% - 2rem));
  max-height: calc(100svh - 2rem);
  padding: 0;
  border: 1px solid #344a68;
  border-radius: 0.9rem;
  background: #111925;
  color: inherit;
  box-shadow: 0 1.25rem 4rem #0009;
}

.settings-dialog::backdrop {
  background: #050910b8;
}

.settings-content {
  display: flex;
  flex-direction: column;
  max-height: calc(100svh - 2.125rem);
}

.settings-header,
.settings-actions {
  display: flex;
  flex: none;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
}

.settings-header {
  border-bottom: 1px solid var(--border);
}

.settings-header h2 {
  margin: 0;
  font-size: 1.15rem;
}

.settings-body {
  min-height: 0;
  padding: 1rem 1.25rem;
  overflow-y: auto;
}

fieldset {
  display: grid;
  gap: 1rem;
  margin: 0;
  padding: 0;
  border: 0;
  min-width: 0;
}

label {
  display: grid;
  min-width: 0;
  gap: 0.4rem;
  color: var(--muted);
  font-size: 0.8rem;
  font-weight: 600;
}

.settings-duration {
  max-width: 12rem;
}

input,
select {
  width: 100%;
  min-width: 0;
  padding: 0.55rem 0.65rem;
  border: 1px solid #34445c;
  border-radius: 0.45rem;
  background: #0b121c;
  color: #eaf0f9;
  font: inherit;
  font-size: 1rem;
  font-variant-numeric: tabular-nums;
}

:is(input, select):focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: 2px;
}

.fixture-settings,
.schedule-calculator {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}

.fixture-settings fieldset {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 0.55rem;
}

.fixture-settings button {
  min-height: 2.45rem;
}

.schedule-calculator fieldset {
  gap: 0.6rem;
}

.schedule-calculator legend {
  padding: 0 0 0.55rem;
  color: #eaf0f9;
  font-size: 0.9rem;
  font-weight: 650;
}

.target-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: end;
  gap: 0.5rem;
}

.calculator-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.calculator-feedback {
  margin: 0.55rem 0 0;
  color: var(--muted);
  font-size: 0.82rem;
}

.schedule-unavailable {
  margin: 0 0 0.85rem;
  color: var(--muted);
  font-size: 0.85rem;
}

.schedule-fields {
  display: grid;
  gap: 0.8rem;
}

.schedule-row {
  display: grid;
  grid-template-columns: minmax(0, 10rem) auto;
  justify-content: start;
  align-items: end;
  gap: 0.5rem;
}

.schedule-row.is-light {
  grid-template-columns: repeat(3, minmax(0, 1fr)) auto;
}

.settings-icon-button,
.add-time,
.settings-secondary,
.settings-primary {
  padding: 0.55rem 0.75rem;
  border: 1px solid #34445c;
  border-radius: 0.5rem;
  background: #172232;
  color: #cbd9ea;
  font-size: 0.82rem;
  font-weight: 650;
  cursor: pointer;
}

.settings-icon-button {
  display: grid;
  place-items: center;
  width: 2.1rem;
  height: 2.1rem;
  padding: 0;
}

.settings-icon-button svg {
  width: 1rem;
  height: 1rem;
}

.remove-time {
  margin-bottom: 0.18rem;
}

.add-time {
  justify-self: start;
  color: var(--blue);
}

.settings-primary {
  border-color: #86b9ff;
  background: #86b9ff;
  color: #091424;
}

button:hover:not(:disabled) {
  filter: brightness(1.14);
}

button:disabled {
  opacity: 0.54;
  cursor: default;
}

.settings-actions {
  justify-content: flex-end;
  border-top: 1px solid var(--border);
}

.form-error,
.empty-schedule {
  margin: 0;
  color: var(--muted);
  font-size: 0.85rem;
}

.form-error {
  margin-top: 0.85rem;
  color: var(--red);
}

@media (max-width: 24rem) {
  .settings-header,
  .settings-body,
  .settings-actions {
    padding-inline: 0.8rem;
  }

  .schedule-row.is-light {
    gap: 0.35rem;
  }
}
</style>
