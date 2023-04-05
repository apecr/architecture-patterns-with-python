import datetime
import json
import logging

import redis

from allocation import config
from allocation.adapters import orm
from allocation.domain import commands
from allocation.service_layer.message_bus import MessageBus
from allocation.service_layer.unit_of_work import SqlAlchemyUnitOfWork

r = redis.Redis(**config.get_redis_host_and_port())
logger = logging.getLogger(__name__)
message_bus = MessageBus()


def main():
    print("Starting redis_pubsub image")
    orm.start_mappers()
    print(config.get_redis_host_and_port())
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    result = pubsub.subscribe(allocate=handle_allocate_orderline,
                              change_batch_quantity=handle_change_batch_quantity)
    print("End Starting redis_pubsub image")
    print(result)


def handle_change_batch_quantity(m):
    print("hello handle_change_batch_quantity")
    data = json.loads(m["data"])
    logger.debug("log for handling change batch quantity %s", m)
    print(f"print for handling change batch quantity {m}, {datetime.datetime.now()}")
    command = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    message_bus.handle(command, uow=SqlAlchemyUnitOfWork())


def handle_allocate_orderline(m):
    print("hello handle_allocate_orderline")
    logger.debug("log for handling allocate orderline %s", m)
    print(f"print for handling allocate orderline {m}, {datetime.datetime.now()}")
    data = json.loads(m["data"])
    command = commands.Allocate(orderid=data["orderid"], qty=data["qty"], sku=data["sku"])
    message_bus.handle(command, uow=SqlAlchemyUnitOfWork())


if __name__ == "__main__":
    main()
