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
    pubsub.subscribe("change_batch_quantity")

    for m in pubsub.listen():
        handle_change_batch_quantity(m)


def handle_change_batch_quantity(m):
    logger.debug("handling %s", m)
    data = json.loads(m["data"])
    command = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    message_bus.handle(command, uow=SqlAlchemyUnitOfWork())


if __name__ == "__main__":
    main()
