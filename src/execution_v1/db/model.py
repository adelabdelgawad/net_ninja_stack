# db/model.py
from datetime import datetime

import pytz
from sqlmodel import Field, Relationship, SQLModel


def cairo_now():
    """Get current time in Cairo timezone."""
    return datetime.now(tz=pytz.timezone("Africa/Cairo"))


# ------------------------------------------------------------------------------
# ISP Model
# ------------------------------------------------------------------------------


class ISP(SQLModel, table=True):
    """Internet Service Provider model"""

    __tablename__ = "isp"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)

    # Relationships
    lines: list["Line"] = Relationship(back_populates="isp")


# ------------------------------------------------------------------------------
# Line Model
# ------------------------------------------------------------------------------


class Line(SQLModel, table=True):
    """Internet line/connection model"""

    __tablename__ = "lines"

    id: int | None = Field(default=None, primary_key=True)
    line_number: str = Field(index=True)
    name: str
    description: str
    isp_id: int = Field(foreign_key="isp.id")
    ip_address: str
    portal_username: str
    portal_password: str
    gateway_ip: str

    # Relationships
    isp: "ISP" = Relationship(back_populates="lines")
    speed_test_results: list["SpeedTestResult"] = Relationship(
        back_populates="line",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    quota_results: list["QuotaResult"] = Relationship(
        back_populates="line",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    def __repr__(self) -> str:
        return f"Line(id={self.id!r}, name={self.name!r}, description={self.description!r})"


# ------------------------------------------------------------------------------
# QuotaResult Model
# ------------------------------------------------------------------------------


class QuotaResult(SQLModel, table=True):
    """Quota check result model"""

    __tablename__ = "quota_results"

    id: int | None = Field(default=None, primary_key=True)
    process_id: str = Field(index=True)
    line_id: int = Field(foreign_key="lines.id")
    data_used: int | None = None
    usage_percentage: int | None = None
    data_remaining: int | None = None
    balance: int | None = None
    renewal_date: str | None = None
    remaining_days: int | None = None
    renewal_cost: int | None = None
    created_date: datetime = Field(default_factory=cairo_now)

    # Relationships
    line: "Line" = Relationship(back_populates="quota_results")

    def __repr__(self):
        return f"QuotaResult(id={self.id!r}, line_id={self.line_id!r}, process_id={self.process_id!r})"


# ------------------------------------------------------------------------------
# SpeedTestResult Model
# ------------------------------------------------------------------------------


class SpeedTestResult(SQLModel, table=True):
    """Speed test result model"""

    __tablename__ = "speed_test_results"

    id: int | None = Field(default=None, primary_key=True)
    process_id: str = Field(index=True)
    line_id: int = Field(foreign_key="lines.id")
    ping: int | None = None
    upload_speed: int | None = None
    download_speed: int | None = None
    public_ip: str | None = None
    created_date: datetime = Field(default_factory=cairo_now)

    # Relationships
    line: "Line" = Relationship(back_populates="speed_test_results")

    def __repr__(self):
        return f"SpeedTestResult(id={self.id!r}, line_id={self.line_id!r}, process_id={self.process_id!r})"


# ------------------------------------------------------------------------------
# Email Model
# ------------------------------------------------------------------------------


class Email(SQLModel, table=True):
    """Email recipient model"""

    __tablename__ = "email"

    id: int | None = Field(default=None, primary_key=True)
    recipient: str = Field(index=True)


# ------------------------------------------------------------------------------
# Log Model
# ------------------------------------------------------------------------------


class Log(SQLModel, table=True):
    """Application log model"""

    __tablename__ = "logs"

    id: int | None = Field(default=None, primary_key=True)
    process_id: str | None = Field(default=None, max_length=50, index=True)
    function: str | None = None
    level: str | None = None
    message: str | None = None
    created_date: datetime = Field(default_factory=cairo_now)

    def __repr__(self):
        return (
            f"Log(id={self.id!r}, process_id={self.process_id!r}, "
            f"level={self.level!r}, message={self.message!r}, "
            f"created_date={self.created_date!r})"
        )
