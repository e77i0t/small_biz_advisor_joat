import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import pytest
from communication_platform.shared import database
from sqlalchemy.orm import Session

def test_engine_and_session():
    engine = database.get_engine()
    assert engine is not None
    session = database.get_session()
    assert isinstance(session, Session)
    session.close()

def test_get_db_dependency():
    gen = database.get_db()
    session = next(gen)
    assert isinstance(session, Session)
    session.close()
    with pytest.raises(StopIteration):
        next(gen) 