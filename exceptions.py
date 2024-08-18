class UnexpectedStatusError(Exception):
    """Ошибка запроса к API-сервису - получен код, отличный от 200."""


class HomeworkStatusError(Exception):
    """Ошибка - некорректиный стаус проверки работы."""


class HomeworkNameError(Exception):
    """Ошибка - домашняя работа не найдена."""


class RequestedKeyError(Exception):
    """В словаре отсутствует запрашиваемый ключ."""


class RequestExceptionError(Exception):
    """Ошибка при подключении к API-сервису."""


class MessageSendingError(Exception):
    """Ошибка при отправке сообщения."""
