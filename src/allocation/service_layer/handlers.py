from __future__ import annotations

from dataclasses import asdict

from allocation.adapters import email, redis_eventpublisher
from allocation.domain import model, events
from allocation.domain.commands import Allocate, CreateBatch, ChangeBatchQuantity
from allocation.domain.events import Allocated
from allocation.domain.model import OrderLine
from allocation.service_layer import unit_of_work


class InvalidSku(Exception):
    pass


def add_batch(command: CreateBatch, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get(sku=command.sku)
        if product is None:
            product = model.Product(command.sku, batches=[])
            uow.products.add(product)
        product.batches.append(model.Batch(command.ref, command.sku, command.qty, command.eta))
        uow.commit()


def allocate(
        command: Allocate,
        uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = OrderLine(command.orderid, command.sku, command.qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batch_ref = product.allocate(line)
        uow.commit()
        return batch_ref


def send_out_of_stock_notification(
        event: events.OutOfStock,
        uow: unit_of_work.AbstractUnitOfWork
):
    email.send_email("stock@made.com",
                     f"Out of stock for {event.sku}")


def change_batch_quantity(
        command: ChangeBatchQuantity,
        uow: unit_of_work.AbstractUnitOfWork
):
    with uow:
        product = uow.products.get_by_batch_ref(batch_ref=command.ref)
        product.change_batch_quantity(ref=command.ref, qty=command.qty)
        uow.commit()


def publish_allocated_event(event: Allocated, uow: unit_of_work.AbstractUnitOfWork):
    print("Publishing event line_allocated")
    redis_eventpublisher.publish("line_allocated", event)


def add_allocation_to_read_model(event: Allocated, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        uow.session.execute(
            """
            INSERT INTO allocations_view (orderid, sku, batchref)
            VALUES (:orderid, :sku, :batchref)""",
            dict(orderid=event.orderid, sku=event.sku, batchref=event.batchref))
        uow.commit()


def reallocate(
        event: events.Deallocated,
        uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get(sku=event.sku)
        product.events.append(Allocate(**asdict(event)))
        uow.commit()


def remove_allocation_from_read_model(
        event: events.Deallocated,
        uow: unit_of_work.SqlAlchemyUnitOfWork,
):
    with uow:
        uow.session.execute(
            """
            DELETE FROM allocations_view
            WHERE orderid = :orderid AND sku = :sku
            """,
            dict(orderid=event.orderid, sku=event.sku),
        )
        uow.commit()


def add_allocation_to_redis_read_model(event: Allocated, _):
    redis_eventpublisher.update_readmodel(event.orderid, event.sku, event.batchref)


def remove_allocation_to_redis_from_read_model(event: events.Deallocated, _):
    redis_eventpublisher.update_readmodel(event.orderid, event.sku, None)