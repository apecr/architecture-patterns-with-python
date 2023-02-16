from allocation.adapters import email
from ecommerce.messages import CustomerBecameVIP, OrderCreated, CreateOrder


class HistoryEntry:
    def __init__(self, order_id, order_amount):
        self.order_id = order_id
        self.order_amount = order_amount


class Order:
    @classmethod
    def from_basket(cls, customer_id, basket_items):
        return cls


class History:  # Aggregate

    def __init__(self, customer_id: int):
        self.orders = set()  # Set[HistoryEntry]
        self.customer_id = customer_id
        self.events = []

    def record_order(self, order_id: str, order_amount: int):  # (1)
        entry = HistoryEntry(order_id, order_amount)

        if entry in self.orders:
            return

        self.orders.add(entry)

        if len(self.orders) == 3:
            self.events.append(
                CustomerBecameVIP(self.customer_id)
            )


def create_order_from_basket(uow, cmd: CreateOrder):  # (2)
    with uow:
        order = Order.from_basket(cmd.customer_id, cmd.basket_items)
        uow.orders.add(order)
        uow.commit()  # raises OrderCreated


def update_customer_history(uow, event: OrderCreated):  # (3)
    with uow:
        history = uow.order_history.get(event.customer_id)
        history.record_order(event.order_id, event.order_amount)
        uow.commit()  # raises CustomerBecameVIP


def congratulate_vip_customer(uow, event: CustomerBecameVIP):  # (4)
    with uow:
        customer = uow.customers.get(event.customer_id)
        email.send_email(
            customer.email_address,
            f'Congratulations {customer.first_name}!'
        )
