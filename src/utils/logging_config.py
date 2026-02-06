"""
Logging configuration for Hallucination Hunter
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from rich.console import Console
from rich.logging import RichHandler


# Global console for rich output
console = Console()


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{level_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    use_rich: bool = True
) -> logging.Logger:
    """
    Configure logging for the application
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        log_format: Custom log format string
        use_rich: Whether to use rich for console output
    
    Returns:
        Root logger instance
    """
    # Get numeric level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Default format
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if use_rich:
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            rich_tracebacks=True,
            tracebacks_show_locals=True
        )
        console_handler.setLevel(numeric_level)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter(log_format))
        console_handler.setLevel(numeric_level)
    
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel(numeric_level)
        root_logger.addHandler(file_handler)
    
    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("filelock").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class AuditLogger:
    """
    Specialized logger for audit trail
    Logs verification events for compliance and debugging
    """
    
    def __init__(self, log_file: Optional[str] = None):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Create audit log file
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            handler = logging.FileHandler(log_path, encoding='utf-8')
            handler.setFormatter(logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s'
            ))
            self.logger.addHandler(handler)
    
    def log_verification_start(self, document_id: str, claim_count: int) -> None:
        """Log start of verification process"""
        self.logger.info(
            f"VERIFICATION_START | doc_id={document_id} | claims={claim_count}"
        )
    
    def log_claim_result(
        self,
        document_id: str,
        claim_id: str,
        claim_text: str,
        category: str,
        confidence: float,
        evidence_ids: list
    ) -> None:
        """Log individual claim verification result"""
        self.logger.info(
            f"CLAIM_RESULT | doc_id={document_id} | claim_id={claim_id} | "
            f"category={category} | confidence={confidence:.3f} | "
            f"evidence_count={len(evidence_ids)}"
        )
    
    def log_verification_complete(
        self,
        document_id: str,
        trust_score: float,
        duration_seconds: float
    ) -> None:
        """Log completion of verification process"""
        self.logger.info(
            f"VERIFICATION_COMPLETE | doc_id={document_id} | "
            f"trust_score={trust_score:.1f} | duration={duration_seconds:.2f}s"
        )
    
    def log_user_feedback(
        self,
        document_id: str,
        claim_id: str,
        original_category: str,
        new_category: str,
        notes: Optional[str] = None
    ) -> None:
        """Log user feedback/override on a claim"""
        self.logger.info(
            f"USER_FEEDBACK | doc_id={document_id} | claim_id={claim_id} | "
            f"original={original_category} | new={new_category} | "
            f"notes={notes or 'N/A'}"
        )
    
    def log_export(
        self,
        document_id: str,
        export_format: str,
        filename: str
    ) -> None:
        """Log export event"""
        self.logger.info(
            f"EXPORT | doc_id={document_id} | format={export_format} | "
            f"filename={filename}"
        )
    
    def log_error(
        self,
        document_id: str,
        error_type: str,
        error_message: str
    ) -> None:
        """Log error during verification"""
        self.logger.error(
            f"ERROR | doc_id={document_id} | type={error_type} | "
            f"message={error_message}"
        )


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        from src.config.settings import get_settings
        settings = get_settings()
        audit_log_file = settings.logs_dir / "audit_history.log"
        _audit_logger = AuditLogger(str(audit_log_file))
    return _audit_logger


class ProgressTracker:
    """
    Tracks and reports progress for long-running operations
    """
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.now()
        self.logger = get_logger(__name__)
    
    def update(self, increment: int = 1, message: Optional[str] = None) -> None:
        """Update progress"""
        self.current = min(self.current + increment, self.total)
        percent = (self.current / self.total) * 100
        
        if message:
            self.logger.info(f"{self.description}: {percent:.1f}% - {message}")
    
    def finish(self) -> float:
        """Mark progress as complete and return duration"""
        duration = (datetime.now() - self.start_time).total_seconds()
        self.logger.info(
            f"{self.description}: Complete ({self.total} items in {duration:.2f}s)"
        )
        return duration
    
    @property
    def progress_percent(self) -> float:
        """Get current progress percentage"""
        return (self.current / self.total) * 100 if self.total > 0 else 0
    
    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds"""
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def estimated_remaining(self) -> float:
        """Estimate remaining time in seconds"""
        if self.current == 0:
            return 0
        rate = self.current / self.elapsed_seconds
        remaining = self.total - self.current
        return remaining / rate if rate > 0 else 0
