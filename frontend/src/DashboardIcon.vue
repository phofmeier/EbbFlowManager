<script setup>
defineProps({ name: { type: String, required: true } });
</script>

<template>
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.65"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <template v-if="name === 'identity'">
      <rect x="4" y="4" width="16" height="16" rx="3" />
      <path d="M8 9h8M8 13h3m4 0h1m-8 3h6" />
    </template>
    <template v-else-if="name === 'pump'">
      <circle cx="12" cy="12" r="8" />
      <path d="M12 8v4l3 2" />
    </template>
    <template v-else-if="name === 'light'">
      <circle cx="12" cy="12" r="4" />
      <path
        d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"
      />
    </template>
    <path
      v-else-if="name === 'reservoir'"
      d="M12 3C9 7 5.5 10.9 5.5 15a6.5 6.5 0 0 0 13 0C18.5 10.9 15 7 12 3Zm-3 12a3 3 0 0 0 3 3"
    />
    <path
      v-else-if="name === 'climate'"
      d="M10 14.5V5a2 2 0 0 1 4 0v9.5a4 4 0 1 1-4 0ZM12 17V9m5-2h3m-3 4h2"
    />
    <path v-else-if="name === 'diagnostics'" d="M3 12h4l3-7 4 14 3-7h4" />
    <template v-else-if="name === 'settings'">
      <path
        d="M10 3h4l.5 2.2 1.6.9 2.2-.7 2 3.5-1.7 1.5v1.9l1.7 1.5-2 3.5-2.2-.7-1.6.9-.5 2.2h-4l-.5-2.2-1.6-.9-2.2.7-2-3.5 1.7-1.5v-1.9L3.7 8.9l2-3.5 2.2.7 1.6-.9L10 3Z"
        transform="translate(0 1)"
      />
      <circle cx="12" cy="12.4" r="2.5" />
    </template>
    <path v-else-if="name === 'chevron'" d="m6 9 6 6 6-6" />
    <path v-else-if="name === 'close'" d="m6 6 12 12M6 18 18 6" />
  </svg>
</template>
