import pytest

from allocation.service_layer.message_bus import MessageBus


@pytest.fixture
def message_bus():
    return MessageBus()
