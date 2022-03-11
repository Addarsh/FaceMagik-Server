"""
Helper to create HTTP response native objects.
"""


def create_response_message(msg: str) -> dict:
    return {"message": msg}
