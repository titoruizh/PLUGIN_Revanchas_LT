# -*- coding: utf-8 -*-
"""
Logging Configuration - Revanchas LT Plugin
Sistema de logging estructurado para reemplazar prints

Uso:
    from utils.logging_config import get_logger
    
    logger = get_logger(__name__)
    logger.info("Mensaje informativo")
    logger.error("Mensaje de error")
    logger.debug("Mensaje de debug")
"""

import logging
import sys
from typing import Optional

try:
    from ..config.settings import LoggingSettings
except ImportError:
    # Fallback si no se puede importar settings
    class LoggingSettings:
        DEFAULT_LEVEL = 'INFO'
        LOG_FORMAT = '[RevanchasLT] %(levelname)s - %(name)s: %(message)s'
        PREFIX_SUCCESS = '✓'
        PREFIX_ERROR = '✗'
        PREFIX_WARNING = '⚠'
        PREFIX_INFO = 'ℹ'
        PREFIX_DEBUG = '🔍'


# Registro de loggers creados
_loggers = {}
_configured = False


def configure_logging(level: str = 'INFO', 
                      log_format: Optional[str] = None) -> None:
    """
    Configura el sistema de logging global.
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        log_format: Formato personalizado de log (opcional)
    """
    global _configured
    
    if _configured:
        return
    
    # Configurar root logger para el plugin
    root_logger = logging.getLogger('RevanchasLT')
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Evitar handlers duplicados
    if not root_logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        format_str = log_format or LoggingSettings.LOG_FORMAT
        formatter = logging.Formatter(format_str)
        console_handler.setFormatter(formatter)
        
        root_logger.addHandler(console_handler)
    
    root_logger.propagate = False
    _configured = True


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Obtiene un logger configurado para el módulo especificado.
    
    Args:
        name: Nombre del módulo (usar __name__)
        level: Nivel de logging opcional (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Logger configurado
    """
    if name in _loggers:
        return _loggers[name]
    
    # Crear logger
    logger = logging.getLogger(f"RevanchasLT.{name}")
    
    # Configurar nivel
    log_level = getattr(logging, level or LoggingSettings.DEFAULT_LEVEL)
    logger.setLevel(log_level)
    
    # Evitar handlers duplicados
    if not logger.handlers:
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Formato
        formatter = logging.Formatter(LoggingSettings.LOG_FORMAT)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    # Evitar propagación a root logger
    logger.propagate = False
    
    _loggers[name] = logger
    return logger


def log_success(logger: logging.Logger, message: str) -> None:
    """Log mensaje de éxito con prefijo visual"""
    logger.info(f"{LoggingSettings.PREFIX_SUCCESS} {message}")


def log_error(logger: logging.Logger, message: str) -> None:
    """Log mensaje de error con prefijo visual"""
    logger.error(f"{LoggingSettings.PREFIX_ERROR} {message}")


def log_warning(logger: logging.Logger, message: str) -> None:
    """Log mensaje de advertencia con prefijo visual"""
    logger.warning(f"{LoggingSettings.PREFIX_WARNING} {message}")


def log_info(logger: logging.Logger, message: str) -> None:
    """Log mensaje informativo con prefijo visual"""
    logger.info(f"{LoggingSettings.PREFIX_INFO} {message}")


def log_debug(logger: logging.Logger, message: str) -> None:
    """Log mensaje de debug con prefijo visual"""
    logger.debug(f"{LoggingSettings.PREFIX_DEBUG} {message}")


class PluginLogger:
    """
    Clase helper para logging con métodos de conveniencia.
    
    Uso:
        from utils.logging_config import PluginLogger
        
        log = PluginLogger(__name__)
        log.success("Operación completada")
        log.error("Falló la operación")
    """
    
    def __init__(self, name: str, level: Optional[str] = None):
        self._logger = get_logger(name, level)
    
    def debug(self, message: str) -> None:
        log_debug(self._logger, message)
    
    def info(self, message: str) -> None:
        log_info(self._logger, message)
    
    def success(self, message: str) -> None:
        log_success(self._logger, message)
    
    def warning(self, message: str) -> None:
        log_warning(self._logger, message)
    
    def error(self, message: str) -> None:
        log_error(self._logger, message)
    
    def exception(self, message: str) -> None:
        """Log excepción con traceback"""
        self._logger.exception(f"{LoggingSettings.PREFIX_ERROR} {message}")
