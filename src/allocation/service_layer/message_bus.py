from typing import List, Callable, Dict, Type

from allocation.domain import events
from allocation.service_layer import unit_of_work
from allocation.service_layer.handlers import send_out_of_stock_notification, add_batch, allocate, change_batch_quantity


class AbstractMessageBus:
    HANDLERS: Dict[Type[events.Event], List[Callable]]

    def handle(self, event: events.Event, uow: unit_of_work.AbstractUnitOfWork):
        for handler in self.HANDLERS[type(event)]:
            handler(event, uow=uow)


class MessageBus(AbstractMessageBus):
    HANDLERS = {
        events.OutOfStock: [send_out_of_stock_notification],
        events.BatchCreated: [add_batch],
        events.AllocationRequired: [allocate],
        events.BatchQuantityChanged: [change_batch_quantity]
    }

    def handle(self, event: events.Event, uow: unit_of_work.AbstractUnitOfWork):
        results = []
        queue = [event]
        while queue:
            event = queue.pop(0)
            for handler in self.HANDLERS[type(event)]:
                results.append(handler(event, uow=uow))
                new_events = uow.collect_new_events()
                if new_events:
                    queue.extend(new_events)
        return results
