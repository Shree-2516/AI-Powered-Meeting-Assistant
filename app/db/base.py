# Import all the models, so that Base has them before being
# imported by Alembic or used for table creation
from app.db.base_class import Base  # noqa
from app.db.models import MeetingRecord  # noqa
