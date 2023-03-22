from helpers.log import setup_custom_logger


class BaseHandler:
    def __init__(self, service: str):
        self._service = service
        self._logger = setup_custom_logger(self._service)