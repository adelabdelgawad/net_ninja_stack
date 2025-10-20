from datetime import date, datetime, time
from typing import List, Optional

import pytz
from cryptography.fernet import Fernet
from sqlmodel import Field, Relationship, SQLModel

from core.config import settings

# Load encryption key from environment (generate one if not exists)
ENCRYPTION_KEY = settings.encryption_key
cipher_suite = Fernet(
    ENCRYPTION_KEY.encode()
    if isinstance(ENCRYPTION_KEY, str)
    else ENCRYPTION_KEY
)


def cairo_now():
    return datetime.now(tz=pytz.timezone("Africa/Cairo"))


class ISP(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    created_at: datetime = Field(default_factory=cairo_now)
    updated_at: datetime = Field(default_factory=cairo_now)

    lines: List["Line"] = Relationship(back_populates="isp")


class Line(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    line_number: str = Field(unique=True)
    description: str | None = None
    ip_address: str | None = None
    username: bytes | None = None
    password: bytes | None = None
    isp_id: int = Field(foreign_key="isp.id")
    created_at: datetime = Field(default_factory=cairo_now)
    updated_at: datetime = Field(default_factory=cairo_now)
    is_active: bool | None = True

    isp: Optional[ISP] = Relationship(back_populates="lines")
    task_targets: List["TaskTarget"] = Relationship(back_populates="line")
    processes: List["Process"] = Relationship(back_populates="line")
    quota_results: List["QuotaResult"] = Relationship(back_populates="line")
    speed_test_results: List["SpeedTestResult"] = Relationship(
        back_populates="line"
    )

    def set_username(self, username: str):
        self.username = cipher_suite.encrypt(username.encode())
        self.updated_at = cairo_now()

    def set_password(self, password: str):
        self.password = cipher_suite.encrypt(password.encode())
        self.updated_at = cairo_now()

    def get_credentials(self) -> tuple[str, str]:
        """Decrypt and return credentials"""
        if not self.username or not self.password:
            return "", ""
        username = cipher_suite.decrypt(self.username).decode()
        password = cipher_suite.decrypt(self.password).decode()
        return username, password

    def has_credentials(self) -> bool:
        """Check if line has stored credentials"""
        return bool(self.username and self.password)


class TaskStatus(SQLModel, table=True):
    __tablename__ = "task_status"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    description: str | None = None

    tasks: List["Task"] = Relationship(back_populates="status")


class Job(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    description: str | None = None
    created_at: datetime = Field(default_factory=cairo_now)
    updated_at: datetime = Field(default_factory=cairo_now)

    tasks: List["Task"] = Relationship(back_populates="job")


class Schedule(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    execution_time: time | None = None
    execution_date: date | None = None
    is_daily: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=cairo_now)
    updated_at: datetime = Field(default_factory=cairo_now)

    task_schedules: List["TaskSchedule"] = Relationship(
        back_populates="schedule"
    )


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = None
    status_id: int = Field(foreign_key="task_status.id")
    job_id: int = Field(foreign_key="job.id")
    created_at: datetime = Field(default_factory=cairo_now)
    updated_at: datetime = Field(default_factory=cairo_now)

    status: Optional[TaskStatus] = Relationship(back_populates="tasks")
    job: Optional[Job] = Relationship(back_populates="tasks")
    task_targets: List["TaskTarget"] = Relationship(back_populates="task")
    task_schedules: List["TaskSchedule"] = Relationship(back_populates="task")
    processes: List["Process"] = Relationship(back_populates="task")
    task_results: List["TaskResult"] = Relationship(back_populates="task")


class TaskResult(SQLModel, table=True):
    __tablename__ = "task_result"

    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    is_succeed: bool
    created_at: datetime = Field(default_factory=cairo_now)

    task: Optional[Task] = Relationship(back_populates="task_results")


class TaskTarget(SQLModel, table=True):
    __tablename__ = "task_target"

    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    line_id: int = Field(foreign_key="line.id")
    created_at: datetime = Field(default_factory=cairo_now)

    task: Optional[Task] = Relationship(back_populates="task_targets")
    line: Optional[Line] = Relationship(back_populates="task_targets")


class TaskSchedule(SQLModel, table=True):
    __tablename__ = "task_schedule"

    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    schedule_id: int = Field(foreign_key="schedule.id")
    created_at: datetime = Field(default_factory=cairo_now)

    task: Optional[Task] = Relationship(back_populates="task_schedules")
    schedule: Optional[Schedule] = Relationship(
        back_populates="task_schedules"
    )


class Process(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    line_id: int = Field(foreign_key="line.id")
    status: str | None = None  # running, completed, failed, etc.
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=cairo_now)

    task: Optional[Task] = Relationship(back_populates="processes")
    line: Optional[Line] = Relationship(back_populates="processes")
    quota_results: List["QuotaResult"] = Relationship(back_populates="process")
    speed_test_results: List["SpeedTestResult"] = Relationship(
        back_populates="process"
    )
    logs: List["Log"] = Relationship(back_populates="process")


class QuotaResult(SQLModel, table=True):
    __tablename__ = "quota_result"

    id: int | None = Field(default=None, primary_key=True)
    process_id: int = Field(foreign_key="process.id")
    line_id: int = Field(foreign_key="line.id")
    data_used_mb: int | None = None
    usage_percentage: int | None = None
    data_remaining_mb: int | None = None
    balance_amount: int | None = None
    renewal_date: date | None = None
    remaining_days: int | None = None
    renewal_cost_amount: int | None = None
    timestamp: datetime = Field(default_factory=cairo_now)

    process: Optional[Process] = Relationship(back_populates="quota_results")
    line: Optional[Line] = Relationship(back_populates="quota_results")


class SpeedTestResult(SQLModel, table=True):
    __tablename__ = "speed_test_result"

    id: int | None = Field(default=None, primary_key=True)
    process_id: int = Field(foreign_key="process.id")
    line_id: int = Field(foreign_key="line.id")
    ping_ms: int | None = None
    upload_speed_mbps: int | None = None
    download_speed_mbps: int | None = None
    public_ip: str | None = None
    timestamp: datetime = Field(default_factory=cairo_now)

    process: Optional[Process] = Relationship(
        back_populates="speed_test_results"
    )
    line: Optional[Line] = Relationship(back_populates="speed_test_results")


class EmailType(SQLModel, table=True):
    __tablename__ = "email_type"

    id: int | None = Field(default=None, primary_key=True)
    type: str = Field(unique=True)
    description: str | None = None

    emails: List["Email"] = Relationship(back_populates="email_type")


class Email(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    recipient: str
    email_type_id: int = Field(foreign_key="email_type.id")
    created_at: datetime = Field(default_factory=cairo_now)
    updated_at: datetime = Field(default_factory=cairo_now)

    email_type: Optional[EmailType] = Relationship(back_populates="emails")


class Log(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    process_id: int = Field(foreign_key="process.id")
    level: str | None = None  # INFO, WARNING, ERROR, DEBUG
    message: str | None = None
    timestamp: datetime = Field(default_factory=cairo_now)

    process: Optional[Process] = Relationship(back_populates="logs")
