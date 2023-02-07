import pytest

from allocation.domain.events import BatchCreated, AllocationRequired
from allocation.service_layer import handlers
from tests.unit.message_bus import FakeUnitOfWork


def test_allocate_returns_allocation(message_bus):
    uow = FakeUnitOfWork()
    message_bus.handle(BatchCreated("batch1", "COMPLICATED-LAMP", 100, None), uow)
    result = message_bus.handle(AllocationRequired("o1", "COMPLICATED-LAMP", 10), uow)
    assert result[0] == "batch1"


def test_allocate_errors_for_invalid_sku(message_bus):
    uow = FakeUnitOfWork()
    message_bus.handle(BatchCreated("b1", "AREALSKU", 100, None), uow)

    with pytest.raises(handlers.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        message_bus.handle(AllocationRequired("o1", "NONEXISTENTSKU", 10), uow)


def test_allocate_commits(message_bus):
    uow = FakeUnitOfWork()
    message_bus.handle(BatchCreated("b1", "OMINOUS-MIRROR", 100, None), uow)
    message_bus.handle(AllocationRequired("o1", "OMINOUS-MIRROR", 10), uow)
    assert uow.committed
