from datetime import date

from allocation.domain.commands import CreateBatch, ChangeBatchQuantity, Allocate
from tests.unit.message_bus import FakeUnitOfWork, FakeMessageBus


def test_changes_available_quantity(message_bus):
    uow = FakeUnitOfWork()
    batch_created = CreateBatch("batch1", "ADORABLE-SETTEE", 100, None)
    message_bus.handle(batch_created, uow)

    message_bus.handle(ChangeBatchQuantity("batch1", 50), uow)

    batch = uow.products.get(sku="ADORABLE-SETTEE").batches[0]
    assert batch.available_quantity == 50


def test_reallocates_if_necessary(message_bus):
    uow = FakeUnitOfWork()
    event_history = [
        CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
        CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
        Allocate("order1", "INDIFFERENT-TABLE", 20),
        Allocate("order2", "INDIFFERENT-TABLE", 20),
    ]
    for e in event_history:
        message_bus.handle(e, uow)

    [batch1, batch2] = uow.products.get(sku="INDIFFERENT-TABLE").batches
    assert batch1.available_quantity == 10
    assert batch2.available_quantity == 50

    message_bus.handle(ChangeBatchQuantity("batch1", 25), uow)

    assert batch1.available_quantity == 5
    assert batch2.available_quantity == 30


def test_reallocates_if_necessary_isolated(message_bus):
    fake_message_bus = FakeMessageBus()
    uow = FakeUnitOfWork()

    event_history = [
        CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
        CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
        Allocate("order1", "INDIFFERENT-TABLE", 20),
        Allocate("order2", "INDIFFERENT-TABLE", 20),
    ]

    for e in event_history:
        fake_message_bus.handle(e, uow)

    [batch1, batch2] = uow.products.get(sku="INDIFFERENT-TABLE").batches
    assert batch1.available_quantity == 10
    assert batch2.available_quantity == 50

    fake_message_bus.handle(ChangeBatchQuantity("batch1", 25), uow)

    [reallocation_event] = fake_message_bus.events_published
    assert isinstance(reallocation_event, Allocate)
    assert reallocation_event.orderid in {"order1", "order2"}
    assert reallocation_event.sku == "INDIFFERENT-TABLE"
