"""Exceptions."""


class StickMeError(Exception):
    """Base class for exceptions in this module."""


class UnsetEnvironmentError(StickMeError):
    """Unset environment error."""
