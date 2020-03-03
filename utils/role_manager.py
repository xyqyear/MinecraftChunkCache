# 0: proxy server, 1: proxy client
role = 0


def set_role(r: int):
    global role
    role = r


def get_role() -> int:
    global role
    return role
