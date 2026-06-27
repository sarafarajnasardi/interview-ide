<template>
  <main class="home">
    <section class="card">
      <h1>Interview Coding Platform</h1>

      <p class="subtitle">
        Create or join a live coding interview room.
      </p>

      <button @click="createRoom">
        Create New Room
      </button>

      <div class="divider">
        or
      </div>

      <div class="join-box">
        <input
          v-model="roomId"
          type="text"
          placeholder="Enter room ID"
          @keyup.enter="joinRoom"
        />

        <button @click="joinRoom">
          Join Room
        </button>
      </div>

      <p v-if="error" class="error">
        {{ error }}
      </p>
    </section>
  </main>
</template>

<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"

const router = useRouter()

const roomId = ref("")
const error = ref("")

function createRoom() {
  const newRoomId = generateRoomId()

  router.push(`/interview/${newRoomId}`)
}

function joinRoom() {
  const cleanedRoomId = roomId.value.trim()

  if (!cleanedRoomId) {
    error.value = "Please enter a room ID."
    return
  }

  router.push(`/interview/${cleanedRoomId}`)
}

function generateRoomId() {
  return Math.random().toString(36).substring(2, 8)
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f0f0f;
  color: white;
  font-family: Arial, sans-serif;
}

.card {
  width: 100%;
  max-width: 460px;
  padding: 32px;
  background: #181818;
  border: 1px solid #333;
  border-radius: 16px;
  text-align: center;
}

h1 {
  margin-bottom: 12px;
}

.subtitle {
  color: #aaa;
  margin-bottom: 24px;
}

button {
  padding: 10px 18px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

button:hover {
  background: #1d4ed8;
}

.divider {
  margin: 24px 0;
  color: #777;
}

.join-box {
  display: flex;
  gap: 10px;
}

input {
  flex: 1;
  padding: 10px 12px;
  background: #111;
  color: white;
  border: 1px solid #333;
  border-radius: 8px;
  outline: none;
}

input:focus {
  border-color: #2563eb;
}

.error {
  margin-top: 16px;
  color: #f87171;
}
</style>