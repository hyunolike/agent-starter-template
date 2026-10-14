DEMO_REQUESTS = {
    "REQ-1001": {"status": "in_review", "summary": "Sandbox access request"},
    "REQ-1002": {"status": "completed", "summary": "Documentation update"},
}


def get_request(request_id: str) -> dict:
    item = DEMO_REQUESTS.get(request_id)
    return {"request_id": request_id, "found": item is not None, "data": item, "demo": True}
