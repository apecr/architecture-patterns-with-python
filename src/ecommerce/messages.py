from dataclasses import dataclass
from typing import List, Any


class Event:
    pass


class Command:
    pass


@dataclass
class CustomerBecameVIP(Event):
    customer_id: int


@dataclass
class OrderCreated(Event):
    customer_id: int
    order_id: int
    order_amount: int


@dataclass
class CreateOrder(Command):
    customer_id: int
    basket_items: List[Any]
