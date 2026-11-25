<script setup>
import { computed, onMounted, ref } from "vue";
import ControllerDashboard from "./ControllerDashboard.vue";

const controllers = ref([]);
const selectedId = ref(null);
const loading = ref(false);
const loadFailed = ref(false);
const dashboardRefresh = ref(0);

const selectedController = computed(() =>
  controllers.value.find((controller) => controller.id === selectedId.value),
);

function connectionLabel(connected) {
  return connected ? "Connected" : "Disconnected";
}

async function refreshControllers() {
  loading.value = true;
  loadFailed.value = false;

  try {
    const response = await fetch("/api/controllers", { cache: "no-store" });
    if (!response.ok) {
      throw new Error("Could not load controllers");
    }

    controllers.value = await response.json();
    if (!selectedController.value) {
      selectedId.value = controllers.value[0]?.id ?? null;
    }
  } catch {
    loadFailed.value = true;
  } finally {
    loading.value = false;
    dashboardRefresh.value += 1;
  }
}

onMounted(refreshControllers);
</script>

<template>
  <header class="topbar">
    <div class="brand">
      <img src="/lettuce.png" alt="" width="44" height="44" />
      <span>EbbFlowManager</span>
    </div>
    <div id="grow-profile-controls" class="topbar-controls"></div>
  </header>

  <div class="layout">
    <aside class="sidebar" aria-labelledby="controllers-heading">
      <div class="sidebar-header">
        <h2 id="controllers-heading">Controllers</h2>
        <button
          class="refresh-button"
          type="button"
          aria-label="Refresh controllers"
          title="Refresh controllers"
          :disabled="loading"
          @click="refreshControllers"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.7"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="M20 7v5h-5M4 17v-5h5" />
            <path
              d="M5.3 8a7.5 7.5 0 0 1 12.3-2.3L20 8m-16 8 2.4 2.3A7.5 7.5 0 0 0 18.7 16"
            />
          </svg>
        </button>
      </div>

      <p v-if="loadFailed" class="sidebar-message sidebar-error" role="alert">
        {{
          controllers.length
            ? "Refresh failed. Showing last loaded statuses."
            : "Could not load controllers."
        }}
      </p>
      <p v-else-if="!controllers.length" class="sidebar-message" role="status">
        {{ loading ? "Loading controllers…" : "No controllers available." }}
      </p>

      <ul
        v-if="controllers.length"
        class="controller-list"
        :aria-busy="loading"
      >
        <li v-for="controller in controllers" :key="controller.id">
          <button
            class="controller-button"
            type="button"
            :aria-current="controller.id === selectedId ? 'true' : undefined"
            aria-controls="dashboard"
            @click="selectedId = controller.id"
          >
            <span class="controller-icon" aria-hidden="true">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"
              >
                <rect x="3.5" y="5" width="17" height="14" rx="3" />
                <path d="M7.5 14.5h4m-4-5h2m3 0h4" />
              </svg>
            </span>
            <span class="controller-details">
              <span class="controller-name">{{ controller.name }}</span>
              <span class="controller-status">{{
                connectionLabel(controller.connected)
              }}</span>
            </span>
            <span
              class="status-dot"
              :class="{ 'is-connected': controller.connected }"
              aria-hidden="true"
            ></span>
          </button>
        </li>
      </ul>
    </aside>

    <main id="dashboard" class="dashboard" aria-labelledby="controller-heading">
      <div class="dashboard-header">
        <h1 id="controller-heading">
          {{ selectedController?.name ?? "Dashboard" }}
        </h1>
      </div>

      <ControllerDashboard
        v-if="selectedController"
        :key="selectedController.id"
        :controller-id="selectedController.id"
        :refresh-token="dashboardRefresh"
      />
      <p v-else class="dashboard-empty">
        Select a controller to open its dashboard.
      </p>
    </main>
  </div>
</template>

<style>
:root {
  color-scheme: dark;
  font-family: system-ui, sans-serif;
  color: #eaf0f9;
  background: #0a0d12;
  --surface: #0e131b;
  --border: #242e3d;
  --muted: #9baac0;
  --blue: #86b9ff;
  --green: #64e5a0;
  --red: #f47e8b;
  --topbar-height: 4.5rem;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

button {
  font: inherit;
}

button:focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: 2px;
}

.topbar {
  position: sticky;
  z-index: 1;
  top: 0;
  min-height: var(--topbar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.625rem clamp(1rem, 2vw, 2rem);
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  font-size: 1.2rem;
  font-weight: 740;
  letter-spacing: -0.04em;
}

.brand img {
  display: block;
  flex: none;
}

.topbar-controls {
  min-width: 0;
  max-width: 100%;
}

.layout {
  display: grid;
  grid-template-columns: 17rem minmax(0, 1fr);
  min-height: calc(100svh - var(--topbar-height));
}

.sidebar {
  position: sticky;
  top: var(--topbar-height);
  align-self: start;
  height: calc(100svh - var(--topbar-height));
  overflow: auto;
  padding: 1.5rem 1rem;
  border-right: 1px solid var(--border);
  background: var(--surface);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 0.25rem 0.75rem;
}

.sidebar-header h2 {
  margin: 0;
  color: var(--muted);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.refresh-button {
  display: grid;
  width: 2.125rem;
  height: 2.125rem;
  place-items: center;
  padding: 0;
  border: 1px solid var(--border);
  border-radius: 0.55rem;
  background: #141c28;
  color: var(--muted);
  cursor: pointer;
}

.refresh-button:hover:not(:disabled) {
  color: var(--blue);
  border-color: #405b7c;
}

.refresh-button:disabled {
  cursor: wait;
  opacity: 0.55;
}

.refresh-button svg,
.controller-icon svg {
  width: 1.125rem;
  height: 1.125rem;
}

.sidebar-message {
  margin: 0.875rem 0.25rem;
  color: var(--muted);
  font-size: 0.84rem;
  line-height: 1.5;
}

.sidebar-error {
  color: var(--red);
}

.controller-list {
  display: grid;
  gap: 0.5rem;
  padding: 0;
  margin: 0;
  list-style: none;
}

.controller-button {
  width: 100%;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.75rem;
  padding: 0.7rem 0.85rem 0.7rem 0.7rem;
  border: 1px solid var(--border);
  border-radius: 0.65rem;
  background: #111821;
  color: inherit;
  cursor: pointer;
  text-align: left;
}

.controller-button:hover {
  background: #172231;
  border-color: #40536c;
}

.controller-button[aria-current="true"] {
  background: #14243a;
  border-color: #42699a;
  box-shadow: inset 3px 0 var(--blue);
}

.controller-icon {
  display: grid;
  width: 2.125rem;
  height: 2.125rem;
  place-items: center;
  border: 1px solid #29384c;
  border-radius: 0.5rem;
  background: #192331;
  color: #acbad0;
}

.controller-button[aria-current="true"] .controller-icon {
  border-color: #344f74;
  background: #1d3554;
  color: var(--blue);
}

.controller-details {
  display: grid;
  gap: 0.175rem;
  min-width: 0;
  overflow-wrap: anywhere;
}

.controller-name {
  font-size: 0.9rem;
  font-weight: 650;
}

.controller-status {
  color: var(--muted);
  font-size: 0.75rem;
}

.status-dot {
  width: 0.48rem;
  height: 0.48rem;
  flex: none;
  border-radius: 50%;
  background: var(--red);
}

.status-dot.is-connected {
  background: var(--green);
  box-shadow: 0 0 0 3px #64e5a01f;
}

.dashboard {
  padding: clamp(1.25rem, 3.6vw, 3.5rem);
}

.dashboard-header {
  margin-bottom: 1.5rem;
}

.dashboard-header h1 {
  margin: 0;
  max-width: 100%;
  overflow-wrap: anywhere;
  font-size: clamp(1.75rem, 4vw, 2.8rem);
  font-weight: 720;
  letter-spacing: -0.055em;
  line-height: 1.08;
}

.dashboard-empty {
  margin: 0;
  color: var(--muted);
  font-size: 0.9rem;
  line-height: 1.45;
}

@media (max-width: 44rem) {
  .topbar {
    flex-wrap: wrap;
  }

  .layout {
    grid-template-columns: minmax(0, 1fr);
    align-content: start;
  }

  .sidebar {
    position: static;
    height: auto;
    max-height: 16rem;
    padding: 1rem;
    border-right: 0;
    border-bottom: 1px solid var(--border);
  }
}

@media (max-width: 26rem) {
  .topbar {
    gap: 0.5rem;
  }

  .brand {
    font-size: 1rem;
  }

  .brand img {
    width: 2.125rem;
    height: 2.125rem;
  }
}
</style>
