import pytest
from main import get_email

def test_get_email():
    """Tests the get_email function."""
    assert get_email() == "23f3000686@ds.study.iitm.ac.in"