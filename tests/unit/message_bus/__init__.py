from typing import List

from allocation.adapters import repository
from allocation.domain import events, model
from allocation.domain.commands import CreateBatch, Allocate, ChangeBatchQuantity
from allocation.domain.events import OutOfStock
from allocation.service_layer import unit_of_work
from allocation.service_layer.handlers import allocate, change_batch_quantity, add_batch
from allocation.service_layer.message_bus import AbstractMessageBus, Message


class FakeRepository(repository.AbstractRepository):
    def for_order(self, orderid) -> List[model.Product]:
        return []

    def __init__(self, products):
        self._products = set(products)
        self.seen = set()

    def _add(self, product):
        self._products.add(product)

    def _get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)

    def _get_by_batch_ref(self, batch_ref: str):
        for product in self._products:
            for batch in product.batches:
                if batch.reference == batch_ref:
                    return product
        return None


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


class FakeMessageBus(AbstractMessageBus):
    def __init__(self):
        self.events_published = []
        self.EVENT_HANDLERS = {
            OutOfStock: [lambda e: None],
        }
        self.COMMAND_HANDLERS = {
            CreateBatch: add_batch,
            Allocate: allocate,
            ChangeBatchQuantity: change_batch_quantity
        }

    def handle(self, message: Message, uow: unit_of_work.AbstractUnitOfWork):
        super().handle(message=message, uow=uow)
        new_messages = uow.collect_new_events()
        if new_messages:
            self.events_published.extend(new_messages)
