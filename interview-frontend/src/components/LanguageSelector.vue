<template>
  <div class="language-selector">
    <label for="language">Language:</label>

    <select
      id="language"
      :value="modelValue"
      @change="$emit('update:modelValue', $event.target.value)"
    >
      <option value="python">Python</option>
      <option value="c">C</option>
      <option value="cpp">C++</option>
      <option value="java">Java</option>
    </select>
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
.language-selector {
  margin-bottom: 16px;
}

select {
  margin-left: 8px;
  padding: 6px 10px;
}
</style>