import abc

from allocation.adapters import orm
from allocation.domain import model


class AbstractRepository(abc.ABC):
    def __init__(self):
        self.seen = set()

    def add(self, product: model.Product):
        self._add(product)
        self.seen.add(product)

    def get(self, sku) -> model.Product:
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    def get_by_batch_ref(self, batch_ref: str) -> model.Product:
        product = self._get_by_batch_ref(batch_ref=batch_ref)
        if product:
            self.seen.add(product)
        return product

    @abc.abstractmethod
    def _get_by_batch_ref(self, batch_ref: str):
        raise NotImplementedError

    @abc.abstractmethod
    def _add(self, product: model.Product):
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, sku) -> model.Product:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def _get_by_batch_ref(self, batch_ref: str):
        return (
            self.session.query(model.Product)
                .join(model.Batch)
                .filter(orm.batches.c.reference == batch_ref)
                .first()
        )

    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, product):
        self.session.add(product)

    def _get(self, sku):
        return self.session.query(model.Product).filter_by(sku=sku).first()
