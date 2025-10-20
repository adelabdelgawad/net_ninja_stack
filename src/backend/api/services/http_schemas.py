from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class Model(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
        # Add this to handle validation properly
        str_strip_whitespace=True,
    )


# Line Schemas
class LineCreate(Model):
    line_number: str
    name: str
    description: str | None = None
    ip_address: str | None = None
    isp_id: int
    username: str | None = None
    password: str | None = None


class LineUpdate(Model):
    line_number: str | None = None
    name: str | None = None
    description: str | None = None
    ip_address: str | None = None
    isp_id: int | None = None
    username: str | None = None
    password: str | None = None
    is_active: bool | None = None


class LineResponse(Model):
    id: int
    line_number: str
    name: str
    description: str | None = None
    ip_address: str | None = None
    isp_id: int
    has_credentials: bool
    username: str | None = None
    password: str | None = None
    created_at: datetime
    updated_at: datetime
    is_active: bool


class LineSummary(Model):
    id: int
    line_number: str
    name: str
    isp_id: int
    has_credentials: bool
    is_active: bool


class LinesDashboardResponse(Model):
    all_lines: int | None = 0
    active_lines: int | None = 0
    inactive_lines: int | None = 0


class EmailCreate(Model):
    recipient: str
    email_type_id: int


class EmailUpdate(Model):
    recipient: str | None = None
    email_type_id: int | None = None


class EmailResponse(Model):
    id: int
    recipient: str
    email_type_id: int


# Task Schemas
class TaskCreate(Model):
    name: str
    description: str | None = None
    status_id: int
    job_id: int


class TaskUpdate(Model):
    name: str | None = None
    description: str | None = None
    status_id: int | None = None
    job_id: int | None = None


class TaskResponse(Model):
    id: int
    name: str
    description: str | None = None
    status_id: int
    job_id: int
    created_at: datetime
    updated_at: datetime


class TaskSummary(Model):
    id: int
    name: str
    status_id: int
    job_id: int


# TaskTarget Schemas
class TaskTargetCreate(Model):
    task_id: int
    line_id: int


class TaskTargetResponse(Model):
    id: int
    task_id: int
    line_id: int
    created_at: datetime


class TaskTargetSummary(Model):
    id: int
    task_id: int
    line_id: int


# Schedule Schemas
class ScheduleCreate(Model):
    name: str
    execution_time: time | None = None
    execution_date: date | None = None
    is_daily: bool = False
    is_active: bool = True


class ScheduleUpdate(Model):
    name: str | None = None
    execution_time: time | None = None
    execution_date: date | None = None
    is_daily: bool | None = None
    is_active: bool | None = None


class ScheduleResponse(Model):
    id: int
    name: str
    execution_time: time | None = None
    execution_date: date | None = None
    is_daily: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ScheduleSummary(Model):
    id: int
    name: str
    execution_time: time | None = None
    is_daily: bool
    is_active: bool


class EmailSummary(Model):
    id: int
    recipient: str
    email_type_id: int


class LogResponse(Model):
    id: int
    process_id: int
    message: str | None = None
    timestamp: datetime


class LogSummary(Model):
    id: int
    process_id: int
    message: str | None = None
    timestamp: datetime


# Job Schemas


class JobResponse(Model):
    id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class JobSummary(Model):
    id: int
    name: str
    description: str | None = None


# TaskStatus Schemas
class TaskStatusResponse(Model):
    id: int
    name: str
    description: str | None = None


class TaskStatusSummary(Model):
    id: int
    name: str
    description: str | None = None


# TaskResult Schemas


class TaskResultResponse(Model):
    id: int
    task_id: int
    is_succeed: bool
    created_at: datetime


class TaskResultSummary(Model):
    id: int
    task_id: int
    is_succeed: bool
    created_at: datetime
