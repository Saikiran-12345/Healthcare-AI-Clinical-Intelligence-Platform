"""
Core Domain Exceptions for Healthcare AI & ML Management System.
"""


class HealthcareAppException(Exception):
    """Base exception for all healthcare application domain errors."""
    def __init__(self, message: str, code: str = "APPLICATION_ERROR", details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


class StorageError(HealthcareAppException):
    """Raised when an operation on the JSON/CSV storage layer fails."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="STORAGE_ERROR", details=details)


class RecordNotFoundError(StorageError):
    """Raised when a requested record is not found in the storage layer."""
    def __init__(self, entity_name: str, record_id: str):
        message = f"{entity_name} with ID '{record_id}' was not found."
        super().__init__(message, details={"entity": entity_name, "id": record_id})


class RecordAlreadyExistsError(StorageError):
    """Raised when attempting to insert a record with a duplicate unique key."""
    def __init__(self, entity_name: str, field_name: str, field_value: str):
        message = f"{entity_name} with {field_name}='{field_value}' already exists."
        super().__init__(message, details={"entity": entity_name, "field": field_name, "value": field_value})


class ValidationError(HealthcareAppException):
    """Raised when data validation fails."""
    def __init__(self, message: str, field_errors: dict = None):
        super().__init__(message, code="VALIDATION_ERROR", details=field_errors or {})
        self.field_errors = field_errors or {}


class AuthenticationError(HealthcareAppException):
    """Raised during authentication failures (invalid credentials, disabled account)."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="AUTH_ERROR", details=details)


class AuthorizationError(HealthcareAppException):
    """Raised when a user lacks permissions to perform an action."""
    def __init__(self, message: str = "You do not have permission to access this resource."):
        super().__init__(message, code="PERMISSION_DENIED")


class PredictionError(HealthcareAppException):
    """Raised when ML model prediction fails."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="PREDICTION_ERROR", details=details)


class NLPProcessingError(HealthcareAppException):
    """Raised when symptom NLP analysis encounters an error."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="NLP_ERROR", details=details)


class AppointmentConflictError(HealthcareAppException):
    """Raised when scheduling an appointment causes a time conflict."""
    def __init__(self, message: str = "Appointment time conflicts with an existing booking."):
        super().__init__(message, code="APPOINTMENT_CONFLICT")
