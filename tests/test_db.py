import pytest

from reviews.db import get_pgvector_version

pytestmark = pytest.mark.integration


def test_pgvector_yuklu():
    assert get_pgvector_version()
