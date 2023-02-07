import pytest

from allocation.adapters import repository
from allocation.domain.events import BatchCreated, AllocationRequired
from allocation.service_layer import handlers, unit_of_work, message_bus


class FakeRepository(repository.AbstractRepository):
    def __init__(self, products):
        self._products = set(products)
        self.seen = set()

    def _add(self, product):
        self._products.add(product)

    def _get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_add_batch_for_new_product():
    uow = FakeUnitOfWork()
    message_bus.handle(BatchCreated("b1", "CRUNCHY-ARMCHAIR", 100, None), uow)
    assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
    assert uow.committed


def test_add_batch_for_existing_product():
    uow = FakeUnitOfWork()
    message_bus.handle(BatchCreated("b1", "GARISH-RUG", 100, None), uow)
    message_bus.handle(BatchCreated("b2", "GARISH-RUG", 99, None), uow)
    assert "b2" in [b.reference for b in uow.products.get("GARISH-RUG").batches]


def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()
    message_bus.handle(BatchCreated("batch1", "COMPLICATED-LAMP", 100, None), uow)
    result = handlers.allocate(AllocationRequired("o1", "COMPLICATED-LAMP", 10), uow)
    assert result == "batch1"


def test_allocate_errors_for_invalid_sku():
    uow = FakeUnitOfWork()
    message_bus.handle(BatchCreated("b1", "AREALSKU", 100, None), uow)

    with pytest.raises(handlers.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        handlers.allocate(AllocationRequired("o1", "NONEXISTENTSKU", 10), uow)


def test_allocate_commits():
    uow = FakeUnitOfWork()
    message_bus.handle(BatchCreated("b1", "OMINOUS-MIRROR", 100, None), uow)
    message_bus.handle(AllocationRequired("o1", "OMINOUS-MIRROR", 10), uow)
    assert uow.committed
