import requests
from icecream import ic

from api.services.http_schemas import LineCreate  # Adjust imports as needed
from api.services.http_schemas import LineUpdate

BASE_URL = "http://localhost:8000/config/lines/"


def post_line(line: LineCreate):
    response = requests.post(BASE_URL, json=line.model_dump())
    ic(f"POST Line | Status Code: {response.status_code} | Response Body: {response.json()}")


def get_lines():
    response = requests.get(BASE_URL)
    ic(f"GET Lines | Status Code: {response.status_code} | Response Body: {response.json()}")


def get_line_by_id(line_id: int):
    url = f"{BASE_URL}{line_id}/"
    response = requests.get(url)
    ic(f"GET Line by ID | Status Code: {response.status_code} | Response Body: {response.json()}")


def update_line(line_id: int, line: LineUpdate):
    url = f"{BASE_URL}{line_id}/"
    response = requests.put(url, json=line.model_dump())
    ic(f"PUT Line | Status Code: {response.status_code} | Response Body: {response.json()}")


def delete_line(line_id: int):
    url = f"{BASE_URL}{line_id}/"
    response = requests.delete(url)
    ic(f"DELETE Line | Status Code: {response.status_code} | Response Body: {response.json()}")


if __name__ == "__main__":
    # # Example usage with real data:
    # new_line = LineCreate(
    #     line_number="033262598",
    #     name="Home VDSL",
    #     description="My Home VDSL Line",
    #     ip_address="10.23.1.90",
    #     isp_id=1,
    #     username="033262598",
    #     password="Password",
    # )
    # post_line(new_line)

    # get_lines()

    # line_id = 1  # Replace with a real line ID from your DB
    # get_line_by_id(line_id)

    # updated_line = LineUpdate(
    #     name="Updated Home VDSL",
    #     description="Updated description",
    #     ip_address="10.23.1.91",
    #     isp_id=1,
    #     username="033262598",
    #     password="NewPassword",
    # )
    # update_line(1, updated_line)

    delete_line(1)
