from sqlalchemy import Column, Integer, String, Table, MetaData, ForeignKey, Date
from sqlalchemy.orm import mapper, relationship

from app.batch import Batch
from app.order_line import OrderLine

metadata = MetaData()

order_lines = Table(
    'order_lines', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('sku', String(255)),
    Column('quantity', Integer, nullable=False),
    Column('order_reference', String(255)),
)
#
# batches = Table(
#     "batches",
#     metadata,
#     Column("id", Integer, primary_key=True, autoincrement=True),
#     Column("reference", String(255)),
#     Column("sku", String(255)),
#     Column("_purchased_quantity", Integer, nullable=False),
#     Column("eta", Date, nullable=True),
# )
#
# allocations = Table(
#     "allocations",
#     metadata,
#     Column("id", Integer, primary_key=True, autoincrement=True),
#     Column("orderline_id", ForeignKey("order_lines.id")),
#     Column("batch_id", ForeignKey("batches.id")),
# )


def start_mappers():
    lines_mapper = mapper(OrderLine, order_lines)
    # mapper(
    #     Batch,
    #     batches,
    #     properties={
    #         "_allocations": relationship(
    #             lines_mapper, secondary=allocations, collection_class=set,
    #         )
    #     },
    # )
