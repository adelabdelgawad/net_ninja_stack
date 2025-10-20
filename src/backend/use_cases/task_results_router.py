import requests
from icecream import ic

BASE_URL = "http://localhost:8000/task-management/task-results/"


def get_task_results(skip=0, limit=10):
    params = {"skip": skip, "limit": limit}
    response = requests.get(BASE_URL, params=params)
    ic(f"GET Task Results | Status Code: {response.status_code} | Response Count: {len(response.json())} | Sample: {response.json()[0] if response.json() else 'None'}")


def get_task_results_by_task_id(task_id: int, skip=0, limit=10):
    url = f"{BASE_URL}task/{task_id}"
    params = {"skip": skip, "limit": limit}
    response = requests.get(url, params=params)
    ic(f"GET Task Results by Task ID | Status Code: {response.status_code} | Task ID {task_id} Results: {response.json()}")


def get_task_results_by_task_ids(task_ids, skip=0, limit=10):
    url = f"{BASE_URL}tasks"
    params = [("task_ids", tid) for tid in task_ids] + \
        [("skip", skip), ("limit", limit)]
    response = requests.get(url, params=params)
    ic(f"GET Task Results by Task IDs | Status Code: {response.status_code} | Results: {response.json()}")


def get_task_results_by_success_status(is_succeed: bool, skip=0, limit=10):
    url = f"{BASE_URL}status/{str(is_succeed).lower()}"
    params = {"skip": skip, "limit": limit}
    response = requests.get(url, params=params)
    ic(f"GET Task Results by Success Status | Status Code: {response.status_code} | Results: {response.json()}")


# Example usage with real data
get_task_results(skip=0, limit=5)
get_task_results_by_task_id(task_id=1, skip=0, limit=5)
get_task_results_by_task_ids([1, 2, 3], skip=0, limit=5)
get_task_results_by_success_status(is_succeed=False, skip=0, limit=5)
