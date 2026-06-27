<template>
  <div class="output-box">
    <h3>Output</h3>

    <pre>{{ output || "Output will appear here..." }}</pre>
  </div>
</template>

<script setup>
defineProps({
  output: {
    type: String,
    required: true,
  },
})
</script>

<style scoped>
pre {
  min-height: 100px;
  padding: 12px;
  background: #111;
  color: #00ff88;
  border: 1px solid #333;
  border-radius: 8px;
  white-space: pre-wrap;
}
</style>