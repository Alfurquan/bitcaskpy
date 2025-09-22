from app.logging.logger_factory import LoggerFactory

logger = LoggerFactory.get_logger("demo", service="log_demo")

logger.info("Some demo log message")
logger.error("An error occurred", error_code=500)
logger.debug("Debugging info")
logger.warning("This is a warning")