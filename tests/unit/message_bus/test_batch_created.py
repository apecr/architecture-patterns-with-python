from allocation.domain.events import BatchCreated
from tests.unit.message_bus import FakeUnitOfWork


def test_add_batch_for_new_product(message_bus):
    uow = FakeUnitOfWork()
    message_bus.handle(BatchCreated("b1", "CRUNCHY-ARMCHAIR", 100, None), uow)
    assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
    assert uow.committed


def test_add_batch_for_existing_product(message_bus):
    uow = FakeUnitOfWork()
    message_bus.handle(BatchCreated("b1", "GARISH-RUG", 100, None), uow)
    message_bus.handle(BatchCreated("b2", "GARISH-RUG", 99, None), uow)
    assert "b2" in [b.reference for b in uow.products.get("GARISH-RUG").batches]


