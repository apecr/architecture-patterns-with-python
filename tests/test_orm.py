from app.order_line import OrderLine


def test_orderline_mapper_can_load_lines(session):
    session.execute(
        'INSERT INTO order_lines (order_reference, sku, quantity) VALUES '
        '("order1", "RED-CHAIR", 12),'
        '("order2", "RED-TABLE", 13),'
        '("order3", "BLUE-LIPSTICK", 14)'
    )
    # expected = [
    #     OrderLine("order1", "RED-CHAIR", 12),
    #     OrderLine("order1", "RED-TABLE", 13),
    #     OrderLine("order2", "BLUE-LIPSTICK", 14),
    # ]
    print(session.query(OrderLine).all())


def test_orderline_mapper_can_save_lines(session):
    new_line = OrderLine("order1", "DECORATIVE-WIDGET", 12)
    session.add(new_line)
    session.commit()

    rows = list(session.execute('SELECT order_reference, sku, quantity FROM "order_lines"'))
    assert rows == [("order1", "DECORATIVE-WIDGET", 12)]
