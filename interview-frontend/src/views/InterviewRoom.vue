<template>
  <main class="interview-room">
    <h1>Interview Coding Platform</h1>

    <p>
      Room: {{ roomId }} |
      Status: {{ isConnected ? "Connected" : "Disconnected" }}
      Users online: {{ usersCount }}
    </p>

    <LanguageSelector v-model="language" />

    <CodeEditor v-model="code" :language="monacoLanguage" />

    <TestCases v-model="testCases" />

    <button @click="runCode" :disabled="isRunning">
       {{ isRunning ? "Running..." : "Run Code" }}
    </button>

    <OutputBox :output="output" />
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { useRoute } from "vue-router"

import LanguageSelector from "../components/LanguageSelector.vue"
import CodeEditor from "../components/CodeEditor.vue"
import TestCases from "../components/TestCases.vue"
import OutputBox from "../components/OutputBox.vue"

const route = useRoute()
const roomId = route.params.roomId

const starterCode = {
  python: `print("Hello, World!")`,

  c: `#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}`,

  cpp: `#include <iostream>
using namespace std;

int main() {
    cout << "Hello, World!" << endl;
    return 0;
}`,

  java: `public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}`,
}

const monacoLanguageMap = {
  python: "python",
  c: "c",
  cpp: "cpp",
  java: "java",
}

const language = ref("python")
const code = ref(starterCode.python)
const testCases = ref([
  {
    input: "",
    expected_output: "",
  },
])
const output = ref("")
const socket = ref(null)
const isConnected = ref(false)
const usersCount = ref(0)
const isRunning = ref(false)

let isRemoteUpdate = false

const monacoLanguage = computed(() => {
  return monacoLanguageMap[language.value]
})

function sendSocketMessage(type, payload) {
  if (!socket.value || socket.value.readyState !== WebSocket.OPEN) {
    return
  }

  socket.value.send(
    JSON.stringify({
      type,
      payload,
    })
  )
}

onMounted(() => {
  socket.value = new WebSocket(
    `ws://127.0.0.1:8083/ws/interview/${roomId}/`
  )

  socket.value.onopen = () => {
    isConnected.value = true
    output.value = `Connected to interview room: ${roomId}`
  }

socket.value.onmessage = (event) => {
  const data = JSON.parse(event.data)

  isRemoteUpdate = true
  
  if (data.type === "presence_update") {
    usersCount.value = data.payload.users_count
  }
  if (data.type === "code_change") {
    code.value = data.payload.code
  }

  if (data.type === "language_change") {
    language.value = data.payload.language
  }

  if (data.type === "test_cases_change") {
  testCases.value = data.payload.test_cases
}

  if (data.type === "run_output") {
    output.value = data.payload.output
  }

   isRemoteUpdate = false
  }

  socket.value.onerror = () => {
    output.value = "WebSocket connection error."
  }

  socket.value.onclose = () => {
    isConnected.value = false
    output.value = "Disconnected from interview room."
  }
})

onBeforeUnmount(() => {
  if (socket.value) {
    socket.value.close()
  }
})

watch(code, (newCode) => {
  if (isRemoteUpdate) return

  sendSocketMessage("code_change", {
    code: newCode,
  })
})

watch(language, (newLanguage) => {
  if (isRemoteUpdate) return

  code.value = starterCode[newLanguage]
  output.value = ""

  sendSocketMessage("language_change", {
    language: newLanguage,
  })

  sendSocketMessage("code_change", {
    code: code.value,
  })
})

watch(
  testCases,
  (newTestCases) => {
    if (isRemoteUpdate) return

    sendSocketMessage("test_cases_change", {
      test_cases: newTestCases,
    })
  },
  { deep: true }
)

async function runCode() {
  if (isRunning.value) return

  isRunning.value = true

  const runningMessage = "Running code..."
  output.value = runningMessage

  sendSocketMessage("run_output", {
    output: runningMessage,
  })

  try {
    const response = await fetch("http://127.0.0.1:8083/api/submissions/run/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
  language: language.value,
  code: code.value,
  test_cases: testCases.value,
}),
    })

    const data = await response.json()

    const finalOutput = `Status: ${data.status}

Message:
${data.message}

Output:
${data.output}

Time: ${data.time || "N/A"}
Memory: ${data.memory || "N/A"} KB`

    output.value = finalOutput

    sendSocketMessage("run_output", {
      output: finalOutput,
    })
  } catch (error) {
    const errorOutput = `Error connecting to backend:

${error}`

    output.value = errorOutput

    sendSocketMessage("run_output", {
      output: errorOutput,
    })
  } finally {
    isRunning.value = false
  }
}
</script>

<style scoped>
.interview-room {
  min-height: 100vh;
  padding: 24px;
  background: #0f0f0f;
  color: white;
  font-family: Arial, sans-serif;
}

button {
  margin-top: 16px;
  padding: 10px 18px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
button:disabled {
  background: #555;
  cursor: not-allowed;
}
button:hover {
  background: #1d4ed8;
}
</style>