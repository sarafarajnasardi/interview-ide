<template>
  <div class="test-cases">
    <div class="header">
      <h3>Test Cases</h3>

      <button type="button" @click="addTestCase">
        + Add Test Case
      </button>
    </div>

    <div
      v-for="(testCase, index) in modelValue"
      :key="index"
      class="test-case-card"
    >
      <div class="test-case-header">
        <strong>Test Case {{ index + 1 }}</strong>

        <button
          v-if="modelValue.length > 1"
          type="button"
          class="remove-btn"
          @click="removeTestCase(index)"
        >
          Remove
        </button>
      </div>

      <label>Input</label>
      <textarea
        :value="testCase.input"
        placeholder="Enter input for this test case..."
        @input="updateTestCase(index, 'input', $event.target.value)"
      ></textarea>

      <label>Expected Output</label>
      <textarea
        :value="testCase.expected_output"
        placeholder="Enter expected output..."
        @input="updateTestCase(index, 'expected_output', $event.target.value)"
      ></textarea>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(["update:modelValue"])

function updateTestCase(index, field, value) {
  const updatedTestCases = props.modelValue.map((testCase, currentIndex) => {
    if (currentIndex === index) {
      return {
        ...testCase,
        [field]: value,
      }
    }

    return testCase
  })

  emit("update:modelValue", updatedTestCases)
}

function addTestCase() {
  emit("update:modelValue", [
    ...props.modelValue,
    {
      input: "",
      expected_output: "",
    },
  ])
}

function removeTestCase(index) {
  const updatedTestCases = props.modelValue.filter((_, currentIndex) => {
    return currentIndex !== index
  })

  emit("update:modelValue", updatedTestCases)
}
</script>

<style scoped>
.test-cases {
  margin-top: 18px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header button {
  padding: 8px 12px;
  background: #16a34a;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.test-case-card {
  margin-top: 14px;
  padding: 16px;
  background: #181818;
  border: 1px solid #333;
  border-radius: 10px;
}

.test-case-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.remove-btn {
  padding: 6px 10px;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

label {
  display: block;
  margin: 10px 0 6px;
  color: #ddd;
}

textarea {
  width: 100%;
  min-height: 80px;
  padding: 12px;
  background: #111;
  color: white;
  border: 1px solid #333;
  border-radius: 8px;
  font-family: monospace;
  resize: vertical;
}
</style>