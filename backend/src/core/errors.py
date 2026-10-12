"""Dhruva.AI V2 — Standardized Error Handling Architecture.

Defines the centralized exception hierarchy and error payload structures.
Ensures zero internal leaks (no raw stack traces, SQL errors, or credentials).
"""

from typing import Any, Dict, List, Optional
from fastapi import status


class DhruvaException(Exception):
    """Base exception for all domain and application errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []


class AuthenticationError(DhruvaException):
    """Raised when authentication credentials are missing, invalid, or expired."""

    def __init__(
        self,
        message: str = "Authentication required or credentials invalid",
        code: str = "AUTHENTICATION_FAILED",
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class PermissionDeniedError(DhruvaException):
    """Raised when user lacks the required RBAC role or resource permission."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        code: str = "PERMISSION_DENIED",
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class TenantIsolationError(DhruvaException):
    """Raised when an actor attempts to access or mutate resources of another institution."""

    def __init__(
        self,
        message: str = "Cross-tenant access violation: Access to requested institution resource is forbidden",
        code: str = "TENANT_ACCESS_DENIED",
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class NotFoundError(DhruvaException):
    """Raised when a requested resource does not exist within the tenant scope."""

    def __init__(
        self,
        resource: str = "Resource",
        identifier: Optional[str] = None,
        code: str = "RESOURCE_NOT_FOUND",
    ) -> None:
        msg = f"{resource} not found" if not identifier else f"{resource} '{identifier}' not found"
        super().__init__(
            message=msg,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictError(DhruvaException):
    """Raised when a unique constraint or domain state conflict occurs."""

    def __init__(
        self,
        message: str,
        code: str = "RESOURCE_CONFLICT",
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class ValidationError(DhruvaException):
    """Raised when business logic or input validation fails."""

    def __init__(
        self,
        message: str = "Validation failed for one or more fields",
        code: str = "VALIDATION_FAILED",
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class RateLimitExceededError(DhruvaException):
    """Raised when request rate exceeds allowed limits."""

    def __init__(
        self,
        message: str = "Too many requests. Please wait before retrying.",
        code: str = "RATE_LIMIT_EXCEEDED",
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class AccountSuspendedError(DhruvaException):
    """Raised when an authenticated user has been suspended or deactivated."""

    def __init__(
        self,
        message: str = "Account is suspended or inactive. Please contact your institution administrator.",
        code: str = "ACCOUNT_INACTIVE",
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
        )
