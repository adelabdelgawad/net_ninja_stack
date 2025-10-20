import requests
from icecream import ic


BASE_URL = "http://localhost:8000/task-management/task-statuses/"


def get_task_statuses():
    """Test GET /task-statuses/ endpoint"""
    response = requests.get(BASE_URL)
    ic(
        f"GET Task Statuses | Status Code: {response.status_code} | "
        f"Count: {len(response.json())} | "
        f"Sample: {response.json()[0] if response.json() else 'None'}"
    )


def get_task_status(task_status_id: int):
    """Test GET /task-statuses/{task_status_id} endpoint"""
    url = f"{BASE_URL}{task_status_id}"
    response = requests.get(url)
    ic(
        f"GET Task Status | Status Code: {response.status_code} | "
        f"Status ID {task_status_id} Details: {response.json()}"
    )


# Example usage
get_task_statuses()
get_task_status(1)
