# 🌱 SpringGPT

**Your AI-powered guide to Spring Framework documentation.**

SpringGPT is a locally running, documentation-focused AI chatbot designed to make navigating and understanding Spring documentation easier. Instead of relying on general-purpose AI knowledge, SpringGPT uses a semantic search and retrieval pipeline to answer questions exclusively using the Spring documentation provided in `chatbot-backend/data/`.

Whether you're trying to understand a Spring concept, find an explanation of a particular feature, or figure out how to implement something, SpringGPT helps you find relevant answers through natural conversation.

**No guessing. No unrelated answers. Just Spring documentation.**

## Features

- **Documentation-Grounded Answers:** Answers questions exclusively using the ingested Spring documentation. If a question falls outside the available documentation, SpringGPT politely refuses to answer rather than generating an unsupported response.
- **Semantic Search:** Understands the meaning and intent behind questions, retrieving relevant documentation even when the wording doesn't exactly match the source material.
- **Multiple Chats:** Start and manage multiple conversations independently.
- **Chat History & Sidebar:** Easily navigate between previous conversations and pick up where you left off.
- **Animated Spring Bean Mascot:** A friendly Spring Bean companion with animations for different states, including thinking, waving, and more.
- **Dark & Light Themes:** Switch between dark and light modes for a comfortable experience.
- **Runs Locally:** The application and its AI models run locally, without relying on external AI APIs.
- **Single-User Application:** Designed as a personal, local documentation assistant rather than a multi-user platform.

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | Angular |
| Backend | Python, FastAPI |
| LLM Orchestration | LangChain |
| Embedding Model | `nomic-embed-text` |
| Language Model | `llama3.2:3b` |
| Model Runtime | Ollama |
| Vector Database | Chroma |
| Search Method | Semantic Similarity Search (Top-K Retrieval) |

All AI models are executed locally through Ollama, keeping the application self-contained.

## Getting Started

Follow these steps to run SpringGPT locally.

### Prerequisites

Make sure you have the following installed:

- [Node.js and npm](https://nodejs.org/)
- [Angular CLI](https://angular.dev/tools/cli)
- [Python](https://www.python.org/)
- [Ollama](https://ollama.com/)

### Set Up Ollama

SpringGPT requires two locally installed models:

- `nomic-embed-text` – Generates embeddings for semantic document retrieval.
- `llama3.2:3b` – Generates conversational answers using the retrieved documentation.

Pull both models:

```bash
ollama pull nomic-embed-text
ollama pull llama3.2:3b
```

Make sure Ollama is running before starting the backend.

### Start the Backend

Navigate to the backend directory:

```bash
chatbot-backend/
```

Create a python enviornment and install the backend dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server using your backend entry point:

```bash
uvicorn main:app --reload
```

The backend should now be accessible at:

```text
http://localhost:8000
```

### Ingest the Spring Documentation

Before using the chatbot, you need to ingest the Spring documentation into the vector database.

1. Make sure the documentation files are available inside `chatbot-backend/data/`.
2. Open the FastAPI Swagger UI:

   ```text
   http://localhost:8000/docs
   ```

3. Locate the `/ingest` API endpoint.
4. Execute the endpoint to start the documentation ingestion process.
5. Wait for ingestion and vectorization to complete successfully.

Once ingestion is complete, SpringGPT will be able to retrieve information from the Spring documentation.

> **Note:** Documentation ingestion should be performed whenever you want to populate or refresh the vector database with the source documentation.

### Start the Frontend

Open a new terminal and navigate to the frontend directory:

```bash
chatbot-frontend/
```

Install the dependencies:

```bash
npm install
```

Start the Angular development server:

```bash
ng serve
```

Open the application in your browser:

```text
http://localhost:4200
```

## Team Breadwinners

- [@Darsh-KP](https://github.com/Darsh-KP)
- [@di-gital](https://github.com/di-gital)
- [@dlin07](https://github.com/dlin07)
- [@gilololol64](https://github.com/gilololol64)
- [@sarinjet1008](https://github.com/sarinjet1008)
- [@tlee51](https://github.com/tlee51)
- [@walterl1](https://github.com/walterl1)

---

*SpringGPT — Making Spring documentation easier to understand, one conversation at a time.*
