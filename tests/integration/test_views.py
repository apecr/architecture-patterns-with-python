from datetime import date

from allocation import views
from allocation.domain import commands
from allocation.service_layer import unit_of_work

today = date.today()


def test_allocations_view(session_factory, message_bus):
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    message_bus.handle(commands.CreateBatch("sku1batch", "sku1", 50, None), uow)  # (1)
    message_bus.handle(commands.CreateBatch("sku2batch", "sku2", 50, today), uow)
    message_bus.handle(commands.Allocate("order1", "sku1", 20), uow)
    message_bus.handle(commands.Allocate("order1", "sku2", 20), uow)
    # add a spurious batch and order to make sure we're getting the right ones
    message_bus.handle(commands.CreateBatch("sku1batch-later", "sku1", 50, today), uow)
    message_bus.handle(commands.Allocate("otherorder", "sku1", 30), uow)
    message_bus.handle(commands.Allocate("otherorder", "sku2", 10), uow)

    assert views.allocations("order1", uow) == [
        {"sku": "sku1", "batchref": "sku1batch"},
        {"sku": "sku2", "batchref": "sku2batch"},
    ]