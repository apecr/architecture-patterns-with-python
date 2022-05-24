def allocate(order_line, batches):
    def _get_soonest_batch():
        filtered_batches = list(filter(lambda batch: batch.can_allocate(order_line), batches))
        if not filtered_batches:
            return None
        return min(iter(sorted(filtered_batches)))

    batch_to_allocate = _get_soonest_batch()
    if batch_to_allocate is None:
        raise OutOfStock(f'Out of stock for sku {order_line.sku}')
    batch_to_allocate.allocate(order_line)
    return batch_to_allocate.reference


class OutOfStock(Exception):
    pass
