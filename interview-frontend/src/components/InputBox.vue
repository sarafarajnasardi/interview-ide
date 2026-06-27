<template>
  <div class="input-box">
    <h3>Custom Input</h3>

    <textarea
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
      placeholder="Enter input here..."
    ></textarea>
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    required: true,
  },
})

defineEmits(["update:modelValue"])
</script>

<style scoped>
textarea {
  width: 100%;
  height: 100px;
  padding: 12px;
  background: #111;
  color: white;
  border: 1px solid #333;
  border-radius: 8px;
  font-family: monospace;
}
</style>