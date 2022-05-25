import dataclasses


@dataclasses.dataclass(unsafe_hash=True)
class OrderLine:
    order_reference: str
    sku: str
    quantity: int
