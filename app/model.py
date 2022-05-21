from operator import attrgetter


def none_aware_attrgetter(attr):
    getter = attrgetter(attr)

    def key_func(item):
        value = getter(item)
        return value is not None, value

    return key_func


def allocate(order_line, batches):
    def _get_soonest_batch(batch_lines):
        return min(batch_lines, key=none_aware_attrgetter('eta'))

    batch_to_allocate = _get_soonest_batch(batches)
    batch_to_allocate.allocate(order_line)

    return batch_to_allocate.reference
