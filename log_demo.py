from app.logging.logger_factory import LoggerFactory

logger = LoggerFactory.get_logger("demo", service="log_demo")

logger.info("Demo event", message="This is a demo log message", user="tester")
logger.error("Demo error", error_code=500, error_message="Simulated error occurred")