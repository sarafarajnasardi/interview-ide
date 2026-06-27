<template>
  <div class="editor-wrapper">
    <VueMonacoEditor
      :value="modelValue"
      :language="language"
      theme="vs-dark"
      width="100%"
      height="500px"
      :options="editorOptions"
      @change="handleChange"
    />
  </div>
</template>

<script setup>
import { VueMonacoEditor } from "@guolao/vue-monaco-editor"

defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  language: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(["update:modelValue"])

const editorOptions = {
  fontSize: 15,
  minimap: {
    enabled: false,
  },
  automaticLayout: true,
  scrollBeyondLastLine: false,

  padding: {
    top: 16,
    bottom: 16,
  },

  lineNumbersMinChars: 4,
  lineDecorationsWidth: 12,
}

function handleChange(value) {
  emit("update:modelValue", value || "")
}
</script>

<style scoped>
.editor-wrapper {
  width: 100%;
  height: 500px;
  border: 1px solid #333;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
}
</style>