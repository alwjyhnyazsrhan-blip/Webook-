# database/models.py
try:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()
except ImportError:
    class MockMetadata:
        def create_all(self, bind):
            pass
    class MockBase:
        metadata = MockMetadata()
    Base = MockBase()
