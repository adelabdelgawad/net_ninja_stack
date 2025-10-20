# db/validators.py
import re
from pydantic import BaseModel, Field, field_validator


class LineCreate(BaseModel):
    """Validation schema for line creation"""
    line_number: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    isp_id: int = Field(..., gt=0)
    ip_address: str
    portal_username: str = Field(..., min_length=1)
    portal_password: str = Field(..., min_length=1)
    gateway_ip: str

    @field_validator('ip_address', 'gateway_ip')
    @classmethod
    def validate_ip(cls, v):
        """Validate IP address format"""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid IP address format')
        octets = v.split('.')
        if not all(0 <= int(octet) <= 255 for octet in octets):
            raise ValueError('IP address octets must be 0-255')
        return v

    @field_validator('line_number')
    @classmethod
    def validate_line_number(cls, v):
        """Validate line number format"""
        if not v.strip():
            raise ValueError('Line number cannot be empty')
        return v.strip()


class EmailCreate(BaseModel):
    """Validation schema for email recipient"""
    recipient: str

    @field_validator('recipient')
    @classmethod
    def validate_email(cls, v):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
