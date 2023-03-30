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
    orm.start_mappers()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(allocate=handle_allocate_orderline, change_batch_quantity=handle_change_batch_quantity)


def handle_change_batch_quantity(m):
    data = json.loads(m["data"])
    logger.debug("log for handling change batch quantity %s", m)
    print(f"print for handling change batch quantity {m}, {datetime.datetime.now()}")
    command = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    message_bus.handle(command, uow=SqlAlchemyUnitOfWork())


def handle_allocate_orderline(m):
    logger.debug("log for handling allocate orderline %s", m)
    print(f"print for handling allocate orderline {m}, {datetime.datetime.now()}")
    data = json.loads(m["data"])
    command = commands.Allocate(orderid=data["orderid"], qty=data["qty"], sku=data["sku"])
    message_bus.handle(command, uow=SqlAlchemyUnitOfWork())


if __name__ == "__main__":
    main()
