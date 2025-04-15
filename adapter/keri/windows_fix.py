"""
Windows compatibility patch for KERI library.
This module patches the logging configuration to work on Windows by disabling the SysLogHandler.
"""
import os
import sys
import logging
import platform

def apply_windows_fixes():
    """Apply fixes for running KERI on Windows"""
    if platform.system() == 'Windows':
        # Monkey patch SysLogHandler to do nothing on Windows
        from logging import handlers
        
        # Store original SysLogHandler constants
        original_handler = handlers.SysLogHandler
        
        class DummySysLogHandler(logging.Handler):
            """Dummy handler that does nothing, used to replace SysLogHandler on Windows"""
            # Copy all the constants from the original SysLogHandler
            LOG_EMERG, LOG_ALERT, LOG_CRIT, LOG_ERR, LOG_WARNING, \
            LOG_NOTICE, LOG_INFO, LOG_DEBUG = range(8)
            
            LOG_KERN, LOG_USER, LOG_MAIL, LOG_DAEMON, LOG_AUTH, \
            LOG_SYSLOG, LOG_LPR, LOG_NEWS, LOG_UUCP, LOG_CRON, \
            LOG_AUTHPRIV, LOG_FTP = range(12)
            
            LOG_LOCAL0, LOG_LOCAL1, LOG_LOCAL2, LOG_LOCAL3, \
            LOG_LOCAL4, LOG_LOCAL5, LOG_LOCAL6, LOG_LOCAL7 = range(16, 24)
            
            def __init__(self, *args, **kwargs):
                super().__init__()
            
            def emit(self, record):
                pass
            
            def createSocket(self, *args, **kwargs):
                pass
        
        # Replace the SysLogHandler with our dummy version
        handlers.SysLogHandler = DummySysLogHandler
        
        # Fix the invalid escape sequence warning
        import warnings
        warnings.filterwarnings("ignore", category=SyntaxWarning, 
                              message="invalid escape sequence")
        
        print("Applied Windows compatibility fixes for KERI")