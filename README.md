# Collaborative Interview IDE

A professional, real-time collaborative coding platform designed for technical interviews and pair programming. This application provides a seamless, synchronized coding experience with integrated remote code execution and automated test case evaluation.

## 🚀 Key Features

*   **Real-Time Collaboration**: Minimal-latency code synchronization across multiple clients using WebSockets (Django Channels).
*   **Intelligent Code Editor**: Powered by Monaco Editor (the core engine behind VS Code) offering advanced syntax highlighting, code completion, and formatting.
*   **Live Code Execution**: Secure remote code execution supporting multiple languages (Python, C, C++, Java) integrated via the Judge0 API.
*   **Automated Test Evaluation**: Allows interviewers to define input/output test cases and instantly evaluate the candidate's solution with detailed pass/fail reports, execution time, and memory usage metrics.
*   **Live Presence Tracking**: Real-time indicator of users currently active in the interview room.

## 🛠️ Technology Stack

### Frontend
*   **Framework**: Vue 3 (Composition API)
*   **Build Tool**: Vite for lightning-fast HMR and optimized builds
*   **Editor Engine**: `@guolao/vue-monaco-editor`
*   **Routing**: Vue Router for seamless single-page application navigation

### Backend
*   **Framework**: Django & Django REST Framework (DRF)
*   **WebSockets**: Django Channels for handling bidirectional real-time communication
*   **Code Execution**: Judge0 API (Remote Compilation & Execution)
*   **Database**: SQLite (Development)

## 🏗️ Architecture

1.  **Room Generation**: Users land on the home page and can join or create a unique interview room.
2.  **WebSocket Connection**: Once in a room, a WebSocket connection is established with the Django backend.
3.  **Event Broadcasting**: As the user types, editor state changes are broadcasted to the Django Channels consumer, which instantly relays the payload to all other clients in the same room.
4.  **Code Evaluation**: When the candidate runs their code, a REST API call is made to the backend, which proxies the request to the Judge0 API. The backend polls for the execution results, compares them against the expected outputs of the provided test cases, and returns a formatted evaluation report.

## ⚙️ How to Run Locally

### Prerequisites
*   Node.js (v22+)
*   Python (3.10+)

### 1. Starting the Backend

```bash
cd interview-backend
# Activate the virtual environment
source venv/bin/activate
# Run migrations (if not already applied)
python manage.py migrate
# Start the development server
python manage.py runserver 8000
```
The backend API and WebSocket server will be available at `http://localhost:8000` & `ws://localhost:8000`.

### 2. Starting the Frontend

Open a new terminal window:

```bash
cd interview-frontend
# Install dependencies
npm install
# Start the Vite development server
npm run dev
```
The frontend application will be accessible at `http://localhost:5173`.

## 💡 Use Cases

*   **Campus Placements & Technical Interviews**: Conduct remote coding rounds efficiently.
*   **Pair Programming**: Collaborate on algorithmic problems with peers.
*   **Educational Mentoring**: Instructors can live-demonstrate coding concepts while students follow along in the same environment.
