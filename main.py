import json
import datetime
from typing import List, Dict, Any, Optional, Union
import re
import os
import httpx
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from enum import Enum
import uvicorn

# ======== Models ========

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class Task(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    due_date: Optional[str] = None  # ISO format date string
    status: TaskStatus = TaskStatus.TODO
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None  # ISO format datetime string
    
    def __init__(self, **data):
        if 'created_at' not in data:
            data['created_at'] = datetime.datetime.now().isoformat()
        super().__init__(**data)

class TaskInput(BaseModel):
    command: str

class TaskResponse(BaseModel):
    success: bool
    message: str
    tasks: List[Task] = Field(default_factory=list)

# ======== LLM Integration ========

class LLMProcessor:
    def __init__(self, model_name: str = "mistral"):
        """Initialize the LLM processor with the specified model."""
        self.model_name = model_name
        self.ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
        
    async def process_command(self, command: str, tasks: List[Task]) -> Dict[str, Any]:
        """Process a natural language command using the LLM."""
        try:
            # Convert tasks to a JSON string for the prompt
            tasks_json = json.dumps([task.dict() for task in tasks], indent=2)
            
            # Create a prompt for the LLM
            prompt = f"""
            You are TaskPilot, an AI assistant that manages tasks. 
            
            Current task list:
            ```json
            {tasks_json}
            ```
            
            User command: "{command}"
            
            Analyze this command and determine what action to take. Possible actions:
            1. ADD - Add a new task
            2. UPDATE - Update an existing task
            3. DELETE - Delete a task
            4. LIST - List tasks with optional filtering/sorting
            5. PRIORITIZE - Reorganize tasks by priority
            6. SCHEDULE - Suggest optimal scheduling
            
            Return your response as a JSON object with these fields:
            - action: The action to take (ADD, UPDATE, DELETE, LIST, PRIORITIZE, SCHEDULE)
            - tasks: The updated task list (for ADD, UPDATE, DELETE) or filtered/sorted tasks (for LIST, PRIORITIZE, SCHEDULE)
            - message: A human-readable explanation of what you did
            
            For new tasks, extract as many details as possible (title, description, priority, due_date, tags).
            """
            
            # Call Ollama API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "message": f"LLM API error: {response.text}",
                        "tasks": tasks
                    }
                
                result = response.json()
                llm_response = result.get("response", "")
                
                # Extract JSON from the response
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', llm_response)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # Try to find JSON without markdown formatting
                    json_match = re.search(r'(\{[\s\S]*\})', llm_response)
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        return {
                            "success": False,
                            "message": "Failed to parse LLM response",
                            "tasks": tasks
                        }
                
                try:
                    parsed_response = json.loads(json_str)
                    return {
                        "success": True,
                        "message": parsed_response.get("message", "Command processed"),
                        "tasks": parsed_response.get("tasks", tasks),
                        "action": parsed_response.get("action", "LIST")
                    }
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "message": "Failed to parse JSON from LLM response",
                        "tasks": tasks
                    }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing command: {str(e)}",
                "tasks": tasks
            }
    
    def fallback_process(self, command: str, tasks: List[Task]) -> Dict[str, Any]:
        """Process commands without LLM when it's not available."""
        command = command.lower().strip()
        
        # Simple command parsing
        if "add" in command or "create" in command:
            # Extract task title (everything after "add" or "create")
            title = re.sub(r'^(add|create)\s+', '', command, flags=re.IGNORECASE).strip()
            if title:
                new_task = Task(
                    id=len(tasks) + 1,
                    title=title,
                    created_at=datetime.datetime.now().isoformat()
                )
                tasks.append(new_task)
                return {
                    "success": True,
                    "message": f"Added task: {title}",
                    "tasks": tasks,
                    "action": "ADD"
                }
        
        elif "list" in command:
            return {
                "success": True,
                "message": "Here are your tasks",
                "tasks": tasks,
                "action": "LIST"
            }
            
        elif "prioritize" in command or "sort" in command:
            # Sort by priority
            priority_order = {
                Priority.URGENT: 0,
                Priority.HIGH: 1,
                Priority.MEDIUM: 2,
                Priority.LOW: 3
            }
            sorted_tasks = sorted(tasks, key=lambda t: priority_order.get(t.priority, 4))
            return {
                "success": True,
                "message": "Tasks sorted by priority",
                "tasks": sorted_tasks,
                "action": "PRIORITIZE"
            }
            
        # Default response
        return {
            "success": True,
            "message": "Showing all tasks",
            "tasks": tasks,
            "action": "LIST"
        }

# ======== Task Manager ========

class TaskManager:
    def __init__(self, llm_processor: LLMProcessor):
        """Initialize the task manager with an LLM processor."""
        self.tasks: List[Task] = []
        self.llm_processor = llm_processor
        self.next_id = 1
    
    def _assign_task_id(self, task: Task) -> Task:
        """Assign an ID to a task if it doesn't have one."""
        if task.id is None:
            task.id = self.next_id
            self.next_id += 1
        return task
    
    def add_task(self, task: Task) -> Task:
        """Add a new task to the list."""
        task = self._assign_task_id(task)
        self.tasks.append(task)
        return task
    
    def get_tasks(self) -> List[Task]:
        """Get all tasks."""
        return self.tasks
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def update_task(self, task_id: int, updated_task: Task) -> Optional[Task]:
        """Update an existing task."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                # Preserve the ID and created_at
                updated_task.id = task_id
                if not updated_task.created_at:
                    updated_task.created_at = task.created_at
                self.tasks[i] = updated_task
                return updated_task
        return None
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                self.tasks.pop(i)
                return True
        return False
    
    def update_tasks_from_llm(self, llm_tasks: List[Dict[str, Any]]) -> List[Task]:
        """Update the task list based on LLM output."""
        # Convert dict tasks to Task objects
        new_tasks = []
        for task_dict in llm_tasks:
            # Handle potential missing fields or type mismatches
            try:
                # Clean up the task dict to match Task model
                if isinstance(task_dict.get("tags"), str):
                    task_dict["tags"] = [tag.strip() for tag in task_dict["tags"].split(",")]
                
                # Ensure priority is valid
                if "priority" in task_dict and task_dict["priority"] not in [p.value for p in Priority]:
                    # Try to map common priority terms
                    priority_map = {
                        "critical": Priority.URGENT,
                        "urgent": Priority.URGENT,
                        "high": Priority.HIGH,
                        "medium": Priority.MEDIUM,
                        "normal": Priority.MEDIUM,
                        "low": Priority.LOW
                    }
                    task_dict["priority"] = priority_map.get(
                        str(task_dict["priority"]).lower(), 
                        Priority.MEDIUM
                    )
                
                # Ensure status is valid
                if "status" in task_dict and task_dict["status"] not in [s.value for s in TaskStatus]:
                    # Try to map common status terms
                    status_map = {
                        "to do": TaskStatus.TODO,
                        "todo": TaskStatus.TODO,
                        "in progress": TaskStatus.IN_PROGRESS,
                        "in-progress": TaskStatus.IN_PROGRESS,
                        "done": TaskStatus.DONE,
                        "completed": TaskStatus.DONE,
                        "finished": TaskStatus.DONE
                    }
                    task_dict["status"] = status_map.get(
                        str(task_dict["status"]).lower(), 
                        TaskStatus.TODO
                    )
                
                task = Task(**task_dict)
                new_tasks.append(task)
            except Exception as e:
                print(f"Error converting task: {e}")
                # Skip invalid tasks
                continue
        
        # Update IDs for new tasks
        for task in new_tasks:
            if task.id is None:
                task = self._assign_task_id(task)
        
        # Replace the task list
        self.tasks = new_tasks
        return self.tasks
    
    async def process_command(self, command: str) -> Dict[str, Any]:
        """Process a natural language command."""
        try:
            # Try using the LLM processor
            result = await self.llm_processor.process_command(command, self.tasks)
            
            if not result["success"]:
                # Fall back to simple command processing
                result = self.llm_processor.fallback_process(command, self.tasks)
            
            # Update tasks if the LLM returned new/modified tasks
            if result["success"] and "tasks" in result:
                self.update_tasks_from_llm(result["tasks"])
            
            return {
                "success": result["success"],
                "message": result["message"],
                "tasks": self.tasks
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing command: {str(e)}",
                "tasks": self.tasks
            }

# ======== API ========

app = FastAPI(title="TaskPilot API", description="AI-powered task management system")

# Initialize LLM processor and task manager
llm_processor = LLMProcessor(model_name="mistral")
task_manager = TaskManager(llm_processor)

# Add some example tasks
task_manager.add_task(Task(
    title="Complete project proposal",
    description="Write up the final project proposal for client review",
    priority=Priority.HIGH,
    due_date=(datetime.datetime.now() + datetime.timedelta(days=2)).isoformat().split('T')[0],
    tags=["work", "client"]
))

task_manager.add_task(Task(
    title="Buy groceries",
    description="Milk, eggs, bread, vegetables",
    priority=Priority.MEDIUM,
    tags=["personal", "shopping"]
))

@app.post("/tasks/process", response_model=TaskResponse)
async def process_task_command(input_data: TaskInput = Body(...)):
    """Process a natural language command for task management."""
    result = await task_manager.process_command(input_data.command)
    return TaskResponse(
        success=result["success"],
        message=result["message"],
        tasks=result["tasks"]
    )

@app.get("/tasks", response_model=List[Task])
def get_all_tasks():
    """Get all tasks."""
    return task_manager.get_tasks()

@app.post("/tasks", response_model=Task)
def create_task(task: Task):
    """Create a new task."""
    return task_manager.add_task(task)

@app.get("/tasks/{task_id}", response_model=Optional[Task])
def get_task(task_id: int):
    """Get a task by ID."""
    task = task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=Optional[Task])
def update_task(task_id: int, task: Task):
    """Update a task."""
    updated_task = task_manager.update_task(task_id, task)
    if updated_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task

@app.delete("/tasks/{task_id}", response_model=bool)
def delete_task(task_id: int):
    """Delete a task."""
    success = task_manager.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return success

# ======== CLI Demo ========

async def cli_demo():
    """Run a CLI demo of the TaskPilot system."""
    print("🚀 TaskPilot - AI-Powered Task Management")
    print("----------------------------------------")
    print("Type your commands in natural language, or 'exit' to quit.")
    print("Examples:")
    print("  - Add a task to call mom tomorrow")
    print("  - Show all my high priority tasks")
    print("  - Mark the grocery task as done")
    print("  - Prioritize my tasks")
    print("----------------------------------------")
    
    while True:
        command = input("\n> ")
        if command.lower() in ["exit", "quit", "q"]:
            break
            
        result = await task_manager.process_command(command)
        
        print(f"\n{result['message']}")
        if result["tasks"]:
            print("\nTasks:")
            for task in result["tasks"]:
                priority_symbol = {
                    Priority.URGENT: "🔴",
                    Priority.HIGH: "🟠",
                    Priority.MEDIUM: "🟡",
                    Priority.LOW: "🟢"
                }.get(task.priority, "⚪")
                
                status_symbol = {
                    TaskStatus.TODO: "□",
                    TaskStatus.IN_PROGRESS: "◑",
                    TaskStatus.DONE: "✓"
                }.get(task.status, "□")
                
                due_str = f" (Due: {task.due_date})" if task.due_date else ""
                tags_str = f" [{', '.join(task.tags)}]" if task.tags else ""
                
                print(f"{status_symbol} {priority_symbol} {task.id}: {task.title}{due_str}{tags_str}")
                if task.description:
                    print(f"   {task.description}")
        print("----------------------------------------")

# ======== Main ========

if __name__ == "__main__":
    import asyncio
    
    # Check if we should run the API or CLI demo
    if os.environ.get("RUN_API", "false").lower() == "true":
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        asyncio.run(cli_demo())