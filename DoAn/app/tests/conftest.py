import pytest


def pytest_collection_modifyitems(config, items):
    for item in items:
        parts = item.path.parts
        if "integration" in parts and "tests" in parts:
            item.add_marker(pytest.mark.integration)
