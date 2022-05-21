def allocate(order_line, batches):
    def _get_soonest_batch(batch_lines):
        return next(iter(sorted(filter(lambda batch: batch.can_allocate(order_line), batch_lines))))

    batch_to_allocate = _get_soonest_batch(batches)
    batch_to_allocate.allocate(order_line)

    return batch_to_allocate.reference
