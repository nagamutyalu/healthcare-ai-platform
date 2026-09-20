from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import URL

DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username="healthcare_app",
    password="HealthApp@2026",
    host="127.0.0.1",
    port=3306,
    database="healthcare_ai",
)

engine = create_engine(
    DATABASE_URL,
    echo=True,
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
