from typing import Union, Any, Optional

class State:
    """
    Класс для хранения состояний пользователей.
    """

    var_name = None

    def __init__(self):
        ...

    def __str__(self) -> str:
        return str(self.var_name)

class StatesGroupMeta(type):

    class_name = None

    def __new__(cls, name, bases, attrs):
        for key, value in attrs.items():
            if isinstance(value, State):
                value.var_name = key
            if str(key) == '__qualname__':
                cls.class_name = value
        return super().__new__(cls, name, bases, attrs)

class StatesGroup(metaclass=StatesGroupMeta):
    """
    Класс для хранения состояний пользователей.
    """
    variables = {}
    user_registers = {}

    def __init_subclass__(cls):
        super().__init_subclass__()

        for key, value in cls.__dict__.items():
            if isinstance(value, State):
                value.class_name = cls.__name__
                cls.variables[key] = value
    
    @classmethod
    def set_state(cls, state: State, user_id: int, **kwargs) -> None:
        cls.user_registers.update({int(user_id): {"state": state, "kwargs": kwargs}})
    
    @classmethod
    def get_state(cls, user_id: int) -> Optional[str]:
        values = cls.user_registers.get(int(user_id), None)
        return None if values is None else f'{values["state"]}'
    
    @classmethod
    def get_data(cls, user_id: int) -> dict:
        values = cls.user_registers.get(int(user_id), None)
        return {} if values is None else values["kwargs"]

    @classmethod
    def set_data(cls, user_id: int, **kwargs) -> None:
        if user_id not in cls.user_registers:
            raise ValueError('The user_id has not set the state.')
        
        cls.user_registers[user_id]['kwargs'].update(kwargs)

    @classmethod
    def remove_state(cls, user_id: int) -> None:
        cls.user_registers.pop(int(user_id), None)

    @classmethod
    def clear_data(cls, user_id: int) -> None:
        cls.user_registers[user_id]['kwargs'].clear()

class StateException(Exception):
    pass

class FSMContext:
    def __init__(self, user_id: int):
        self.user_id = int(user_id)
    
    def set_state(self, state: State, **kwargs: Any) -> None:
        """
        Устанавливает стейт для пользователя.

        Args:
            state (State): Установка стейта.
            kwargs (Any): значения.
        Returns:
            None
        """
        StatesGroup.set_state(state, self.user_id, **StatesGroup.get_data(self.user_id), **kwargs)
    
    def set_data(self, **kwargs: Any) -> None:
        """
        Устанавливает значение пользователю.
        
        Args:
            kwargs (Any): значение которое будет храниться у пользователя.
        Returns:
            None
        """

        StatesGroup.set_data(self.user_id, **kwargs)
    
    def get_state(self) -> Optional[str]:
        """
        Получает текущий стейт пользователя.

        Returns:
            str | None: str - у пользователя установлен стейт.None - у пользователя нету стейта.
        """
        return StatesGroup.get_state(self.user_id)
    
    def get_data(self) -> dict:
        """
        Получения значения которое установлено у пользователя.

        Return:
            dict
        """

        return StatesGroup.get_data(self.user_id)
    
    def finish(self) -> None:
        """
        Завершения состояние пользователю
        
        Returns:
            None
        """
        StatesGroup.remove_state(self.user_id)
    
    def clear_data(self) -> None:
        """
        Очистка данных пользователя.
        """
        StatesGroup.clear_data(self.user_id)
    
    def __str__(self) -> str:
        return str(self.user_id)