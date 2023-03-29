import json
import logging
from dataclasses import asdict

from redis import Redis

from allocation.config import get_redis_host_and_port
from allocation.domain.events import Event

r = Redis(**get_redis_host_and_port())
logger = logging.getLogger(__name__)


def publish(channel, event: Event):
    logger.debug("publishing: channel=%s, event=%s", channel, event)
    r.publish(channel, json.dumps(asdict(event)))
