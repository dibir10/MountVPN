from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User_table(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int]
    username: Mapped[str] = mapped_column(String(150))
    vpn_key: Mapped[str] = mapped_column(String(150))
    started_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    ends_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

