"""CSV Validator - Core validation logic (from di/vladiate MIT license)"""

from typing import List, Set, Any
from dataclasses import dataclass


class ValidationException(Exception):
    """Raised when validation fails"""
    pass


@dataclass
class ValidationResult:
    """Result of validation"""
    passed: bool
    errors: List[str]
    warnings: List[str]
    row_count: int


class Validator:
    """Base validator class"""
    
    def __init__(self, empty_ok: bool = False):
        self.empty_ok = empty_ok
        self.invalid_set: Set[Any] = set()
    
    def validate(self, field: Any, row: dict = None) -> bool:
        raise NotImplementedError
    
    @property
    def bad(self) -> Set[Any]:
        return self.invalid_set


class FloatValidator(Validator):
    """Validates field can be cast to float"""
    
    def validate(self, field: Any, row: dict = None) -> bool:
        try:
            if field or not self.empty_ok:
                float(field)
            return True
        except (ValueError, TypeError):
            self.invalid_set.add(field)
            return False


class IntValidator(Validator):
    """Validates field can be cast to int"""
    
    def validate(self, field: Any, row: dict = None) -> bool:
        try:
            if field or not self.empty_ok:
                int(field)
            return True
        except (ValueError, TypeError):
            self.invalid_set.add(field)
            return False


class CSVValidator:
    """Main CSV validator"""
    
    def __init__(self):
        self.column_validators = {}
        self.errors = []
    
    def add_column_validator(self, column: str, validator: Validator):
        self.column_validators[column] = validator
    
    def validate_row(self, row: dict) -> bool:
        for column, validator in self.column_validators.items():
            if column in row:
                if not validator.validate(row[column], row):
                    self.errors.append(f"Column {column}: invalid")
                    return False
        return True
