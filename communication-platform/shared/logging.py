import logging
import os
import sys
import json
from typing import Optional

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        # Add trace_id if present in the log record's extra
        trace_id = getattr(record, 'trace_id', None)
        if trace_id is not None:
            log_record['trace_id'] = trace_id
        # Add exception info if present
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def init_logging(service_name: str, log_level: Optional[str] = None):
    """
    Initialize logging with JSON formatter and optional log level.
    :param service_name: Name of the service for logger naming.
    :param log_level: Log level as string (e.g., 'INFO', 'DEBUG'). Defaults to env LOG_LEVEL or INFO.
    """
    level = log_level or os.getenv('LOG_LEVEL', 'INFO').upper()
    logger = logging.getLogger()
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = JsonFormatter()
    handler.setFormatter(formatter)
    logger.handlers = [handler]
    logger.propagate = False
    # Add service name to all logs
    logging.LoggerAdapter(logger, {'service': service_name})

class TraceLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter to inject trace_id into log records.
    """
    def process(self, msg, kwargs):
        extra = kwargs.get('extra')
        if extra is None:
            extra = {}
        # Ensure self.extra is a dict
        adapter_extra = self.extra if isinstance(self.extra, dict) else {}
        if 'trace_id' not in extra and 'trace_id' in adapter_extra:
            extra['trace_id'] = adapter_extra['trace_id']
        kwargs['extra'] = extra
        return msg, kwargs 