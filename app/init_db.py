from app.database import Base, engine
from app.models import Transaction

Base.metadata.create_all(engine)
