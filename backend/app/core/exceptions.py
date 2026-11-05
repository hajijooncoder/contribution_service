class ContributionError(Exception):
    def __init__(self, message: str, code: str, status_code: int = 400, **kwargs):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.extra = kwargs
        super().__init__(message)

class ValidationError(ContributionError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, "VALIDATION_ERROR", 400, **kwargs)

class QuarantineError(ContributionError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, "QUARANTINE_ERROR", 400, **kwargs)

class DuplicateError(ContributionError):
    def __init__(self, message: str, existing_id: str = None, **kwargs):
        super().__init__(message, "DUPLICATE_DETECTED", 409, existing_id=existing_id, **kwargs)

class QuorumError(ContributionError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, "QUORUM_ERROR", 400, **kwargs)

class ExportGatewayError(ContributionError):
    def __init__(self, message: str, status_code: int = 403, **kwargs):
        super().__init__(message, "EXPORT_GATEWAY_ERROR", status_code, **kwargs)

class RateLimitError(ContributionError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", 429, **kwargs)

class NotFoundError(ContributionError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, "NOT_FOUND", 404, **kwargs)

class ForbiddenError(ContributionError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, "FORBIDDEN", 403, **kwargs)

class UnauthorizedError(ContributionError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, "UNAUTHORIZED", 401, **kwargs)

class InternalError(ContributionError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, "INTERNAL_ERROR", 500, **kwargs)