TaskPilot 🚀

AI-powered task management through natural language

Python FastAPI License: MIT

📋 Overview

TaskPilot is an intelligent task management system that allows you to manage your tasks using natural language commands. It leverages Large Language Models to understand and process your instructions, making task management more intuitive and efficient.

Simply tell TaskPilot what you want to do in plain English, and it will handle the details for you:

> Add a task to finish the quarterly report by next Friday with high priority
✅ Added task: Finish the quarterly report (High Priority, Due: 2023-05-12)

✨ Features

    🗣️ Natural Language Interface: Manage tasks using everyday language
    🧠 AI-Powered Understanding: Leverages Mistral LLM to interpret your commands
    🔄 Complete Task Management: Add, update, delete, list, and organize tasks
    🚨 Priority Levels: Automatically categorize tasks (Low, Medium, High, Urgent)
    📅 Due Dates: Set and track deadlines for your tasks
    🏷️ Tagging System: Organize tasks with custom tags
    📊 Status Tracking: Monitor progress (Todo, In Progress, Done)
    🔌 REST API: Full-featured API for integration with other applications
    💻 CLI Interface: Command-line interface for quick task management
    🐳 Docker Support: Easy deployment with Docker

🛠️ Installation
Prerequisites

    Python 3.7+
    Ollama with the Mistral model installed

Option 1: Standard Installation

    Clone the repository:

    git clone https://github.com/Itaxh1/TaskPilot.git
    cd TaskPilot


2. **Install dependencies**:

```shellscript
pip install -r requirements.txt
```


3. **Install and run Ollama with Mistral**:

```shellscript
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# For Windows, download from https://ollama.ai/download

# Pull and run the Mistral model
ollama pull mistral
ollama run mistral
```




### Option 2: Docker Installation

1. **Clone the repository**:

```shellscript
git clone https://github.com/Itaxh1/TaskPilot.git
cd TaskPilot
```


2. **Create a Docker Compose file** (save as `docker-compose.yml`):

```yaml
version: '3'
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    command: ["ollama", "serve"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  taskpilot:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_URL=http://ollama:11434
      - RUN_API=true
    depends_on:
      ollama:
        condition: service_healthy

volumes:
  ollama_data:
```


3. **Create a Dockerfile** (save as `Dockerfile`):

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["python", "main.py"]
```


4. **Build and run with Docker Compose**:

```shellscript
docker-compose up -d

# Initialize the Mistral model
docker-compose exec ollama ollama pull mistral
```




## 🚀 Usage

### CLI Mode

Run TaskPilot in CLI mode:

```shellscript
python main.py
```

You'll see a prompt where you can enter natural language commands:

```plaintext
🚀 TaskPilot - AI-Powered Task Management
----------------------------------------
Type your commands in natural language, or 'exit' to quit.
Examples:
  - Add a task to call mom tomorrow
  - Show all my high priority tasks
  - Mark the grocery task as done
  - Prioritize my tasks
----------------------------------------

>
```

#### Example Commands

| Command | Description
|-----|-----
| `Add a task to review the marketing proposal by Thursday` | Creates a new task with a due date
| `Add a high priority task to fix the login bug` | Creates a high priority task
| `Show all my tasks` | Lists all tasks
| `Show my high priority tasks` | Lists tasks filtered by priority
| `Mark task 3 as done` | Updates the status of task #3
| `Delete task 2` | Removes task #2
| `Prioritize my tasks` | Sorts tasks by priority
| `What tasks are due this week?` | Lists tasks with due dates this week
| `Add tags client and urgent to task 1` | Adds tags to an existing task


### API Mode

Start the API server:

```shellscript
RUN_API=true python main.py
```

Or using uvicorn directly:

```shellscript
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

#### API Endpoints

| Endpoint | Method | Description
|-----|-----
| `/tasks/process` | POST | Process natural language commands
| `/tasks` | GET | List all tasks
| `/tasks` | POST | Create a new task
| `/tasks/{task_id}` | GET | Get a specific task
| `/tasks/{task_id}` | PUT | Update a task
| `/tasks/{task_id}` | DELETE | Delete a task


#### Example API Requests

**Process a natural language command**:

```shellscript
curl -X POST "http://localhost:8000/tasks/process" \
  -H "Content-Type: application/json" \
  -d '{"command": "Add a task to prepare presentation for client meeting tomorrow"}'
```

**List all tasks**:

```shellscript
curl -X GET "http://localhost:8000/tasks"
```

**Create a new task**:

```shellscript
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Review project proposal",
    "description": "Go through the latest version and provide feedback",
    "priority": "high",
    "due_date": "2023-05-15",
    "tags": ["work", "client"]
  }'
```

**Update a task**:

```shellscript
curl -X PUT "http://localhost:8000/tasks/1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Review project proposal",
    "description": "Go through the latest version and provide feedback",
    "priority": "high",
    "due_date": "2023-05-15",
    "status": "in_progress",
    "tags": ["work", "client", "urgent"]
  }'
```

**Delete a task**:

```shellscript
curl -X DELETE "http://localhost:8000/tasks/1"
```

### API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`


## 🔧 Configuration

### Environment Variables

| Variable | Description | Default
|-----|-----
| `OLLAMA_URL` | URL for the Ollama API | `http://localhost:11434`
| `RUN_API` | Set to "true" to run in API mode | `false`


## 🧩 How It Works

TaskPilot uses a combination of FastAPI for the backend and Ollama for natural language processing:

1. **Input**: User enters a natural language command
2. **Processing**: The command is sent to the Mistral LLM via Ollama
3. **Interpretation**: The LLM analyzes the command and determines the appropriate action
4. **Execution**: TaskPilot executes the action and updates the task list
5. **Response**: Results are returned to the user in a readable format


### Architecture Diagram

```plaintext
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────▶│  TaskPilot  │────▶│   Ollama    │
│ Interface   │     │  (FastAPI)  │     │  (Mistral)  │
└─────────────┘     └─────────────┘     └─────────────┘
       ▲                   │                   │
       │                   │                   │
       └───────────────────┴───────────────────┘
```

## 📁 Project Structure

```plaintext
TaskPilot/
├── main.py              # Main application file
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
└── README.md            # Project documentation
```

### Code Organization

The `main.py` file contains several key components:

- **Models**: Pydantic models for tasks and API responses
- **LLMProcessor**: Handles communication with the Ollama API
- **TaskManager**: Manages the task collection and operations
- **FastAPI App**: Defines the API endpoints
- **CLI Demo**: Provides a command-line interface


## 📦 Dependencies

- **FastAPI**: Web framework for building APIs
- **Pydantic**: Data validation and settings management
- **httpx**: Asynchronous HTTP client
- **uvicorn**: ASGI server implementation
- **Ollama**: Local LLM server
- **Mistral**: Large Language Model


## 🔍 Troubleshooting

### Common Issues

**Issue**: Cannot connect to Ollama server
**Solution**: Make sure Ollama is running with `ollama serve` and check the `OLLAMA_URL` environment variable.

**Issue**: LLM responses are not accurate
**Solution**: Ensure you're using the Mistral model. Try using more specific commands.

**Issue**: Application crashes on startup
**Solution**: Check that all dependencies are installed with `pip install -r requirements.txt`.

## 🧪 Development

### Setting Up Development Environment

1. Clone the repository:

```shellscript
git clone https://github.com/Itaxh1/TaskPilot.git
cd TaskPilot
```


2. Create a virtual environment:

```shellscript
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```


3. Install dependencies:

```shellscript
pip install -r requirements.txt
```


4. Install development dependencies:

```shellscript
pip install pytest black isort mypy
```




### Running Tests

```shellscript
pytest
```

### Code Formatting

```shellscript
black main.py
isort main.py
```

## 🔮 Future Enhancements

- **Web UI**: Develop a user-friendly web interface
- **Database Integration**: Persistent storage with SQLAlchemy
- **Calendar Integration**: Sync with Google Calendar, Outlook, etc.
- **Recurring Tasks**: Support for repeating tasks
- **Team Collaboration**: Multi-user support and task assignment
- **Mobile App**: Native mobile applications
- **Offline Mode**: Function without internet connection
- **Advanced Analytics**: Task completion statistics and productivity insights
- **Voice Interface**: Support for voice commands


## 👥 Contributing

Contributions are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request


Please make sure to update tests as appropriate.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [Ollama](https://ollama.ai/) for providing local LLM capabilities
- [Mistral AI](https://mistral.ai/) for the language model
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation
- [httpx](https://www.python-httpx.org/) for async HTTP requests
