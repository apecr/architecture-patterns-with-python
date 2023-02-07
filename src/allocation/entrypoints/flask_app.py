from datetime import datetime

from flask import Flask, request

from allocation.adapters import orm
from allocation.domain.events import BatchCreated, AllocationRequired
from allocation.service_layer import handlers, unit_of_work

app = Flask(__name__)
orm.start_mappers()


@app.route("/add_batch", methods=["POST"])
def add_batch():
    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    handlers.add_batch(BatchCreated(request.json["ref"],
                                    request.json["sku"],
                                    request.json["qty"],
                                    eta),
                       unit_of_work.SqlAlchemyUnitOfWork(),
                       )
    return "OK", 201


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        batch_ref = handlers.allocate(
            AllocationRequired(request.json["orderid"], request.json["sku"], request.json["qty"]),
            unit_of_work.SqlAlchemyUnitOfWork(),
        )
    except handlers.InvalidSku as e:
        return {"message": str(e)}, 400
    except Exception as oe:
        return {"message": str(oe)}, 500

    if batch_ref:
        return {"batchref": batch_ref}, 201
    else:
        return {"message": f"Out of stock {request.json['sku']}"}, 400
