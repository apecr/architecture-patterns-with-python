import pytest
import requests

from allocation import config
from ..random_refs import random_sku, random_batchref, random_orderid


def post_to_add_batch(ref, sku, qty, eta):
    url = config.get_api_url()
    r = requests.post(
        f"{url}/add_batch", json={"ref": ref, "sku": sku, "qty": qty, "eta": eta}
    )
    print(r)
    print(r.__dict__)
    assert r.status_code == 201


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_happy_path_returns_201_and_allocated_batch():
    sku, othersku = random_sku(), random_sku("other")
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)
    post_to_add_batch(laterbatch, sku, 100, "2011-01-02")
    post_to_add_batch(earlybatch, sku, 100, "2011-01-01")
    post_to_add_batch(otherbatch, othersku, 100, None)
    data = {"orderid": random_orderid(), "sku": sku, "qty": 3}

    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)

    assert r.status_code == 201
    assert r.json()["batchref"] == earlybatch


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_unhappy_path_returns_400_and_error_message():
    unknown_sku, orderid = random_sku(), random_orderid()
    data = {"orderid": orderid, "sku": unknown_sku, "qty": 20}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)
    assert r.status_code == 400
    assert r.json()["message"] == f"Invalid sku {unknown_sku}"


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_can_not_allocate_not_enough_quantity():
    sku = random_sku()
    earlybatch = random_batchref(1)
    post_to_add_batch(earlybatch, sku, 100, "2011-01-01")
    data = {"orderid": random_orderid(), "sku": sku, "qty": 110}
    url = config.get_api_url()

    r = requests.post(f"{url}/allocate", json=data)

    assert r.json()["message"] == f"Out of stock {sku}"
    assert r.status_code == 400
