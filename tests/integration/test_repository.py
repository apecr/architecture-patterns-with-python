# pylint: disable=protected-access
from allocation.adapters import repository
from allocation.domain import model


def test_repository_can_save_a_batch(session):
    batch = model.Batch("batch1", "RUSTY-SOAPDISH", 100, eta=None)
    product = model.Product(sku=batch.sku, batches=[batch])

    repo = repository.SqlAlchemyProductRepository(session)
    repo.add(product)
    session.commit()

    rows = session.execute(
        'SELECT reference, sku, _purchased_quantity, eta FROM "batches"'
    )
    assert list(rows) == [("batch1", "RUSTY-SOAPDISH", 100, None)]


def insert_order_line(session):
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty)"
        ' VALUES ("order1", "GENERIC-SOFA", 12)'
    )
    [[orderline_id]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid="order1", sku="GENERIC-SOFA"),
    )
    return orderline_id


def insert_batch(session, batch_id):
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        ' VALUES (:batch_id, "GENERIC-SOFA", 100, null)',
        dict(batch_id=batch_id),
    )
    [[batch_id]] = session.execute(
        'SELECT id FROM batches WHERE reference=:batch_id AND sku="GENERIC-SOFA"',
        dict(batch_id=batch_id),
    )
    return batch_id


def insert_product(session, product_id):
    session.execute(
        "INSERT INTO products (sku)"
        ' VALUES (:product_id)',
        dict(product_id=product_id),
    )
    [[product_id]] = session.execute(
        'SELECT id FROM products WHERE sku=:product_id',
        dict(product_id=product_id),
    )
    return product_id


def insert_allocation(session, orderline_id, batch_id):
    session.execute(
        "INSERT INTO allocations (orderline_id, batch_id)"
        " VALUES (:orderline_id, :batch_id)",
        dict(orderline_id=orderline_id, batch_id=batch_id),
    )


SKU = "GENERIC-SOFA"


def test_repository_can_retrieve_a_batch_with_allocations(session):
    orderline_id = insert_order_line(session)
    batch1_id = insert_batch(session, "batch1")
    batch2_id = insert_batch(session, "batch2")
    insert_allocation(session, orderline_id, batch1_id)
    insert_product(session, SKU)

    repo = repository.SqlAlchemyProductRepository(session)
    retrieved_product = repo.get(SKU)

    print(retrieved_product)
    batches = [model.Batch(batch1_id, SKU, 100, None), model.Batch(batch2_id, SKU, 100, None)]
    print(batches)

    expected = model.Product(sku=SKU, batches=batches)
    print(expected)
    # assert retrieved_product == expected
    assert retrieved_product.sku == expected.sku
    assert len(retrieved_product.batches) == 2
