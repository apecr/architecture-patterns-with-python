import json

import pytest
from tenacity import Retrying, stop_after_delay

from . import api_client, redis_client
from ..random_refs import random_sku, random_batchref, random_orderid


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
@pytest.mark.usefixtures("restart_redis_pubsub")
def test_change_batch_quantity_leading_to_reallocation():
    order_id, sku = random_orderid(), random_sku()
    earlier_batch, later_batch = random_batchref("old"), random_batchref("newer")
    api_client.post_to_add_batch(earlier_batch, sku, qty=10, eta="2011-01-01")
    api_client.post_to_add_batch(later_batch, sku, qty=10, eta="2011-01-02")

    response = api_client.post_to_allocate(order_id, sku, 10)

    assert response.json()["batchref"] == earlier_batch

    subscription = redis_client.subscribe_to("line_allocated")
    redis_client.publish_message("change_batch_quantity", {"batchref": earlier_batch, "qty": 5})

    data = _get_data_from_last_redis_message(subscription)
    assert data["orderid"] == order_id
    assert data["batchref"] == later_batch


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
@pytest.mark.usefixtures("restart_redis_pubsub")
def test_allocate_via_redis():
    order_id, sku = random_orderid(), random_sku()
    earlier_batch, later_batch = random_batchref("old"), random_batchref("newer")
    api_client.post_to_add_batch(earlier_batch, sku, qty=10, eta="2011-01-01")
    api_client.post_to_add_batch(later_batch, sku, qty=10, eta="2011-01-02")

    subscription = redis_client.subscribe_to("line_allocated")
    redis_client.publish_message("allocate", {"orderid": order_id, "sku": sku, "qty": 5})

    data = _get_data_from_last_redis_message(subscription)
    assert data["orderid"] == order_id
    assert data["batchref"] == earlier_batch


def _get_data_from_last_redis_message(subscription):
    messages = []
    for attempt in Retrying(stop=stop_after_delay(3), reraise=True):
        with attempt:
            message = subscription.get_message(timeout=1)
            if message:
                messages.append(message)
            return json.loads(messages[-1]["data"])