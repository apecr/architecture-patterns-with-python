import logging
from typing import List, Callable, Dict, Type, Union, Any

from tenacity import Retrying, RetryError, stop_after_attempt, wait_exponential

from allocation.domain.commands import Command, Allocate, ChangeBatchQuantity, CreateBatch
from allocation.domain.events import Event, OutOfStock
from allocation.service_layer import unit_of_work
from allocation.service_layer.handlers import send_out_of_stock_notification, add_batch, allocate, change_batch_quantity

logger = logging.getLogger(__name__)

Message = Union[Event, Command]


class AbstractMessageBus:
    EVENT_HANDLERS: Dict[Type[Event], List[Callable]]
    COMMAND_HANDLERS: Dict[Type[Command], Callable]

    def handle(self, message: Message, uow: unit_of_work.AbstractUnitOfWork):
        if isinstance(message, Event):
            self.handle_event(message, [], uow)
        if isinstance(message, Command):
            self.handle_command(message, [], uow)

    def handle_event(self, event: Event, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork):
        for handler in self.EVENT_HANDLERS[type(event)]:
            handler(event, uow=uow)

    def handle_command(self, command: Command, queue: List[Message],
                       uow: unit_of_work.AbstractUnitOfWork) -> Any:
        handler = self.COMMAND_HANDLERS[type(command)]
        handler(command, uow=uow)


class MessageBus(AbstractMessageBus):
    EVENT_HANDLERS = {
        OutOfStock: [send_out_of_stock_notification],
    }  # type: Dict[Type[Event], List[Callable]]

    COMMAND_HANDLERS = {
        Allocate: allocate,
        CreateBatch: add_batch,
        ChangeBatchQuantity: change_batch_quantity
    }  # type: Dict[Type[Command], Callable]

    def handle(self, message: Message, uow: unit_of_work.AbstractUnitOfWork):
        results = []
        queue = [message]
        while queue:
            message = queue.pop(0)
            if isinstance(message, Event):
                self.handle_event(message, queue, uow)
            elif isinstance(message, Command):
                cmd_result = self.handle_command(message, queue, uow)
                results.append(cmd_result)
            else:
                raise Exception(f"{message} was not an Event or a Command")
        return results

    def handle_event(self, event: Event, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork):
        for handler in self.EVENT_HANDLERS[type(event)]:
            try:
                for attempt in Retrying(
                        stop=stop_after_attempt(3),
                        wait=wait_exponential()
                ):
                    with attempt:
                        logger.debug("handling event %s with handler %s", event, handler)
                        handler(event, uow=uow)
                        queue.extend(uow.collect_new_events())
            except RetryError as retry_failure:
                logger.error("Failed to handle event %s times, giving up!", retry_failure.last_attempt.attempt_number)
                continue

    def handle_command(self, command: Command, queue: List[Message],
                       uow: unit_of_work.AbstractUnitOfWork) -> Any:
        logger.debug("handling command %s", command)
        try:
            handler = self.COMMAND_HANDLERS[type(command)]
            result = handler(command, uow=uow)
            queue.extend(uow.collect_new_events())
            return result
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise
