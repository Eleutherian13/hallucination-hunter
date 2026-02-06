"""
Input validation utilities for Hallucination Hunter
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

from src.config.constants import (
    SUPPORTED_FILE_TYPES,
    MAX_FILE_SIZE_MB,
    MAX_FILES_PER_UPLOAD,
    Domain,
)


@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    @classmethod
    def success(cls, warnings: Optional[List[str]] = None) -> "ValidationResult":
        return cls(is_valid=True, errors=[], warnings=warnings or [])
    
    @classmethod
    def failure(cls, errors: List[str], warnings: Optional[List[str]] = None) -> "ValidationResult":
        return cls(is_valid=False, errors=errors, warnings=warnings or [])
    
    def __bool__(self) -> bool:
        return self.is_valid


class InputValidator:
    """Validates user inputs and uploaded files"""
    
    @classmethod
    def validate_file(
        cls,
        file_path: Optional[Union[str, Path]] = None,
        file_content: Optional[bytes] = None,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> ValidationResult:
        """
        Validate an uploaded file
        
        Args:
            file_path: Path to file
            file_content: File content as bytes
            file_name: Original filename
            file_size: File size in bytes
        """
        errors = []
        warnings = []
        
        # Determine file info
        if file_path:
            path = Path(file_path)
            file_name = path.name
            file_size = path.stat().st_size if path.exists() else 0
            extension = path.suffix.lower()
        elif file_name:
            extension = Path(file_name).suffix.lower()
            file_size = len(file_content) if file_content else file_size or 0
        else:
            return ValidationResult.failure(["No file provided"])
        
        # Check extension
        if extension not in SUPPORTED_FILE_TYPES:
            supported = ", ".join(SUPPORTED_FILE_TYPES.keys())
            errors.append(f"Unsupported file type: {extension}. Supported: {supported}")
        
        # Check file size
        max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            errors.append(f"File too large: {file_size / (1024*1024):.1f}MB. Maximum: {MAX_FILE_SIZE_MB}MB")
        elif file_size > max_size_bytes * 0.8:
            warnings.append(f"Large file ({file_size / (1024*1024):.1f}MB). Processing may be slow.")
        
        # Check for empty file
        if file_size == 0:
            errors.append("File is empty")
        
        if errors:
            return ValidationResult.failure(errors, warnings)
        return ValidationResult.success(warnings)
    
    @classmethod
    def validate_file_batch(
        cls,
        files: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        Validate a batch of files
        
        Args:
            files: List of file info dicts with 'name', 'size', 'content' keys
        """
        errors = []
        warnings = []
        
        # Check count
        if len(files) > MAX_FILES_PER_UPLOAD:
            errors.append(f"Too many files: {len(files)}. Maximum: {MAX_FILES_PER_UPLOAD}")
        
        if len(files) == 0:
            errors.append("No files provided")
        
        # Validate each file
        for i, file_info in enumerate(files):
            result = cls.validate_file(
                file_name=file_info.get("name"),
                file_content=file_info.get("content"),
                file_size=file_info.get("size")
            )
            if not result.is_valid:
                for error in result.errors:
                    errors.append(f"File {i+1} ({file_info.get('name', 'unknown')}): {error}")
            warnings.extend(result.warnings)
        
        if errors:
            return ValidationResult.failure(errors, warnings)
        return ValidationResult.success(warnings)
    
    @classmethod
    def validate_text_input(
        cls,
        text: str,
        min_length: int = 10,
        max_length: int = 100000,
        field_name: str = "Text"
    ) -> ValidationResult:
        """
        Validate text input
        
        Args:
            text: Input text
            min_length: Minimum character length
            max_length: Maximum character length
            field_name: Name of field for error messages
        """
        errors = []
        warnings = []
        
        if not text or not text.strip():
            return ValidationResult.failure([f"{field_name} is required"])
        
        text = text.strip()
        
        if len(text) < min_length:
            errors.append(f"{field_name} too short: {len(text)} characters. Minimum: {min_length}")
        
        if len(text) > max_length:
            errors.append(f"{field_name} too long: {len(text)} characters. Maximum: {max_length}")
        elif len(text) > max_length * 0.9:
            warnings.append(f"{field_name} is near maximum length limit")
        
        if errors:
            return ValidationResult.failure(errors, warnings)
        return ValidationResult.success(warnings)
    
    @classmethod
    def validate_domain(cls, domain: str) -> ValidationResult:
        """Validate domain selection"""
        valid_domains = [d.value for d in Domain]
        
        if domain.lower() not in valid_domains:
            return ValidationResult.failure(
                [f"Invalid domain: {domain}. Valid options: {', '.join(valid_domains)}"]
            )
        return ValidationResult.success()
    
    @classmethod
    def validate_threshold(
        cls,
        value: float,
        min_val: float = 0.0,
        max_val: float = 1.0,
        field_name: str = "Threshold"
    ) -> ValidationResult:
        """Validate a threshold value"""
        errors = []
        
        if not isinstance(value, (int, float)):
            return ValidationResult.failure([f"{field_name} must be a number"])
        
        if value < min_val or value > max_val:
            errors.append(f"{field_name} must be between {min_val} and {max_val}")
        
        if errors:
            return ValidationResult.failure(errors)
        return ValidationResult.success()
    
    @classmethod
    def validate_audit_request(
        cls,
        sources: List[Any],
        llm_output: str,
        domain: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate a complete audit request
        
        Args:
            sources: List of source documents/files
            llm_output: LLM-generated text to verify
            domain: Optional domain for domain-specific verification
        """
        errors = []
        warnings = []
        
        # Validate sources
        if not sources:
            errors.append("At least one source document is required")
        
        # Validate LLM output
        llm_result = cls.validate_text_input(
            llm_output,
            min_length=50,
            max_length=50000,
            field_name="LLM output"
        )
        if not llm_result.is_valid:
            errors.extend(llm_result.errors)
        warnings.extend(llm_result.warnings)
        
        # Validate domain if provided
        if domain:
            domain_result = cls.validate_domain(domain)
            if not domain_result.is_valid:
                errors.extend(domain_result.errors)
        
        if errors:
            return ValidationResult.failure(errors, warnings)
        return ValidationResult.success(warnings)
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize a filename to be safe for filesystem
        
        Args:
            filename: Original filename
        
        Returns:
            Sanitized filename
        """
        # Remove path separators
        filename = filename.replace("/", "_").replace("\\", "_")
        
        # Remove or replace unsafe characters
        filename = re.sub(r'[<>:"|?*]', '_', filename)
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        
        # Limit length
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            max_name_len = 200 - len(ext) - 1
            filename = f"{name[:max_name_len]}.{ext}" if ext else name[:200]
        
        return filename or "unnamed_file"
    
    @classmethod
    def validate_json_structure(
        cls,
        data: Any,
        required_fields: List[str],
        optional_fields: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Validate JSON data structure
        
        Args:
            data: JSON data (dict)
            required_fields: List of required field names
            optional_fields: List of optional field names
        """
        errors = []
        warnings = []
        
        if not isinstance(data, dict):
            return ValidationResult.failure(["Data must be a JSON object"])
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
            elif data[field] is None or data[field] == "":
                errors.append(f"Field cannot be empty: {field}")
        
        # Check for unknown fields
        known_fields = set(required_fields + (optional_fields or []))
        for field in data.keys():
            if field not in known_fields:
                warnings.append(f"Unknown field will be ignored: {field}")
        
        if errors:
            return ValidationResult.failure(errors, warnings)
        return ValidationResult.success(warnings)


def validate_and_raise(result: ValidationResult) -> None:
    """
    Validate and raise exception if invalid
    
    Args:
        result: Validation result
    
    Raises:
        ValueError: If validation failed
    """
    if not result.is_valid:
        raise ValueError("; ".join(result.errors))
