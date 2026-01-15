"""Validation layer for NSE option chain response data."""

from __future__ import annotations

from typing import Any, Dict, List


class ValidationError(RuntimeError):
    """Base exception for validation errors."""


class MissingKeyError(ValidationError):
    """Raised when a required key is missing from the response."""

    def __init__(self, key: str, path: str = ""):
        self.key = key
        self.path = path
        message = f"Missing required key: '{key}'"
        if path:
            message += f" at path: {path}"
        super().__init__(message)


class InvalidTypeError(ValidationError):
    """Raised when a value has an incorrect data type."""

    def __init__(self, key: str, expected_type: type, actual_type: type, path: str = ""):
        self.key = key
        self.expected_type = expected_type
        self.actual_type = actual_type
        self.path = path
        message = (
            f"Invalid type for key '{key}': expected {expected_type.__name__}, "
            f"got {actual_type.__name__}"
        )
        if path:
            message += f" at path: {path}"
        super().__init__(message)


class EmptyDataError(ValidationError):
    """Raised when required data is empty or missing."""

    def __init__(self, key: str, path: str = ""):
        self.key = key
        self.path = path
        message = f"Empty or missing data for key: '{key}'"
        if path:
            message += f" at path: {path}"
        super().__init__(message)


# Required top-level keys in NSE option chain response
_REQUIRED_TOP_LEVEL_KEYS = {"records"}

# Required keys within records
_REQUIRED_RECORDS_KEYS = {"data"}

# Expected types for top-level keys
_EXPECTED_TYPES: Dict[str, type] = {
    "records": dict,
    "filtered": dict,
}

# Expected types within records
_EXPECTED_RECORDS_TYPES: Dict[str, type] = {
    "data": list,
}


def _get_path_string(path: List[str]) -> str:
    """Convert path list to dot-notation string."""
    return ".".join(path) if path else ""


def _validate_key_exists(
    data: Dict[str, Any],
    key: str,
    path: List[str],
    required: bool = True,
) -> None:
    """Validate that a key exists in the data dictionary."""
    if key not in data:
        if required:
            raise MissingKeyError(key, _get_path_string(path))
    return None


def _validate_type(
    value: Any,
    key: str,
    expected_type: type,
    path: List[str],
    allow_none: bool = False,
) -> None:
    """Validate that a value has the expected type."""
    if value is None:
        if not allow_none:
            raise InvalidTypeError(
                key, expected_type, type(None), _get_path_string(path)
            )
        return None

    if not isinstance(value, expected_type):
        raise InvalidTypeError(
            key, expected_type, type(value), _get_path_string(path)
        )
    return None


def _validate_not_empty(
    value: Any,
    key: str,
    path: List[str],
) -> None:
    """Validate that a value is not empty."""
    if value is None:
        raise EmptyDataError(key, _get_path_string(path))

    if isinstance(value, (list, dict, str)):
        if len(value) == 0:
            raise EmptyDataError(key, _get_path_string(path))

    return None


def _validate_records_structure(records: Dict[str, Any], path: List[str]) -> None:
    """Validate the structure of the records object."""
    # Check required keys in records
    for key in _REQUIRED_RECORDS_KEYS:
        _validate_key_exists(records, key, path + ["records"], required=True)

    # Validate types in records
    for key, expected_type in _REQUIRED_RECORDS_KEYS.items():
        if key in records:
            _validate_type(
                records[key],
                key,
                expected_type,
                path + ["records"],
                allow_none=False,
            )

    # Validate data array is not empty
    if "data" in records:
        _validate_not_empty(records["data"], "data", path + ["records"])

        # Validate each record in data array has expected structure
        for idx, record in enumerate(records["data"]):
            record_path = path + ["records", "data", str(idx)]
            _validate_type(record, "record", dict, record_path, allow_none=False)

            # Each record should have at least CE or PE
            if not isinstance(record, dict):
                continue

            has_ce = "CE" in record and record["CE"] is not None
            has_pe = "PE" in record and record["PE"] is not None

            if not (has_ce or has_pe):
                raise EmptyDataError(
                    "CE or PE",
                    _get_path_string(record_path),
                )

            # Validate option data structure if present
            for option_type in ["CE", "PE"]:
                if option_type in record and record[option_type] is not None:
                    option_data = record[option_type]
                    option_path = record_path + [option_type]

                    if not isinstance(option_data, dict):
                        raise InvalidTypeError(
                            option_type,
                            dict,
                            type(option_data),
                            _get_path_string(option_path),
                        )

                    # Validate key fields in option data
                    required_option_fields = ["strikePrice", "expiryDate"]
                    for field in required_option_fields:
                        if field not in option_data:
                            raise MissingKeyError(
                                field, _get_path_string(option_path)
                            )


def validate_nifty_option_chain(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate NSE option chain response data.

    This function performs comprehensive validation of the NSE option chain
    response, ensuring:
    - Required keys exist at all levels
    - Data types match expected types
    - Required data is not empty
    - Option chain records have valid structure

    Args:
        data: Raw JSON dictionary from NSE API.

    Returns:
        The validated data dictionary (unchanged if validation passes).

    Raises:
        MissingKeyError: When a required key is missing.
        InvalidTypeError: When a value has incorrect data type.
        EmptyDataError: When required data is empty or missing.
        ValidationError: For other validation errors.
    """
    if not isinstance(data, dict):
        raise InvalidTypeError("root", dict, type(data), "")

    if len(data) == 0:
        raise EmptyDataError("root", "")

    # Validate top-level required keys
    for key in _REQUIRED_TOP_LEVEL_KEYS:
        _validate_key_exists(data, key, [], required=True)

    # Validate top-level types
    for key, expected_type in _EXPECTED_TYPES.items():
        if key in data:
            _validate_type(
                data[key],
                key,
                expected_type,
                [],
                allow_none=False,
            )

    # Validate records structure
    if "records" in data:
        _validate_records_structure(data["records"], [])

    # Validate filtered structure if present (optional but should be valid if exists)
    if "filtered" in data and data["filtered"] is not None:
        if not isinstance(data["filtered"], dict):
            raise InvalidTypeError(
                "filtered",
                dict,
                type(data["filtered"]),
                "filtered",
            )

    return data
