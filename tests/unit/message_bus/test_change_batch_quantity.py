from datetime import date

from allocation.domain.events import BatchCreated, BatchQuantityChanged, AllocationRequired
from allocation.service_layer import message_bus
from tests.unit.message_bus import FakeUnitOfWork, FakeUnitOfWorkWithFakeMessageBus


def test_changes_available_quantity():
    uow = FakeUnitOfWork()
    message_bus.handle(BatchCreated("batch1", "ADORABLE-SETTEE", 100, None), uow)

    message_bus.handle(BatchQuantityChanged("batch1", 50), uow)

    batch = uow.products.get(sku="ADORABLE-SETTEE").batches[0]
    assert batch.available_quantity == 50


def test_reallocates_if_necessary():
    uow = FakeUnitOfWork()
    event_history = [
        BatchCreated("batch1", "INDIFFERENT-TABLE", 50, None),
        BatchCreated("batch2", "INDIFFERENT-TABLE", 50, date.today()),
        AllocationRequired("order1", "INDIFFERENT-TABLE", 20),
        AllocationRequired("order2", "INDIFFERENT-TABLE", 20),
    ]
    for e in event_history:
        message_bus.handle(e, uow)

    [batch1, batch2] = uow.products.get(sku="INDIFFERENT-TABLE").batches
    assert batch1.available_quantity == 10
    assert batch2.available_quantity == 50

    message_bus.handle(BatchQuantityChanged("batch1", 25), uow)

    assert batch1.available_quantity == 5
    assert batch2.available_quantity == 30


def test_reallocates_if_necessary_isolated():
    uow = FakeUnitOfWorkWithFakeMessageBus()

    event_history = [
        BatchCreated("batch1", "INDIFFERENT-TABLE", 50, None),
        BatchCreated("batch2", "INDIFFERENT-TABLE", 50, date.today()),
        AllocationRequired("order1", "INDIFFERENT-TABLE", 20),
        AllocationRequired("order2", "INDIFFERENT-TABLE", 20),
    ]

    for e in event_history:
        message_bus.handle(e, uow)

    [batch1, batch2] = uow.products.get(sku="INDIFFERENT-TABLE").batches
    assert batch1.available_quantity == 10
    assert batch2.available_quantity == 50

    message_bus.handle(BatchQuantityChanged("batch1", 25), uow)

    [reallocation_event] = uow.events_published
    assert isinstance(reallocation_event, AllocationRequired)
    assert reallocation_event.orderid in {"order1", "order2"}
    assert reallocation_event.sku == "INDIFFERENT-TABLE"
