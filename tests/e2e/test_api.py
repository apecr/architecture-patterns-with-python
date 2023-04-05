import pytest
import requests

from allocation import config
from . import api_client
from ..random_refs import random_sku, random_batchref, random_orderid


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_happy_path_returns_202():
    sku, other_sku = random_sku(), random_sku("other")
    early_batch = random_batchref(1)
    later_batch = random_batchref(2)
    other_batch = random_batchref(3)
    api_client.post_to_add_batch(later_batch, sku, 100, "2011-01-02")
    api_client.post_to_add_batch(early_batch, sku, 100, "2011-01-01")
    api_client.post_to_add_batch(other_batch, other_sku, 100, None)

    r = api_client.post_to_allocate(random_orderid(), sku, 3)

    assert r.status_code == 202


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_happy_path_returns_202_then_we_can_retrieve_new_element():
    order_id = random_orderid()
    sku, other_sku = random_sku(), random_sku("other")
    early_batch = random_batchref(1)
    later_batch = random_batchref(2)
    other_batch = random_batchref(3)
    api_client.post_to_add_batch(later_batch, sku, 100, "2011-01-02")
    api_client.post_to_add_batch(early_batch, sku, 100, "2011-01-01")
    api_client.post_to_add_batch(other_batch, other_sku, 100, None)

    r = api_client.post_to_allocate(order_id, sku, 3)
    assert r.status_code == 202

    get_order_response = api_client.get_allocation(order_id)

    assert get_order_response.ok
    assert get_order_response.json() == [{"sku": sku, "batchref": early_batch}]


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_unhappy_path_returns_400_and_error_message():
    unknown_sku, orderid = random_sku(), random_orderid()
    data = {"orderid": orderid, "sku": unknown_sku, "qty": 20}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)
    assert r.status_code == 400
    assert r.json()["message"] == f"Invalid sku {unknown_sku}"

    get_order_response = api_client.get_allocation(orderid)

    assert get_order_response.status_code == 404


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_can_not_allocate_not_enough_quantity():
    sku = random_sku()
    early_batch = random_batchref(1)
    api_client.post_to_add_batch(early_batch, sku, 100, "2011-01-01")
    data = {"orderid": random_orderid(), "sku": sku, "qty": 110}
    url = config.get_api_url()

    r = requests.post(f"{url}/allocate", json=data)

    assert r.json()["message"] == f"Out of stock {sku}"
    assert r.status_code == 400
