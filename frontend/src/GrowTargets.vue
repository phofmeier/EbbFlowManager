<script setup>
defineProps({
  metrics: { type: Array, required: true },
  phase: { type: Object, default: null },
});

const number = new Intl.NumberFormat(undefined, { maximumFractionDigits: 3 });

function formatTarget({ min, max }) {
  return min === max
    ? number.format(min)
    : `${number.format(min)}–${number.format(max)}`;
}
</script>

<template>
  <div class="targets">
    <p class="targets-caption">
      {{ phase ? `${phase.name} targets` : "Targets" }}
    </p>
    <dl>
      <div v-for="[field, label, unit] in metrics" :key="field">
        <dt>{{ label }}</dt>
        <dd v-if="phase?.targets[field]">
          {{ formatTarget(phase.targets[field]) }}
          <span v-if="unit">{{ unit }}</span>
        </dd>
        <dd v-else class="unset">Not set</dd>
      </div>
    </dl>
  </div>
</template>

<style scoped>
.targets {
  padding: 0.75rem 0.85rem;
  border: 1px solid #2b3b51;
  border-radius: 0.55rem;
  background: #101a27;
}

.targets-caption {
  margin: 0 0 0.55rem;
  color: var(--blue);
  font-size: 0.72rem;
  font-weight: 650;
}

dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin: 0;
}

dt,
dd span,
.unset {
  color: var(--muted);
  font-size: 0.76rem;
}

dd {
  margin: 0.2rem 0 0;
  overflow-wrap: anywhere;
  font-size: 1.15rem;
  font-weight: 650;
  font-variant-numeric: tabular-nums;
}

dd span,
.unset {
  font-weight: 500;
}
</style>
