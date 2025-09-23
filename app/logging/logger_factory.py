import structlog
from app.logging import logging_config

class LoggerFactory:

    @staticmethod
    def get_logger(name: str = None, **kwargs):
        """
        Returns a structlog logger bound with a module/class name and optional context.

        :param name: Usually __name__ from the caller module.
        :param kwargs: Extra context to bind (e.g., service="bitcask-server").
        """
        logger = structlog.get_logger(name)
        if kwargs:
            logger = logger.bind(**kwargs)
        return logger
