class ButtonParameterErorr(Exception):
    """Если не указали ни один параметр."""
    pass

class Telegram(Exception):
    """Прочие ошибки."""
    text: str = ...
    code: int = ...

class Forbidden(Telegram):
    """Недостаточно прав."""
    pass

class Unauthorized(Telegram):
    """Неверный токен бота."""
    pass

class BadRequest(Telegram):
    """Неверный запрос."""
    pass

class NotFound(Telegram):
    """Ресурс не найден."""
    pass

class InternalServerError(Telegram):
    """Ошибка на стороне сервера."""
    pass

class BadGateway(Telegram):
    """Плохой шлюз."""
    pass

class ServiceUnavailable(Telegram):
    """Сервис недоступен."""
    pass

class TooManyRequests(Telegram):
    """Слишком много запросов"""
    def __init__(self, *args: object, value: int) -> None:
        self.value = value
        super().__init__(*args)