import requests
from icecream import ic

from api.services.http_schemas import TaskTargetCreate

BASE_URL = "http://localhost:8000/task-management/task-targets/"


def create_task_target(task_target: TaskTargetCreate):
    """Test POST /task-targets/ endpoint"""
    response = requests.post(BASE_URL, json=task_target.model_dump())
    ic(
        f"POST Task Target | Status Code: {response.status_code} | "
        f"Created ID: {response.json()}"
    )


def get_task_targets(skip=0, limit=100, task_id=None, line_id=None):
    """Test GET /task-targets/ endpoint"""
    params = {
        "skip": skip,
        "limit": limit,
        "task_id": task_id,
        "line_id": line_id
    }
    response = requests.get(BASE_URL, params=params)
    ic(
        f"GET Task Targets | Status Code: {response.status_code} | "
        f"Count: {len(response.json())} | "
        f"Sample: {response.json()[0] if response.json() else 'None'}"
    )


def delete_task_target(task_target_id: int):
    """Test DELETE /task-targets/{task_target_id} endpoint"""
    url = f"{BASE_URL}{task_target_id}"
    response = requests.delete(url)
    ic(
        f"DELETE Task Target | Status Code: {response.status_code} | "
        f"Response: {response.json()}"
    )


# Example usage
new_target = TaskTargetCreate(
    task_id=1,
    line_id=3
)
create_task_target(new_target)

get_task_targets(task_id=1)
delete_task_target(1)
