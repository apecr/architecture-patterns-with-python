from datetime import datetime

from flask import Flask, request

from allocation.adapters import orm
from allocation.domain.commands import CreateBatch, Allocate
from allocation.service_layer import handlers, unit_of_work
from allocation.service_layer.message_bus import MessageBus

app = Flask(__name__)
orm.start_mappers()


@app.route("/add_batch", methods=["POST"])
def add_batch():
    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()

    message_bus = MessageBus()
    message_bus.handle(CreateBatch(request.json["ref"],
                                   request.json["sku"],
                                   request.json["qty"],
                                   eta),
                       unit_of_work.SqlAlchemyUnitOfWork(),
                       )
    return "OK", 201


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    message_bus = MessageBus()
    try:
        batch_ref = message_bus.handle(
            Allocate(request.json["orderid"], request.json["sku"], request.json["qty"]),
            unit_of_work.SqlAlchemyUnitOfWork(),
        ).pop(0)
    except handlers.InvalidSku as e:
        return {"message": str(e)}, 400
    except Exception as oe:
        return {"message": str(oe)}, 500

    if batch_ref:
        return {"batchref": batch_ref}, 201
    else:
        return {"message": f"Out of stock {request.json['sku']}"}, 400
