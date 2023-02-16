from dataclasses import dataclass


class Event(object):
    pass


@dataclass
class OutOfStock(Event):
    sku: str
