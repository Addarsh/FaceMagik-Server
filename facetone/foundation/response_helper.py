"""
Helper to create HTTP response native objects.
"""


def create_response_message_with_error_code(msg: str, code: int) -> dict:
    return {"message": msg, "code": code}


def create_response_message(msg: str) -> dict:
    return {"message": msg}
