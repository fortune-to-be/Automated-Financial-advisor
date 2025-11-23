"""Pytest configuration"""

import pytest
import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

@pytest.fixture(scope='session')
def setup_env():
    """Setup environment variables for tests"""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
