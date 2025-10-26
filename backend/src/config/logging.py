"""
Central logging configuration for RIM.
Expose `configure_logging(settings)` which sets up a colorized console handler
and common library log-levels. Designed to be called early from `main.py`.
"""
from __future__ import annotations

import logging
import sys
from typing import Optional


def configure_logging(settings) -> None:
    """Configure root logging according to settings.

    - Uses ANSI color codes when `settings.LOG_COLORS` is True.
    - Optionally initializes colorama on Windows when `settings.COLORAMA_ENABLED` is True.
    - Resets root handlers to avoid duplicates during reload.
    """
    # If the settings enable Loguru, configure it and intercept stdlib logging
    if getattr(settings, "LOG_USE_LOGURU", False):
        try:
            from loguru import logger as loguru_logger

            # Configure loguru handler
            loguru_logger.remove()
            loguru_logger.add(
                sys.stdout,
                level=getattr(settings, "LOG_LEVEL", "INFO"),
                format=getattr(settings, "LOGURU_FORMAT", "{time} | {level} | {name}\t{message}"),
                colorize=True,
            )

            class _InterceptHandler(logging.Handler):
                """Redirect standard logging records to loguru."""

                def emit(self, record: logging.LogRecord) -> None:
                    # Get corresponding Loguru level if it exists
                    try:
                        level = loguru_logger.level(record.levelname).name
                    except Exception:
                        level = record.levelno

                    # Find caller frame depth
                    frame, depth = logging.currentframe(), 2
                    while frame and frame.f_code.co_filename == logging.__file__:
                        frame = frame.f_back
                        depth += 1

                    loguru_logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

            # Clear existing root handlers and intercept
            logging.root.handlers = [ _InterceptHandler() ]
            logging.root.setLevel(0)

            # Optionally, reduce noisy libraries but allow loguru to control levels
            logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
            logging.getLogger("asyncio").setLevel(logging.WARNING)

            return
        except Exception:
            # Fallback to stdlib logging if loguru setup fails
            pass

    # Optional: enable colorama on Windows (no-op on other OS)
    if getattr(settings, "COLORAMA_ENABLED", True):
        try:
            import colorama  # type: ignore

            colorama.init()
        except Exception:
            # colorama is optional; continue without it
            pass

    class _ColorFormatter(logging.Formatter):
        RESET = "\x1b[0m"
        LEVEL_COLORS = {
            "DEBUG": "\x1b[36m",
            "INFO": "\x1b[32m",
            "WARNING": "\x1b[33m",
            "ERROR": "\x1b[31m",
            "CRITICAL": "\x1b[41m",
        }
        MODULE_PALETTE = [
            "\x1b[95m",
            "\x1b[94m",
            "\x1b[96m",
            "\x1b[92m",
            "\x1b[93m",
            "\x1b[91m",
            "\x1b[90m",
        ]

        _module_color_cache: dict[str, str] = {}

        def _get_module_key(self, record_name: str) -> str:
            parts = record_name.split('.')
            if len(parts) > 1 and parts[0] == 'src':
                return parts[1]
            return parts[0]

        def _get_module_color(self, key: str) -> str:
            # Primero, respetar colores explícitos definidos en settings
            module_overrides = getattr(settings, "LOG_MODULE_COLORS", {}) or {}
            if key in module_overrides:
                return module_overrides[key]

            if key in self._module_color_cache:
                return self._module_color_cache[key]
            idx = abs(hash(key)) % len(self.MODULE_PALETTE)
            color = self.MODULE_PALETTE[idx]
            self._module_color_cache[key] = color
            return color

        def format(self, record: logging.LogRecord) -> str:
            if getattr(settings, "LOG_COLORS", True):
                level = record.levelname
                level_color = self.LEVEL_COLORS.get(level, "")
                module_key = self._get_module_key(record.name)
                module_color = self._get_module_color(module_key)

                orig_levelname = record.levelname
                orig_name = record.name
                try:
                    record.levelname = f"{level_color}{orig_levelname}{self.RESET}"
                    record.name = f"{module_color}{module_key}{self.RESET}"
                    return super().format(record)
                finally:
                    record.levelname = orig_levelname
                    record.name = orig_name
            # Fallback: no colors
            return super().format(record)

    # Build handler
    handler = logging.StreamHandler(sys.stdout)
    # Insertamos una tabulación entre el name y el message para separar visualmente
    fmt = "%(asctime)s %(levelname)s %(name)s:\t%(message)s"
    formatter = _ColorFormatter(fmt=fmt)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    # avoid duplicating handlers during autoreload
    root.handlers = []
    root.setLevel(getattr(settings, "LOG_LEVEL", "INFO"))
    root.addHandler(handler)

    # Reduce noisy library loggers
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


__all__ = ["configure_logging"]
