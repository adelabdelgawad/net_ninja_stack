import requests
from icecream import ic

from api.services.http_schemas import TaskCreate, TaskUpdate

BASE_URL = "http://localhost:8000/task-management/tasks/"


def create_task(task: TaskCreate):
    """Test POST /tasks/ endpoint"""
    response = requests.post(BASE_URL, json=task.model_dump())
    ic(
        f"POST Task | Status Code: {response.status_code} | "
        f"Created ID: {response.json()}"
    )


def update_task(task_id: int, task_update: TaskUpdate):
    """Test PUT /tasks/{task_id} endpoint"""
    url = f"{BASE_URL}{task_id}"
    response = requests.put(url, json=task_update.model_dump())
    ic(
        f"PUT Task | Status Code: {response.status_code} | "
        f"Response: {response.json()}"
    )


def get_tasks(skip=0, limit=100, status_id=None, job_id=None):
    """Test GET /tasks/ endpoint"""
    params = {
        "skip": skip,
        "limit": limit,
        "status_id": status_id,
        "job_id": job_id
    }
    response = requests.get(BASE_URL, params=params)
    ic(
        f"GET Tasks | Status Code: {response.status_code} | "
        f"Count: {len(response.json())} | "
        f"Sample: {response.json()[0] if response.json() else 'None'}"
    )


# Example usage
new_task = TaskCreate(
    name="Daily Speed Test",
    description="Run speed tests on all lines",
    status_id=1,
    job_id=2
)
create_task(new_task)

update_data = TaskUpdate(
    name="Updated Speed Test",
    description="Updated description",
    status_id=2
)
update_task(1, update_data)

get_tasks(status_id=1)
