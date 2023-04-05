from allocation.domain import model
from allocation.service_layer import unit_of_work


def allocations(order_id: str, uow: unit_of_work.SqlAlchemyUnitOfWork):
    with uow:
        results = uow.session.execute(
            """
            SELECT ol.sku, b.reference
            FROM allocations as a 
            JOIN batches as b ON a.batch_id = b.id
            JOIN order_lines AS ol ON a.orderline_id = ol.id
            WHERE ol.orderid = :orderid""",
            {"orderid": order_id}
        )
    return [{"sku": sku, "batchref": batchref} for sku, batchref in results]


def repo_allocations(order_id: str, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        products = uow.products.for_order(orderid=order_id)  # (1)
        batches = [b for p in products for b in p.batches]  # (2)
        return [
            {'sku': b.sku, 'batchref': b.reference}
            for b in batches
            if order_id in b.orderids  # (3)
        ]


def orm_allocations(order_id: str, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        batches = uow.session.query(model.Batch).join(
            model.OrderLine, model.Batch._allocations
        ).filter(
            model.OrderLine.orderid == order_id
        )
        return [
            {"sku": b.sku, "batchref": b.batchref}
            for b in batches
        ]


def replica_view_allocations(order_id: str, uow: unit_of_work.SqlAlchemyUnitOfWork):
    with uow:
        results = uow.session.execute(
            """
            SELECT sku, batchref FROM allocations_view WHERE orderid = :order_id
            """,
            dict(order_id=order_id),
        )
    return [{"sku": sku, "batchref": batchref} for sku, batchref in results]
