from allocation.domain import events
from allocation.service_layer import unit_of_work
from allocation.service_layer.handlers import send_out_of_stock_notification, add_batch, allocate


def handle(event: events.Event, uow: unit_of_work.AbstractUnitOfWork):
    queue = [event]
    while queue:
        event = queue.pop(0)
        for handler in HANDLERS[type(event)]:
            handler(event, uow=uow)
            queue.extend(uow.collect_new_events())


HANDLERS = {
    events.OutOfStock: [send_out_of_stock_notification],
    events.BatchCreated: [add_batch],
    events.AllocationRequired: [allocate]
}
