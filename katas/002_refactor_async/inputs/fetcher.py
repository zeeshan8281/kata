_DB = {
    1: {"name": "ada", "orders": [10, 20, 30]},
    2: {"name": "linus", "orders": [5]},
}


def _get(uid):
    return _DB[uid]


def fetch_user(uid):
    return _get(uid)["name"]


def fetch_orders(uid):
    return _get(uid)["orders"]


def total_spend(uid):
    return sum(fetch_orders(uid))
