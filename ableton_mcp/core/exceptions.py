"""Core exceptions for the Ableton MCP system."""

from typing import Any, Dict, Optional


class AbletonMCPError(Exception):
    """Base exception for all Ableton MCP errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


class ConnectionError(AbletonMCPError):
    """Raised when connection to Ableton Live fails."""


class OSCCommunicationError(AbletonMCPError):
    """Raised when OSC communication fails."""


class InvalidParameterError(AbletonMCPError):
    """Raised when invalid parameters are provided."""


class MusicTheoryError(AbletonMCPError):
    """Raised when music theory analysis fails."""


class DeviceNotFoundError(AbletonMCPError):
    """Raised when a device is not found."""


class TrackNotFoundError(AbletonMCPError):
    """Raised when a track is not found."""


class ClipNotFoundError(AbletonMCPError):
    """Raised when a clip is not found."""


class ConfigurationError(AbletonMCPError):
    """Raised when configuration is invalid."""


class ValidationError(AbletonMCPError):
    """Raised when validation fails."""