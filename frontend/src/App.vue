<template>
  <div id="app">
    <h1>Ebb Flow Manager Frontend (FastAPI + MQTT)</h1>
    <div>
      <button @click="fetchControllers" style="margin-bottom: 10px">
        Refresh Controller IDs
      </button>
      <div v-if="loading">Loading controller IDs...</div>
      <div v-else-if="controllerIds.length > 0">
        <h2>Controller IDs:</h2>
        <ul>
          <li v-for="id in controllerIds" :key="id">ID: {{ id }}</li>
        </ul>
      </div>
      <div v-else-if="!loading && controllerIds.length === 0">
        <p>No controller IDs available.</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      controllerIds: [],
      loading: false,
    };
  },
  async created() {
    await this.fetchControllers(); // Fetch on initialization
  },
  methods: {
    async fetchControllers() {
      this.loading = true;
      try {
        const response = await fetch("http://localhost:8001/controllers/");
        if (!response.ok) {
          throw new Error("Failed to fetch controller IDs");
        }
        const data = await response.json();
        this.controllerIds = data;
      } catch (error) {
        console.error("Error fetching controller IDs:", error);
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style>
/* Existing styles can remain here */
</style>
