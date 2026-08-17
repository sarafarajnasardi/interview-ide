<template>
  <main class="interview-room">
    <header class="room-header">
      <div>
        <p class="eyebrow">Live interview</p>
        <h1>Room {{ roomId }}</h1>
      </div>

      <div class="room-meta">
        <span :class="['status-dot', { online: isConnected }]"></span>
        <span>{{ isConnected ? "Connected" : "Disconnected" }}</span>
        <span>{{ usersCount }} online</span>
      </div>
    </header>

    <section v-if="roomFull" class="room-blocked">
      <div class="room-blocked-icon" aria-hidden="true">!</div>
      <p class="eyebrow">Room full</p>
      <h2>Cannot join this interview room</h2>
      <p>
        This room already has two people connected. Ask someone to leave, then refresh this page to try again.
      </p>
    </section>

    <section v-else class="workspace">
      <aside class="call-panel">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">Video call</p>
            <h2>{{ callStatus }}</h2>
          </div>
        </div>

        <div class="video-grid">
          <div class="video-tile">
            <video
              ref="localVideo"
              :class="{ hidden: !hasLocalVideo }"
              autoplay
              muted
              playsinline
            ></video>
            <span class="video-label">You</span>
            <div v-if="!hasLocalVideo" class="video-placeholder">
              <span class="person-icon" aria-hidden="true"></span>
              <span>Camera off</span>
            </div>
          </div>

          <div class="video-tile">
            <video
              ref="remoteVideo"
              :class="{ hidden: !hasRemoteVideo }"
              autoplay
              playsinline
            ></video>
            <span class="video-label">Peer</span>
            <div v-if="!hasRemoteVideo" class="video-placeholder">
              <span class="person-icon" aria-hidden="true"></span>
              <span>{{ remotePlaceholderText }}</span>
            </div>
          </div>
        </div>

        <div class="call-controls">
          <button
            :class="['control-button', { active: wantsCamera }]"
            @click="toggleCamera"
            :disabled="isStartingMedia"
          >
            {{ wantsCamera ? "Camera On" : "Camera Off" }}
          </button>

          <button
            :class="['control-button', { active: wantsMic }]"
            @click="toggleMic"
            :disabled="isStartingMedia"
          >
            {{ wantsMic ? "Mic On" : "Mic Off" }}
          </button>
        </div>

        <p v-if="callError" class="call-error">{{ callError }}</p>
      </aside>

      <section class="coding-panel">
        <div class="toolbar">
          <LanguageSelector v-model="language" />

          <button class="run-button" @click="runCode" :disabled="isRunning">
            {{ isRunning ? "Running..." : "Run Code" }}
          </button>
        </div>

        <CodeEditor v-model="code" :language="monacoLanguage" />

        <div class="bottom-grid">
          <TestCases v-model="testCases" />
          <OutputBox :output="output" />
        </div>
      </section>
    </section>
  </main>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { useRoute } from "vue-router"

import LanguageSelector from "../components/LanguageSelector.vue"
import CodeEditor from "../components/CodeEditor.vue"
import TestCases from "../components/TestCases.vue"
import OutputBox from "../components/OutputBox.vue"

const route = useRoute()
const roomId = route.params.roomId
const clientId = createClientId()
const defaultBackendHost = `${window.location.hostname || "127.0.0.1"}:8083`
const backendHost = import.meta.env.VITE_BACKEND_HOST || defaultBackendHost
const httpProtocol = window.location.protocol === "https:" ? "https" : "http"
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || `${httpProtocol}://${backendHost}`
const heartbeatIntervalMs = 30000

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
const roomFull = ref(false)

const localVideo = ref(null)
const remoteVideo = ref(null)
const localStream = ref(null)
const remoteStream = ref(null)
const peerConnection = ref(null)
const isStartingMedia = ref(false)
const wantsCamera = ref(false)
const wantsMic = ref(false)
const hasRemoteVideo = ref(false)
const remoteWantsCamera = ref(false)
const callError = ref("")
const callState = ref("idle")

let isRemoteUpdate = false
let pendingIceCandidates = []
let remotePeerId = null
let videoTransceiver = null
let audioTransceiver = null
let hasAnsweredPeerReady = false
let makingOffer = false
let ignoreOffer = false
let isSettingRemoteAnswerPending = false
let heartbeatTimer = null

const monacoLanguage = computed(() => {
  return monacoLanguageMap[language.value]
})

const callStatus = computed(() => {
  if (usersCount.value < 2) return "Waiting for peer"
  if (callState.value === "connected") return "Connected"
  if (callState.value === "connecting") return "Connecting..."
  if (callState.value === "failed") return "Connection failed"
  if (localStream.value) return "Ready"
  return "Waiting"
})

const remotePlaceholderText = computed(() => {
  if (usersCount.value < 2) return "Waiting for peer"
  return remoteWantsCamera.value ? "Starting camera" : "Camera off"
})

const hasLocalVideo = computed(() => {
  return Boolean(localStream.value?.getVideoTracks().some((track) => track.readyState === "live"))
})

function getWebSocketUrl() {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws"
  const host = import.meta.env.VITE_WS_HOST || backendHost
  const params = new URLSearchParams({ clientId })

  return `${protocol}://${host}/ws/interview/${roomId}/?${params.toString()}`
}

function createClientId() {
  const storageKey = `interview-client-id:${roomId}`
  const storedClientId = getStoredClientId(storageKey)

  if (storedClientId) {
    return storedClientId
  }

  const browserCrypto = globalThis.crypto

  if (browserCrypto?.randomUUID) {
    const clientId = browserCrypto.randomUUID()
    setStoredClientId(storageKey, clientId)
    return clientId
  }

  const randomPart = browserCrypto?.getRandomValues
    ? Array.from(browserCrypto.getRandomValues(new Uint32Array(2)), (value) => value.toString(16)).join("")
    : Math.random().toString(16).slice(2)

  const clientId = `${Date.now().toString(16)}-${randomPart}`
  setStoredClientId(storageKey, clientId)
  return clientId
}

function getStoredClientId(storageKey) {
  try {
    return window.sessionStorage?.getItem(storageKey)
  } catch {
    return null
  }
}

function setStoredClientId(storageKey, value) {
  try {
    window.sessionStorage?.setItem(storageKey, value)
  } catch {
    // Storage can be unavailable in private or restricted browser contexts.
  }
}

function sendSocketMessage(type, payload = {}) {
  if (!socket.value || socket.value.readyState !== WebSocket.OPEN) {
    return
  }

  socket.value.send(
    JSON.stringify({
      type,
      payload: {
        ...payload,
        senderId: clientId,
      },
    })
  )
}

function isOwnMessage(payload = {}) {
  return payload.senderId === clientId
}

function isForThisPeer(payload = {}) {
  return !payload.targetId || payload.targetId === clientId
}

onMounted(() => {
  socket.value = new WebSocket(getWebSocketUrl())

  socket.value.onopen = () => {
    isConnected.value = true
    roomFull.value = false
    output.value = `Connected to interview room: ${roomId}`
    announcePeerReady()
    startHeartbeat()
  }

  socket.value.onmessage = async (event) => {
    const data = JSON.parse(event.data)
    const payload = data.payload || {}

    if (data.type === "room_full") {
      showRoomFull(payload.message)
      return
    }

    if (data.type === "presence_update") {
      usersCount.value = payload.users_count

      if (usersCount.value < 2) {
        closePeerConnection()
        callState.value = "idle"
        return
      }

      if (usersCount.value > 1) {
        announcePeerReady()
      }

      return
    }

    if (isOwnMessage(payload)) {
      return
    }

    if (!isForThisPeer(payload)) {
      return
    }

    if (data.type.startsWith("webrtc_")) {
      await handleSignalingMessage(data.type, payload)
      return
    }

    isRemoteUpdate = true

    try {
      if (data.type === "code_change") {
        code.value = payload.code
      }

      if (data.type === "language_change") {
        language.value = payload.language
      }

      if (data.type === "test_cases_change") {
        testCases.value = payload.test_cases
      }

      if (data.type === "run_output") {
        output.value = payload.output
      }

      await nextTick()
    } finally {
      isRemoteUpdate = false
    }
  }

  socket.value.onerror = () => {
    output.value = "WebSocket connection error."
  }

  socket.value.onclose = (event) => {
    isConnected.value = false
    stopHeartbeat()
    closePeerConnection()
    stopLocalStream()
    wantsCamera.value = false
    wantsMic.value = false
    callState.value = "idle"

    if (event.code === 4001 || roomFull.value) {
      showRoomFull()
      return
    }

    output.value = "Disconnected from interview room."
  }
})

onBeforeUnmount(() => {
  stopHeartbeat()
  closePeerConnection()
  stopLocalStream()

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

async function toggleCamera() {
  wantsCamera.value = !wantsCamera.value
  await refreshLocalMedia()
}

async function toggleMic() {
  wantsMic.value = !wantsMic.value
  await refreshLocalMedia()
}

async function refreshLocalMedia() {
  isStartingMedia.value = true
  callError.value = ""
  const previousStream = localStream.value

  try {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("Media devices are not available in this browser context.")
    }

    const { tracks, failures } = await getRequestedMediaTracks()

    localStream.value = tracks.length ? new MediaStream(tracks) : null
    attachLocalStream()

    if (failures.length) {
      callError.value = window.isSecureContext
        ? `Could not access ${failures.join(" and ")}. Check browser permissions or close other apps using it.`
        : "Camera and microphone need localhost or HTTPS."
    }

    if (remotePeerId || peerConnection.value) {
      createPeerConnection()
      await applyLocalMediaToPeer()
      await negotiateIfStable()
    }

    announcePeerReady()
  } catch (error) {
    callError.value = error.message || "Could not start camera or microphone."
    console.error(error)
  } finally {
    stopStream(previousStream)
    isStartingMedia.value = false
  }
}

function attachLocalStream() {
  if (localVideo.value) {
    localVideo.value.srcObject = localStream.value
  }
}

function stopLocalStream() {
  if (!localStream.value) return

  stopStream(localStream.value)
  localStream.value = null
  attachLocalStream()
}

function stopStream(stream) {
  stream?.getTracks().forEach((track) => track.stop())
}

function startHeartbeat() {
  stopHeartbeat()
  heartbeatTimer = window.setInterval(() => {
    sendSocketMessage("heartbeat")
  }, heartbeatIntervalMs)
}

function stopHeartbeat() {
  if (!heartbeatTimer) return

  window.clearInterval(heartbeatTimer)
  heartbeatTimer = null
}

function showRoomFull(message = "This interview room already has two users.") {
  roomFull.value = true
  output.value = message
  callError.value = "Cannot join this room because it already has two users."
}

async function getRequestedMediaTracks() {
  const tracks = []
  const failures = []

  if (!wantsCamera.value && !wantsMic.value) {
    return { tracks, failures }
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: wantsCamera.value,
      audio: wantsMic.value,
    })

    tracks.push(...stream.getTracks())
    return { tracks, failures }
  } catch (error) {
    console.error(error)
  }

  if (wantsCamera.value && wantsMic.value) {
    return getRequestedMediaTracksIndividually()
  }

  if (wantsCamera.value) {
    wantsCamera.value = false
    failures.push("camera")
  }

  if (wantsMic.value) {
    wantsMic.value = false
    failures.push("microphone")
  }

  return { tracks, failures }
}

async function getRequestedMediaTracksIndividually() {
  const tracks = []
  const failures = []

  try {
    const cameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    tracks.push(...cameraStream.getVideoTracks())
  } catch (error) {
    wantsCamera.value = false
    failures.push("camera")
    console.error(error)
  }

  try {
    const micStream = await navigator.mediaDevices.getUserMedia({ video: false, audio: true })
    tracks.push(...micStream.getAudioTracks())
  } catch (error) {
    wantsMic.value = false
    failures.push("microphone")
    console.error(error)
  }

  return { tracks, failures }
}

function announcePeerReady() {
  if (!isConnected.value) return

  sendSocketMessage("webrtc_ready", {
    wantsCamera: wantsCamera.value,
    wantsMic: wantsMic.value,
  })
}

function isPolitePeer() {
  return remotePeerId ? clientId > remotePeerId : true
}

function createPeerConnection() {
  if (peerConnection.value) {
    return peerConnection.value
  }

  const connection = new RTCPeerConnection({
    iceServers: [
      {
        urls: "stun:stun.l.google.com:19302",
      },
    ],
  })

  remoteStream.value = new MediaStream()
  hasRemoteVideo.value = false

  if (remoteVideo.value) {
    remoteVideo.value.srcObject = remoteStream.value
  }

  initializeTransceivers(connection)

  connection.onnegotiationneeded = async () => {
    await negotiateIfStable()
  }

  connection.ontrack = (event) => {
    const existingTrack = remoteStream.value.getTracks().find((track) => track.id === event.track.id)

    if (!existingTrack) {
      remoteStream.value.addTrack(event.track)
    }

    if (event.track.kind === "video") {
      event.track.onunmute = updateRemoteVideoState
      event.track.onmute = updateRemoteVideoState
      event.track.onended = updateRemoteVideoState
    }

    if (remoteVideo.value) {
      remoteVideo.value.play().catch(() => {})
    }

    updateRemoteVideoState()
  }

  connection.onicecandidate = (event) => {
    if (event.candidate) {
      sendSocketMessage("webrtc_ice_candidate", {
        targetId: remotePeerId,
        candidate: event.candidate,
      })
    }
  }

  connection.onconnectionstatechange = () => {
    if (connection.connectionState === "connected") {
      callState.value = "connected"
      callError.value = ""
    }

    if (connection.connectionState === "failed") {
      callState.value = "failed"
      callError.value = "Peer connection failed. Check that both browsers can access camera/microphone over localhost or HTTPS."
    }

    if (["disconnected", "closed"].includes(connection.connectionState)) {
      callState.value = "waiting"
    }
  }

  connection.oniceconnectionstatechange = () => {
    if (["connected", "completed"].includes(connection.iceConnectionState)) {
      callState.value = "connected"
      callError.value = ""
    }

    if (connection.iceConnectionState === "failed") {
      callState.value = "failed"
      callError.value = "Could not establish the media connection. A TURN server may be required outside the same network."
    }

    if (connection.iceConnectionState === "disconnected") {
      callState.value = "waiting"
    }
  }

  connection.onicecandidateerror = (event) => {
    console.error(event.errorText || event.errorCode)
  }

  peerConnection.value = connection

  applyLocalMediaToPeer()

  return connection
}

async function applyLocalMediaToPeer() {
  if (!peerConnection.value) return

  const videoTrack = localStream.value?.getVideoTracks()[0] || null
  const audioTrack = localStream.value?.getAudioTracks()[0] || null

  if (videoTransceiver?.sender) {
    await videoTransceiver.sender.replaceTrack(videoTrack)
  }

  if (audioTransceiver?.sender) {
    await audioTransceiver.sender.replaceTrack(audioTrack)
  }
}

function initializeTransceivers(connection) {
  if (typeof connection.addTransceiver !== "function") {
    videoTransceiver = null
    audioTransceiver = null
    callError.value = "This browser does not support required WebRTC features for the call."
    console.warn("RTCPeerConnection.addTransceiver is not supported in this environment.")
    return
  }

  try {
    videoTransceiver = connection.addTransceiver("video", { direction: "sendrecv" })
  } catch (error) {
    videoTransceiver = null
    callError.value = "Unable to initialize video channel on this device or browser."
    console.error("Failed to create video transceiver:", error)
  }

  try {
    audioTransceiver = connection.addTransceiver("audio", { direction: "sendrecv" })
  } catch (error) {
    audioTransceiver = null
    callError.value = "Unable to initialize audio channel on this device or browser."
    console.error("Failed to create audio transceiver:", error)
  }
}

async function negotiateIfStable() {
  const connection = peerConnection.value

  if (!connection || !remotePeerId || makingOffer || connection.signalingState !== "stable") {
    return
  }

  try {
    makingOffer = true
    callState.value = "connecting"
    await applyLocalMediaToPeer()
    await connection.setLocalDescription()

    sendSocketMessage("webrtc_description", {
      targetId: remotePeerId,
      description: connection.localDescription,
    })
  } catch (error) {
    callError.value = "Could not negotiate the peer connection."
    console.error(error)
  } finally {
    makingOffer = false
  }
}

async function handleSignalingMessage(type, payload) {
  const isNewPeer = payload.senderId && remotePeerId !== payload.senderId

  if (payload.senderId) {
    remotePeerId = payload.senderId
  }

  if (type === "webrtc_ready") {
    remoteWantsCamera.value = Boolean(payload.wantsCamera)

    if (!remoteWantsCamera.value) {
      hasRemoteVideo.value = false
    } else {
      updateRemoteVideoState()
    }

    createPeerConnection()
    callState.value = "connecting"

    if (isNewPeer && !hasAnsweredPeerReady) {
      hasAnsweredPeerReady = true
      announcePeerReady()
    }

    await negotiateIfStable()

    return
  }

  if (type === "webrtc_description" && payload.description) {
    await handleDescription(payload.description)
    return
  }

  if (type === "webrtc_ice_candidate" && payload.candidate) {
    await addIceCandidate(payload.candidate)
  }
}

async function handleDescription(description) {
  const connection = createPeerConnection()
  const readyForOffer =
    !makingOffer
    && (connection.signalingState === "stable" || isSettingRemoteAnswerPending)
  const offerCollision = description.type === "offer" && !readyForOffer

  ignoreOffer = !isPolitePeer() && offerCollision

  if (ignoreOffer) {
    return
  }

  callState.value = "connecting"

  try {
    isSettingRemoteAnswerPending = description.type === "answer"
    await connection.setRemoteDescription(new RTCSessionDescription(description))
    isSettingRemoteAnswerPending = false

    if (description.type === "offer") {
      await addPendingIceCandidates()
      await applyLocalMediaToPeer()
      await connection.setLocalDescription()

      sendSocketMessage("webrtc_description", {
        targetId: remotePeerId,
        description: connection.localDescription,
      })
    }

    if (description.type === "answer") {
      await addPendingIceCandidates()
    }
  } catch (error) {
    callError.value = "Could not apply the peer connection update."
    console.error(error)
  } finally {
    isSettingRemoteAnswerPending = false
  }
}

async function addIceCandidate(candidate) {
  if (!peerConnection.value || !peerConnection.value.remoteDescription) {
    pendingIceCandidates.push(candidate)
    return
  }

  try {
    await peerConnection.value.addIceCandidate(new RTCIceCandidate(candidate))
  } catch (error) {
    if (ignoreOffer) {
      return
    }

    callError.value = "Could not add a peer network candidate."
    console.error(error)
  }
}

async function addPendingIceCandidates() {
  if (!peerConnection.value || !peerConnection.value.remoteDescription) return

  const candidates = pendingIceCandidates
  pendingIceCandidates = []

  for (const candidate of candidates) {
    await addIceCandidate(candidate)
  }
}

function closePeerConnection({ keepRemotePeer = false } = {}) {
  if (peerConnection.value) {
    peerConnection.value.close()
    peerConnection.value = null
  }

  if (remoteStream.value) {
    remoteStream.value.getTracks().forEach((track) => track.stop())
    remoteStream.value = null
  }

  videoTransceiver = null
  audioTransceiver = null
  if (!keepRemotePeer) {
    remotePeerId = null
  }
  hasAnsweredPeerReady = false
  makingOffer = false
  ignoreOffer = false
  isSettingRemoteAnswerPending = false
  hasRemoteVideo.value = false
  remoteWantsCamera.value = false
  pendingIceCandidates = []
}

function updateRemoteVideoState() {
  const videoTrack = remoteStream.value
    ?.getVideoTracks()
    .find((track) => track.readyState === "live")

  hasRemoteVideo.value = remoteWantsCamera.value && Boolean(videoTrack)
}

async function runCode() {
  if (isRunning.value) return

  isRunning.value = true

  const runningMessage = "Running code..."
  output.value = runningMessage

  sendSocketMessage("run_output", {
    output: runningMessage,
  })

  try {
    const response = await fetch(`${apiBaseUrl}/api/submissions/run/`, {
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
  padding: 20px;
  background: #0e1117;
  color: #f8fafc;
  font-family: Arial, sans-serif;
}

.room-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.room-header h1,
.panel-heading h2 {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  line-height: 1.2;
}

.panel-heading h2 {
  font-size: 18px;
}

.eyebrow {
  margin: 0 0 4px;
  color: #94a3b8;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.room-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  color: #cbd5e1;
  background: #151b24;
  border: 1px solid #263244;
  border-radius: 8px;
  white-space: nowrap;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #ef4444;
}

.status-dot.online {
  background: #22c55e;
}

.room-blocked {
  max-width: 620px;
  margin: 76px auto 0;
  padding: 28px;
  text-align: center;
  background: #151b24;
  border: 1px solid #334155;
  border-radius: 8px;
}

.room-blocked-icon {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  margin: 0 auto 16px;
  color: #fecaca;
  background: #7f1d1d;
  border: 1px solid #ef4444;
  border-radius: 50%;
  font-size: 30px;
  font-weight: 800;
}

.room-blocked h2 {
  margin: 0 0 10px;
  font-size: 24px;
  line-height: 1.2;
}

.room-blocked p:last-child {
  margin: 0;
  color: #cbd5e1;
  line-height: 1.5;
}

.workspace {
  display: grid;
  grid-template-columns: minmax(300px, 380px) minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.call-panel,
.coding-panel {
  min-width: 0;
}

.call-panel {
  position: sticky;
  top: 20px;
  padding: 16px;
  background: #151b24;
  border: 1px solid #263244;
  border-radius: 8px;
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.video-grid {
  display: grid;
  gap: 12px;
}

.video-tile {
  position: relative;
  min-height: 190px;
  overflow: hidden;
  background: #06080c;
  border: 1px solid #263244;
  border-radius: 8px;
  aspect-ratio: 16 / 10;
}

.video-tile video {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  background: #06080c;
}

.video-tile video.hidden {
  opacity: 0;
}

.video-label {
  position: absolute;
  left: 10px;
  bottom: 10px;
  padding: 4px 8px;
  color: #e2e8f0;
  background: rgba(6, 8, 12, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
}

.video-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #94a3b8;
  font-weight: 700;
}

.person-icon {
  position: relative;
  width: 74px;
  height: 74px;
  border-radius: 50%;
  background: #1f2937;
  border: 1px solid #334155;
  box-shadow: inset 0 0 0 10px #111827;
}

.person-icon::before,
.person-icon::after {
  position: absolute;
  left: 50%;
  content: "";
  transform: translateX(-50%);
}

.person-icon::before {
  top: 15px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #94a3b8;
}

.person-icon::after {
  bottom: 14px;
  width: 42px;
  height: 24px;
  border-radius: 24px 24px 10px 10px;
  background: #94a3b8;
}

.call-controls {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.control-button,
.run-button {
  min-height: 40px;
  padding: 9px 12px;
  color: #f8fafc;
  background: #253044;
  border: 1px solid #344256;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 700;
}

.control-button:hover,
.run-button:hover {
  background: #30405a;
}

.control-button:disabled,
.run-button:disabled {
  color: #64748b;
  background: #1a2230;
  cursor: not-allowed;
}

.control-button.active,
.run-button {
  background: #2563eb;
  border-color: #2563eb;
}

.control-button.active:hover,
.run-button:hover {
  background: #1d4ed8;
}

.call-error {
  margin: 12px 0 0;
  color: #fca5a5;
  line-height: 1.4;
}

.toolbar {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.bottom-grid {
  display: grid;
  grid-template-columns: minmax(260px, 0.75fr) minmax(320px, 1fr);
  gap: 16px;
}

@media (max-width: 980px) {
  .workspace,
  .bottom-grid {
    grid-template-columns: 1fr;
  }

  .call-panel {
    position: static;
  }
}

@media (max-width: 640px) {
  .interview-room {
    padding: 14px;
  }

  .room-header,
  .toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .room-meta {
    justify-content: flex-start;
    white-space: normal;
  }

  .call-controls {
    grid-template-columns: 1fr;
  }
}
</style>
