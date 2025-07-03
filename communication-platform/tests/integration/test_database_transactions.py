import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from sqlalchemy.orm import Session
from communication_platform.shared import database

def test_database_transaction_commit_and_rollback():
    session = database.get_session()
    try:
        session.begin()
        # Simulate insert
        session.execute("SELECT 1")
        session.commit()
    except Exception:
        session.rollback()
        assert False, "Transaction should not fail"
    finally:
        session.close()
    # Simulate rollback
    session = database.get_session()
    try:
        session.begin()
        session.execute("SELECT 1")
        raise Exception("Force rollback")
    except Exception:
        session.rollback()
    finally:
        session.close() 