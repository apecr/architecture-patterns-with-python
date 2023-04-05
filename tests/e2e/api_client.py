import requests

from allocation import config


def post_to_add_batch(ref, sku, qty, eta):
    data = {"ref": ref, "sku": sku, "qty": qty, "eta": eta}
    return _execute_post(data, "add_batch")


def post_to_allocate(order_id, sku, qty):
    data = {"orderid": order_id, "sku": sku, "qty": qty}
    return _execute_post(data, "allocate")


def get_allocation(order_id):
    url = config.get_api_url()
    print(f"{url}/allocations/{order_id}")
    return requests.get(f"{url}/allocations/{order_id}")


def _execute_post(data, path):
    url = config.get_api_url()
    return requests.post(f"{url}/{path}", json=data)
