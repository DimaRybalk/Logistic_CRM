from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class RoleEnum(str, Enum):
    OWNER = "OWNER"
    DISPATCHER = "DISPATCHER"
    DRIVER = "DRIVER"
    ACCOUNTANT = "ACCOUNTANT"
    VIEWER = "VIEWER"


class CompanyModel(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    members: Mapped[List["CompanyMemberModel"]] = relationship(
        "CompanyMemberModel", back_populates="company", cascade="all, delete-orphan"
    )
    invites: Mapped[List["CompanyInviteModel"]] = relationship(
        "CompanyInviteModel", back_populates="company", cascade="all, delete-orphan"
    )


class CompanyMemberModel(Base):
    __tablename__ = "company_members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[RoleEnum] = mapped_column(
        SQLEnum(RoleEnum, native_enum=False), default=RoleEnum.VIEWER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="companies")
    company: Mapped["CompanyModel"] = relationship(
        "CompanyModel", back_populates="members"
    )


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    companies: Mapped[List["CompanyMemberModel"]] = relationship(
        "CompanyMemberModel", back_populates="user", cascade="all, delete-orphan"
    )


class CompanyInviteModel(Base):
    __tablename__ = "company_invites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    token: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    role: Mapped[RoleEnum] = mapped_column(
        SQLEnum(RoleEnum, native_enum=False), default=RoleEnum.VIEWER, nullable=False
    )
    is_accepted: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    company: Mapped["CompanyModel"] = relationship(
        "CompanyModel", back_populates="invites"
    )
