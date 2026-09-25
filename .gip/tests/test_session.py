import pytest
from gip.session import Session
def test_retry_limit():
    s=Session("x"); s.fail_and_retry(); s.fail_and_retry(); s.fail_and_retry()
    with pytest.raises(RuntimeError): s.fail_and_retry()
