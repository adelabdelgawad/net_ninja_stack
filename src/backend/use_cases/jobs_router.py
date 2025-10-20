import icecream
import requests

BASE_URL = "http://localhost:8000/task-management/jobs/"


def get_all_jobs():
    """Test GET /jobs/ endpoint"""
    response = requests.get(BASE_URL)
    
        f"GET All Jobs | Status Code: {response.status_code} | "
        f"Response Count: {len(response.json())} | "
    )
    icecream.ic(response.json())if response.json() else 'None')


def get_job_by_id(job_id: int):
    """Test GET /jobs/{job_id} endpoint"""
    url = f"{BASE_URL}{job_id}"
    response = requests.get(url)
    
        f"GET Job by ID | Status Code: {response.status_code} | "
        f"Job ID {job_id} Details: {response.json()}"
    )


# Example usage with real data:
get_all_jobs()  # Returns list of JobSummary objects
get_job_by_id(1)  # Returns JobResponse for ID 1
