from allocation.adapters import repository
from allocation.service_layer import unit_of_work


class FakeRepository(repository.AbstractRepository):
    def __init__(self, products):
        self._products = set(products)
        self.seen = set()

    def _add(self, product):
        self._products.add(product)

    def _get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass