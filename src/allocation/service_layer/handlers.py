from __future__ import annotations

from allocation.adapters import email
from allocation.domain import model, events
from allocation.domain.model import OrderLine
from allocation.service_layer import unit_of_work


class InvalidSku(Exception):
    pass


def add_batch(event: events.BatchCreated, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get(sku=event.sku)
        if product is None:
            product = model.Product(event.sku, batches=[])
            uow.products.add(product)
        product.batches.append(model.Batch(event.ref, event.sku, event.qty, event.eta))
        uow.commit()


def allocate(
        event: events.AllocationRequired,
        uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = OrderLine(event.orderid, event.sku, event.qty)
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
