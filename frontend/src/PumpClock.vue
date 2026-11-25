<script setup>
import { computed } from "vue";

const props = defineProps({
  startTimes: { type: Array, required: true },
});

function point(hour, radius) {
  const angle = (hour * Math.PI) / 12 - Math.PI / 2;
  return { x: 90 + radius * Math.cos(angle), y: 90 + radius * Math.sin(angle) };
}

const ticks = Array.from({ length: 24 }, (_, hour) => ({
  outer: point(hour, 64),
  inner: point(hour, hour % 6 === 0 ? 56 : 60),
  major: hour % 6 === 0,
}));
const labels = [0, 6, 12, 18].map((hour) => ({
  ...point(hour, 77),
  text: String(hour).padStart(2, "0"),
}));
const markers = computed(() =>
  props.startTimes.map((time) => {
    const [hour, minute] = time.split(":").map(Number);
    return { ...point(hour + minute / 60, 49), time };
  }),
);
</script>

<template>
  <svg viewBox="0 0 180 180" class="pump-clock" aria-hidden="true">
    <circle class="clock-face" cx="90" cy="90" r="67" />
    <circle class="clock-track" cx="90" cy="90" r="49" />
    <line
      v-for="(tick, index) in ticks"
      :key="index"
      :class="{ major: tick.major }"
      :x1="tick.inner.x"
      :x2="tick.outer.x"
      :y1="tick.inner.y"
      :y2="tick.outer.y"
    />
    <text
      v-for="label in labels"
      :key="label.text"
      :x="label.x"
      :y="label.y"
      dy=".35em"
    >
      {{ label.text }}
    </text>
    <g v-for="marker in markers" :key="marker.time">
      <title>{{ marker.time }}</title>
      <circle :cx="marker.x" :cy="marker.y" r="7" class="clock-marker-halo" />
      <circle :cx="marker.x" :cy="marker.y" r="3.4" class="clock-marker" />
    </g>
    <text x="90" y="90" dy=".35em" class="clock-caption">24 h</text>
  </svg>
</template>

<style scoped>
.pump-clock {
  display: block;
  width: 100%;
  max-width: 13rem;
  flex: none;
  margin-inline: auto;
  overflow: visible;
}

.clock-face {
  fill: #101b2a;
  stroke: #2c405c;
}

.clock-track {
  fill: #101a27;
  stroke: #263b57;
  stroke-dasharray: 2 4;
}

line {
  stroke: #4c6483;
}

line.major {
  stroke: #8aa7cd;
  stroke-width: 1.5;
}

text {
  fill: #9baac0;
  font-size: 9px;
  text-anchor: middle;
  font-variant-numeric: tabular-nums;
}

.clock-caption {
  fill: #cadcf3;
  font-size: 14px;
  font-weight: 650;
}

.clock-marker-halo {
  fill: #3a80f6;
  opacity: 0.24;
}

.clock-marker {
  fill: #87baff;
}
</style>
