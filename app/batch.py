import dataclasses
import datetime
from functools import reduce

from app.order_line import OrderLine


@dataclasses.dataclass(eq=False)
class Batch:
    reference: str
    sku: str
    original_quantity: int
    eta: datetime.date
    _allocated_order_lines: dict = dataclasses.field(default_factory=lambda: {})

    def allocate(self, order_line: OrderLine):
        if not self._is_order_allocated(order_line) and self._is_same_product(order_line):
            if self.original_quantity < order_line.quantity:
                raise AllocateException()
            self._allocated_order_lines[order_line.order_reference] = order_line

    @property
    def available_quantity(self):
        def __reduce_quantity(acc, line):
            return acc + line.quantity
        consumed_quantity = reduce(__reduce_quantity, self._allocated_order_lines.values(), 0)
        return self.original_quantity - consumed_quantity

    def can_allocate(self, order_line):
        if order_line.sku == self.sku:
            return self.available_quantity >= order_line.quantity
        return False

    def _is_order_allocated(self, order_line):
        return order_line.order_reference in self._allocated_order_lines

    def _is_same_product(self, order_line):
        return order_line.sku == self.sku

    def deallocate(self, order_line):
        if self._is_order_allocated(order_line):
            del self._allocated_order_lines[order_line.order_reference]


class AllocateException(Exception):
    pass
