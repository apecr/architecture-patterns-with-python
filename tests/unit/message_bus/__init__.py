from allocation.adapters import repository
from allocation.domain import events
from allocation.domain.events import OutOfStock
from allocation.service_layer import unit_of_work
from allocation.service_layer.handlers import allocate, change_batch_quantity, add_batch
from allocation.service_layer.message_bus import AbstractMessageBus


class FakeRepository(repository.AbstractRepository):
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


class FakeUnitOfWorkWithFakeMessageBus(FakeUnitOfWork):
    def __init__(self):
        super().__init__()
        self.events_published = []

    def collect_new_events(self):
        for product in self.products.seen:
            while product.events:
                self.events_published.append(product.events.pop(0))


class FakeMessageBus(AbstractMessageBus):
    def __init__(self):
        self.events_published = []
        self.HANDLERS = {
            OutOfStock: [lambda e: None],
            events.BatchCreated: [add_batch],
            events.AllocationRequired: [allocate],
            events.BatchQuantityChanged: [change_batch_quantity]
        }

    def handle(self, event: events.Event, uow: unit_of_work.AbstractUnitOfWork):
        for handler in self.HANDLERS[type(event)]:
            handler(event, uow=uow)
            new_events = uow.collect_new_events()
            if new_events:
                self.events_published.extend(new_events)
