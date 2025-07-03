import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from communication_platform.shared import database

@pytest.fixture(scope="module")
def test_messages():
    return [
        {"from": f"+1234567{i:04d}", "body": f"Message {i}"} for i in range(1000)
    ]

def test_database_insert_performance(test_messages, benchmark):
    session = database.get_session()
    def insert_all():
        for msg in test_messages:
            session.execute("INSERT INTO messages (sender, content) VALUES (:from, :body)", msg)
        session.commit()
    benchmark(insert_all)
    session.close()

def test_database_select_performance(benchmark):
    session = database.get_session()
    def select_all():
        session.execute("SELECT * FROM messages").fetchall()
    benchmark(select_all)
    session.close() 