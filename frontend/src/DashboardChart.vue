<script setup>
import { computed, useId } from "vue";

const props = defineProps({
  label: { type: String, required: true },
  series: { type: Array, required: true },
  xRange: { type: Array, required: true },
  xLabels: { type: Array, required: true },
  yRange: { type: Array, default: undefined },
  ySuffix: { type: String, default: "" },
  rightYRange: { type: Array, default: undefined },
  legend: { type: Boolean, default: false },
});

const gradientId = useId();
const yBounds = computed(() => {
  if (props.yRange) return props.yRange;
  const values = props.series.flatMap((series) =>
    series.points.map((point) => point.y),
  );
  const low = Math.min(...values);
  const high = Math.max(...values);
  const step = 10 ** Math.floor(Math.log10(Math.max(high - low, 1)));
  return [
    Math.floor(low / step) * step,
    Math.ceil(high / step) * step || step,
  ].map((value, index, bounds) =>
    index === 1 && value === bounds[0] ? value + step : value,
  );
});

function axisLabels([low, high], suffix = "") {
  return [high, (high + low) / 2, low].map(
    (value) => String(Math.round(value * 10) / 10) + suffix,
  );
}

const yLabels = computed(() => axisLabels(yBounds.value, props.ySuffix));
const rightYLabels = computed(() =>
  props.rightYRange ? axisLabels(props.rightYRange) : [],
);

function coords(point, bounds) {
  const [xMin, xMax] = props.xRange;
  const [yMin, yMax] = bounds;
  return [
    Number((((point.x - xMin) / (xMax - xMin)) * 500).toFixed(2)),
    Number((110 - ((point.y - yMin) / (yMax - yMin)) * 106).toFixed(2)),
  ];
}

const paths = computed(() =>
  props.series
    .filter(({ points }) => points.length)
    .map((series) => {
      const bounds =
        series.axis === "right" ? props.rightYRange : yBounds.value;
      const points = series.points.map((point) => coords(point, bounds));
      const line = points.map(([x, y]) => `${x},${y}`).join(" L");
      const [firstX, firstY] = points[0];
      const lastX = points.at(-1)[0];
      return {
        ...series,
        line: "M" + line,
        area: `M${line} L${lastX},110 L${firstX},110 Z`,
        firstX,
        firstY,
        single: points.length === 1,
      };
    }),
);
</script>

<template>
  <figure
    class="chart"
    :class="{ 'has-right-axis': rightYRange }"
    :aria-label="label"
  >
    <div class="chart-axis-y" aria-hidden="true">
      <span v-for="label in yLabels" :key="label">{{ label }}</span>
    </div>
    <svg
      class="chart-plot"
      viewBox="0 0 500 114"
      preserveAspectRatio="none"
      role="img"
      :aria-label="label"
    >
      <defs>
        <linearGradient
          :id="gradientId"
          x1="0"
          x2="0"
          y1="0"
          y2="1"
          gradientUnits="objectBoundingBox"
        >
          <stop offset="0%" stop-color="currentColor" stop-opacity="0.24" />
          <stop offset="100%" stop-color="currentColor" stop-opacity="0.025" />
        </linearGradient>
      </defs>
      <path
        class="chart-grid"
        d="M0 4h500M0 57h500M0 110h500M0 4v106M125 4v106M250 4v106M375 4v106M500 4v106"
        vector-effect="non-scaling-stroke"
      />
      <path
        v-if="paths.length === 1"
        :d="paths[0].area"
        :fill="'url(#' + gradientId + ')'"
      />
      <template v-for="line in paths" :key="line.label">
        <circle
          v-if="line.single"
          :cx="line.firstX"
          :cy="line.firstY"
          r="3"
          :fill="line.color"
        />
        <path
          v-else
          :d="line.line"
          :stroke="line.color"
          :stroke-dasharray="line.dash"
          class="chart-line"
          vector-effect="non-scaling-stroke"
        />
      </template>
    </svg>
    <div
      v-if="rightYRange"
      class="chart-axis-y chart-axis-right"
      aria-hidden="true"
    >
      <span v-for="label in rightYLabels" :key="label">{{ label }}</span>
    </div>
    <div class="chart-axis-x" aria-hidden="true">
      <span v-for="(tick, index) in xLabels" :key="index">{{ tick }}</span>
    </div>
    <figcaption v-if="legend" class="chart-legend">
      <span v-for="line in paths" :key="line.label">
        <i :style="{ backgroundColor: line.color }" aria-hidden="true"></i
        >{{ line.label }}
      </span>
    </figcaption>
  </figure>
</template>

<style scoped>
.chart {
  display: grid;
  grid-template-columns: max-content minmax(0, 1fr);
  gap: 0.35rem 0.65rem;
  margin: 0;
  color: var(--chart-color, var(--blue));
}

.chart.has-right-axis {
  grid-template-columns: max-content minmax(0, 1fr) max-content;
}

.chart-plot {
  display: block;
  width: 100%;
  height: 7.7rem;
  overflow: visible;
}

.chart-grid {
  fill: none;
  stroke: #233248;
  stroke-width: 1;
}

.chart-line {
  fill: none;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.chart-axis-x,
.chart-axis-y,
.chart-legend {
  color: var(--muted);
  font-size: 0.7rem;
  font-variant-numeric: tabular-nums;
}

.chart-axis-x,
.chart-legend {
  display: flex;
  grid-column: 2;
}

.chart-axis-x {
  justify-content: space-between;
  gap: 0.2rem;
}

.chart-axis-y {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-end;
}

.chart-axis-right {
  align-items: flex-start;
}

.chart-legend {
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
  padding-top: 0.45rem;
}

.chart-legend span {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.chart-legend i {
  width: 0.6rem;
  height: 0.2rem;
  border-radius: 1rem;
}

.has-right-axis .chart-legend {
  grid-column: 2 / -1;
}
</style>
