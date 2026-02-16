"""Custom exception classes for DeepThought."""


class DeepThoughtError(Exception):
    """Base exception for DeepThought."""

    pass


class AgentExecutionError(DeepThoughtError):
    """Raised when agent execution fails."""

    def __init__(self, agent_name: str, message: str) -> None:
        self.agent_name = agent_name
        super().__init__(f"Agent '{agent_name}' failed: {message}")


class ToolExecutionError(DeepThoughtError):
    """Raised when a tool fails to execute."""

    def __init__(self, tool_name: str, message: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class VerificationError(DeepThoughtError):
    """Raised when verification fails."""

    pass


class DatabaseError(DeepThoughtError):
    """Raised for database-related errors."""

    pass


class AuthenticationError(DeepThoughtError):
    """Raised when authentication fails (invalid credentials, expired token)."""

    pass


class AuthorizationError(DeepThoughtError):
    """Raised when a user lacks permission to access a resource."""

    pass


class NotFoundError(DeepThoughtError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: str) -> None:
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} not found: {identifier}")
