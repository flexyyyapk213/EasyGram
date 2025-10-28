"""
Асинхронная версия
"""

import aiohttp
from typing import Union, Callable, List, Tuple, Any
import traceback

import asyncio

from .types import (
    ParseMode,
    Message,
    ReplyKeyboardMarkup,
    GetMe,
    InlineKeyboardMarkup,
    CallbackQuery,
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat,
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeChatMember,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChatAdministrators,
    User,
    PollOption,
    InputFile,
    ChatAction,
    Poll,
    Request,
    File,
    PollAnswer,
    InlineKeyboardButton
)

from ..exception import Telegram

import re

from concurrent.futures import ThreadPoolExecutor

import json

from ..state import StatesGroup, State, FSMContext

import logging

import inspect

from io import BytesIO

__all__ = [
    'ParseMode',
    'Message',
    'ReplyKeyboardMarkup',
    'GetMe',
    'InlineKeyboardMarkup',
    'CallbackQuery',
    'BotCommand',
    'BotCommandScopeDefault',
    'BotCommandScopeChat',
    'BotCommandScopeAllChatAdministrators',
    'BotCommandScopeChatMember',
    'BotCommandScopeAllGroupChats',
    'BotCommandScopeAllPrivateChats',
    'BotCommandScopeChatAdministrators',
    'User',
    'PollOption',
    'InputFile',
    'ChatAction',
    'Poll',
    'AsyncBot',
    'File'
]

class AsyncBot:
    """
    Класс для управления ботом асинхронно.
    """
    offset = 0
    _message_handlers = []
    _callback_query_handlers = []
    _next_step_handlers = []
    _poll_handlers = []
    _poll_answer_handlers = []
    _query_next_step_handlers = []
    __loop__ = asyncio.new_event_loop()
    __session__: aiohttp.ClientSession = aiohttp.ClientSession(connector=aiohttp.TCPConnector(keepalive_timeout=30, loop=__loop__), loop=__loop__)
    __request__: Request = Request(log_level=logging.DEBUG, loop=__loop__)
    __executor__: ThreadPoolExecutor = None

    def __init__(self, token: str, log_level: int=logging.DEBUG, thread_max_workers: int=15):
        """
        Инициализирует AsyncBot с заданным токеном.

        Args:
            token (str): Токен для аутентификации запросов к API Telegram.
            log_level (int): Уровень логирования.
        """
        from ..utils import handle_reply_markup

        self.handle_reply_markup = handle_reply_markup
        
        self.token = token

        self.__executor__ = ThreadPoolExecutor(thread_max_workers)

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        self.__request__.logger.setLevel(log_level)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)

        self.logger.addHandler(console_handler)
        
        try:
            self.me: User = self.__loop__.run_until_complete(self.get_me())
        except (TimeoutError, ConnectionError) as e:
            traceback.print_exc()
        except Exception as e:
            raise Telegram('The token is incorrectly set.')

        self.logger.debug(f'The bot is launched with user name @{self.me.username}')

    async def get_me(self) -> User:
        """
        Получает актуальную информацию о боте из Telegram.

        Returns:
            User: Объект, представляющий бота.
        """
        
        response = await self.__request__.get(f'https://api.telegram.org/bot{self.token}/getMe')
        return User((await response.json())['result'])

    async def set_my_commands(self, commands: List[BotCommand], scope: Union[BotCommandScopeChat, BotCommandScopeDefault, BotCommandScopeChatMember, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats, BotCommandScopeChatAdministrators, BotCommandScopeAllChatAdministrators]=None, language_code: str=None) -> bool:
        """
        Устанавливает команды для бота.

        Args:
            commands (List[BotCommand]): Список команд для установки.
            scope (Union[BotCommandScopeChat, BotCommandScopeDefault, etc.], optional): Область видимости команд.
            language_code (str, optional): Код языка для локализации команд.

        Returns:
            bool: Возвращает True, если команды успешно установлены.
        """
        parameters = {
            'commands': [{"command": cmd.command, "description": cmd.description} for cmd in commands]
        }

        if scope:
            parameters['scope'] = {"type": scope.type}
            if hasattr(scope, 'chat_id'):
                parameters['scope'].update({"chat_id": scope.chat_id})
            if hasattr(scope, 'user_id'):
                parameters['scope'].update({"user_id": scope.user_id})

        if language_code:
            parameters['language_code'] = language_code
        
        response = await self.__request__.get(f'https://api.telegram.org/bot{self.token}/setMyCommands', json=parameters)
        return (await response.json())['ok'] if response is not None else False

    async def send_message(self, chat_id: Union[int, str], text: Union[int, float, str], reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, parse_mode: str=None, reply_to_message_id: int=None, disable_web_page_preview: bool=False) -> Message:
        """
        Отправляет текстовое сообщение пользователю или в чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата.
            text (Union[int, float, str]): Текст сообщения.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None], optional): Клавиатура для сообщения.
            parse_mode (str, optional): Режим форматирования текста.
            reply_to_message_id (int, optional): Если указан, сообщение будет отправлено как ответ на указанное сообщение.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
        parameters = {
            'chat_id': chat_id,
            'text': text,
            "link_preview_options": {
                "is_disabled": disable_web_page_preview
            }
        }

        reply_markup = self.handle_reply_markup(reply_markup, async_mode=True)

        if reply_markup is not None:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id
        
        response = await self.__request__.post(f'https://api.telegram.org/bot{self.token}/sendMessage', json=parameters)
        return Message((await response.json())['result'], self) if response is not None else None

    async def send_photo(self, chat_id: Union[int, str], photo: Union[InputFile], caption: Union[int, float, str]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, parse_mode: str=None, photo_name: str=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет фотографию в чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата.
            photo (Union[InputFile]): Файл фотографии.
            caption (Union[int, float, str], optional): Подпись к фотографии.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None], optional): Клавиатура для сообщения.
            parse_mode (str, optional): Режим форматирования текста подписи.
            photo_name (str, optional): Имя файла фотографии.
            reply_to_message_id (int, optional): Если указан, сообщение будет отправлено как ответ на указанное сообщение.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
        parameters = {
            'chat_id': chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        if photo_name is not None:
            try:
                _type = re.search('.*?\.(\w+)', photo_name).group(1)
                name = photo_name
            except AttributeError:
                name = 'image.png'
                _type = 'png'
        else:
            if hasattr(photo.file, 'name'):
                name = photo.file.name
                _type = re.search(r'.*?\.(\w+)', photo.file.name).group(1)
            else:
                name = 'image.png'
                _type = 'png'

        if caption is not None:
            parameters['caption'] = caption

        reply_markup = self.handle_reply_markup(reply_markup, async_mode=True)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}, ensure_ascii=False)
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        data = aiohttp.FormData()

        for param in parameters:
            if param == 'reply_markup':
                data.add_field(param, json.dumps(parameters[param]))
                continue
            data.add_field(param, str(parameters[param]))

        data.add_field('photo', photo.file, filename=name, content_type=f'image/{_type}')

        response = await self.__request__.post(f'https://api.telegram.org/bot{self.token}/sendPhoto', data=data)
        return Message((await response.json())['result'], self) if response is not None else None

    def message(self, _filters: Callable[[Message], any]=None, content_types: Union[str, List[str]]=None, commands: Union[str, List[str]]=None, allowed_chat_type: Union[List[str], Tuple[str], str]=None, state: State=None) -> Callable:
        """
        Декоратор для обработки входящих сообщений.

        Args:
            _filters (Callable[[Message], any], optional): Функция фильтрации сообщений.
            content_types (Union[str, List[str]], optional): Типы контента, которые должен обрабатывать обработчик.
            commands (Union[str, List[str]], optional): Команды, на которые должен реагировать обработчик.
            allowed_chat_type (Union[List[str], Tuple[str], str], optional): Типы чатов, в которых активен обработчик.
            state (State, optional): Состояние в контексте машины состояний.

        Returns:
            Callable: Функция-обертка, которая регистрирует обработчик сообщений.
        """
        def wrapper(func):
            self._message_handlers.append({'func': func, 'filters': _filters, 'content_types': content_types, 'commands': commands, 'allowed_chat_type': allowed_chat_type, 'state': state})
        return wrapper

    def message_handler(self, _filters: Callable[[Message], any]=None, content_types: Union[str, List[str]]=None, commands: Union[str, List[str]]=None, allowed_chat_type: Union[List[str], Tuple[str], str]=None, state: State=None) -> Callable:
        """
        Декоратор для обработки входящих сообщений, предназначенный для миграции из aiogram2 в EasyGram.

        Args:
            _filters (Callable[[Message], any], optional): Функция фильтрации сообщений.
            content_types (Union[str, List[str]], optional): Типы контента, которые должен обрабатывать обработчик.
            commands (Union[str, List[str]], optional): Команды, на которые должен реагировать обработчик.
            allowed_chat_type (Union[List[str], Tuple[str], str], optional): Типы чатов, в которых активен обработчик.
            state (State, optional): Состояние в контексте машины состояний.

        Returns:
            Callable: Функция-обертка, которая регистрирует обработчик сообщений.
        """
        def wrapper(func):
            self._message_handlers.append({'func': func, 'filters': _filters, 'content_types': content_types, 'commands': commands, 'allowed_chat_type': allowed_chat_type, 'state': state})
        return wrapper

    def callback_query(self, _filters: Callable[[CallbackQuery], any]=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None, state: State=None) -> Callable:
        """
        Декоратор для обработки callback-запросов от InlineKeyboardMarkup.

        Args:
            _filters (Callable[[CallbackQuery], any], optional): Функция фильтрации запросов.
            allowed_chat_type (Union[str, List[str], Tuple[str]], optional): Типы чатов, в которых активен обработчик.
            state (State, optional): Состояние в контексте машины состояний.

        Returns:
            Callable: Функция-обертка, которая регистрирует обработчик запросов.
        """
        def wrapper(func):
            self._callback_query_handlers.append({'func': func, 'filters': _filters, 'allowed_chat_type': allowed_chat_type, 'state': state})
        return wrapper

    def callback_query_handler(self, _filters: Callable[[CallbackQuery], any]=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None, state: State=None) -> Callable:
        """
        Декоратор для обработки callback-запросов от InlineKeyboardMarkup, предназначенный для миграции из aiogram2 в EasyGram.

        Args:
            _filters (Callable[[CallbackQuery], any], optional): Функция фильтрации запросов.
            allowed_chat_type (Union[str, List[str], Tuple[str]], optional): Типы чатов, в которых активен обработчик.
            state (State, optional): Состояние в контексте машины состояний.

        Returns:
            Callable: Функция-обертка, которая регистрирует обработчик запросов.
        """
        def wrapper(func):
            self._callback_query_handlers.append({'func': func, 'filters': _filters, 'allowed_chat_type': allowed_chat_type, 'state': state})
        return wrapper
    
    def poll_handler(self, _filters: Callable[[Poll], any]=None) -> Callable:
        """
        Декоратор для обработки опросов, предназначенный для миграции из pyTelegramBotAPI в EasyGram.

        Args:
            _filters (Callable[[Poll], any], optional): Функция фильтрации опросов.
        """

        def wrapper(func):
            self._poll_handlers.append({'func': func, 'filters': _filters})
        return wrapper
    
    def poll(self, _filters: Callable[[Poll], any]=None) -> Callable:
        """
        Декоратор для обработки опросов, предназначенный для миграции из pyTelegramBotAPI в EasyGram.

        Args:
            _filters (Callable[[Poll], any], optional): Функция фильтрации опросов.
        """

        def wrapper(func):
            self._poll_handlers.append({'func': func, 'filters': _filters})
        return wrapper
    
    def poll_answer_handler(self, _filters: Callable[[PollAnswer], Any]=None, state: State=None) -> Callable:
        """
        Декоратор для обработки ответов на опросы.
        :param _filters: лямбда
        :param state: поле State
        :return: Callable
        """

        def wrapper(func):
            self._poll_answer_handlers.append({
                'func': func,
                'filters': _filters,
                'state': state
            })
        
        return wrapper

    def poll_answer(self, _filters: Callable[[PollAnswer], Any]=None, state: State=None) -> Callable:
        """
        Декоратор для обработки ответов на опросы.
        :param _filters: лямбда
        :param state: поле State
        :return: Callable
        """

        def wrapper(func):
            self._poll_answer_handlers.append({
                'func': func,
                'filters': _filters,
                'state': state
            })
        
        return wrapper

    async def answer_callback_query(self, chat_id: Union[int, str], text: Union[int, float, str]=None, show_alert: bool=False) -> bool:
        """
        Отправляет ответ на callback-запрос пользователя.

        Args:
            chat_id (Union[int, str]): Идентификатор чата.
            text (Union[int, float, str], optional): Текст ответа.
            show_alert (bool, optional): Если True, ответ будет показан в виде всплывающего уведомления.

        Returns:
            bool: Возвращает True, если ответ был успешно отправлен.
        """
        parameters = {
            'callback_query_id': chat_id,
            'text': str(text),
            'show_alert': show_alert
        }
        
        response = await self.__request__.post(f'https://api.telegram.org/bot{self.token}/answerCallbackQuery', json=parameters)
        return (await response.json())['ok'] if response is not None else False

    async def delete_message(self, chat_id: Union[int, str], message_ids: Union[list, int]) -> bool:
        """
        Удаляет сообщение из чата.
        - Сообщение можно удалить, только если оно было отправлено менее 48 часов назад.
        - Сообщение в приватном чате можно удалить, только если оно было отправлено более 24 часов назад.

        Args:
            chat_id (Union[int, str]): Идентификатор чата.
            message_ids (Union[list, int]): Идентификатор сообщений для удаления.

        Returns:
            bool: Возвращает True, если сообщение было успешно удалено.
        """
        parameters = {
            'chat_id': chat_id,
            'message_id': message_ids
        }

        response = await self.__request__.post(f'https://api.telegram.org/bot{self.token}/deleteMessage', json=parameters)
        return (await response.json())['ok'] if response is not None else False

    async def edit_message_text(self, chat_id: Union[int, str], message_id: int, text: Union[int, float, str], parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, disable_web_page_preview: bool=False) -> bool:
        """
        Редактирует текст существующего сообщения.
        - Обратите внимание, что деловые сообщения, которые не были отправлены ботом и не содержат встроенной клавиатуры, можно редактировать только в течение 48 часов с момента отправки.

        Args:
            chat_id (Union[int, str]): Идентификатор чата.
            message_id (int): Идентификатор редактируемого сообщения.
            text (Union[int, float, str]): Новый текст сообщения.
            parse_mode (Union[str, ParseMode], optional): Режим форматирования текста.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None], optional): Клавиатура для сообщения.

        Returns:
            bool: Возвращает True, если сообщение было успешно отредактировано.
        """

        parameters = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": str(text),
            "link_preview_options": {
                "is_disabled": disable_web_page_preview
            }
        }

        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
        
        reply_markup = self.handle_reply_markup(reply_markup, async_mode=True)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}, ensure_ascii=False)
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'inline_keyboard': reply_markup.rows}, ensure_ascii=False)

        response = await self.__request__.post(f'https://api.telegram.org/bot{self.token}/editMessageText', json=parameters)
        return (await response.json())['ok'] if response is not None else False

    async def send_poll(self, chat_id: Union[int, str], question: Union[int, float, str], options: Union[List[PollOption], List[str]], question_parse_mode: Union[str, ParseMode]=None, is_anonymous: bool=True, type: str='regular', allows_multiple_answers: bool=False, correct_option_id: int=0, explanation: str=None, explanation_parse_mode: Union[str, ParseMode]=None, open_period: int=None, is_closed: bool=False, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет опрос в указанный чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется опрос.
            question (Union[int, float, str]): Текст вопроса опроса.
            options (Union[List[PollOption], List[str]]): Список вариантов ответов.
            question_parse_mode (Union[str, ParseMode], optional): Режим форматирования текста вопроса.
            is_anonymous (bool, optional): Указывает, является ли опрос анонимным.
            type (str, optional): Тип опроса ('regular' или 'quiz').
            allows_multiple_answers (bool, optional): Разрешить ли выбор нескольких вариантов ответов.
            correct_option_id (int, optional): Индекс правильного ответа, если опрос является викториной.
            explanation (str, optional): Объяснение, которое следует после опроса.
            explanation_parse_mode (Union[str, ParseMode], optional): Режим форматирования текста объяснения.
            open_period (int, optional): Время в секундах, в течение которого опрос будет активен.
            is_closed (bool, optional): Закрыть ли опрос сразу после создания.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None], optional): Клавиатура, которая будет отображаться с сообщением.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен ответить опрос.

        Returns:
            Message: Объект сообщения, содержащий опрос.
        """
        parameters = {
            "chat_id": chat_id,
            "question": str(question),
            "type": type,
            "allows_multiple_answers": allows_multiple_answers,
            "is_closed": is_closed
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        if len(options) < 2:
            try:
                raise Telegram('В списке параметра options должно быть минимум 2 элемента.')
            except Telegram as e:
                traceback.print_exc(e)
        elif len(options) > 10:
            try:
                raise Telegram('В списке параметра options должно быть максимум 10 элементов.')
            except Telegram as e:
                traceback.print_exc(e)
        else:
            parameters['options'] = []
            for option in options:
                if isinstance(option, PollOption):
                    _opt = {"text": option.text}
                    if option.text_parse_mode is not None: _opt.update({"text_parse_mode": option.text_parse_mode})
                    parameters['options'].append(_opt)
                else:
                    parameters['options'].append({"text": option})

        if type == 'quiz':
            parameters['correct_option_id'] = correct_option_id

        if explanation is not None:
            parameters['explanation'] = explanation
            if explanation_parse_mode is not None: parameters['explanation_parse_mode'] = explanation_parse_mode

        reply_markup = self.handle_reply_markup(reply_markup)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}, ensure_ascii=False)
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'inline_keyboard': reply_markup.rows}, ensure_ascii=False)

        if open_period is not None:
            parameters['open_period'] = open_period
        
        response = await self.__request__.post(f'https://api.telegram.org/bot{self.token}/sendPoll', json=parameters)
        return Message((await response.json())['result'], self) if response is not None else None

    async def send_audio(self, chat_id: Union[int, str], audio: Union[InputFile], title: str=None, caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет аудиофайл в указанный чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется аудио.
            audio (Union[InputFile]): Аудиофайл для отправки.
            title (str, optional): Название аудиофайла.
            caption (str, optional): Подпись к аудиофайлу.
            parse_mode (Union[str, ParseMode], optional): Режим форматирования текста подписи.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None], optional): Клавиатура для сообщения.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен быть дан ответ.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        if title is None: parameters['title'] = 'audio'
        else: parameters['title'] = title

        parameters['audio'] = audio

        if caption is not None:
            parameters['caption'] = caption

        reply_markup = self.handle_reply_markup(reply_markup, async_mode=True)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}, ensure_ascii=False)
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'inline_keyboard': reply_markup.rows}, ensure_ascii=False)
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        data = aiohttp.FormData()

        for param in parameters:
            if param == 'reply_markup':
                data.add_field(param, json.loads(parameters[param]))
                continue
            data.add_field(param, str(parameters[param]))

        response = await self.__request__.post(f'https://api.telegram.org/bot{self.token}/sendAudio', data=data)
        return Message((await response.json())['result'], self) if response is not None else None

    async def send_document(self, chat_id: Union[int, str], document: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет документ в указанный чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется документ.
            document (Union[InputFile]): Файл документа для отправки.
            caption (str, optional): Подпись к документу.
            parse_mode (Union[str, ParseMode], optional): Режим форматирования текста подписи.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None], optional): Клавиатура, прикрепляемая к сообщению.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен быть дан ответ.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        parameters['document'] = document.file

        if caption is not None:
            parameters['caption'] = caption

        reply_markup = self.handle_reply_markup(reply_markup, async_mode=True)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        data = aiohttp.FormData()

        for param in parameters:
            if param == 'reply_markup':
                data.add_field(param, json.dumps(parameters[param], ensure_ascii=False))
                continue
            elif param == 'document':
                data.add_field(
                    'document',
                    parameters[param],
                    filename=getattr(document.file, 'name', 'document.bin')
                )
                continue
            data.add_field(param, str(parameters[param]))
        
        response = await self.__request__.post(f'https://api.telegram.org/bot{self.token}/sendDocument', data=data)
        return Message((await response.json())['result'], self) if response is not None else None

    async def send_animation(self, chat_id: Union[int, str], animation: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет анимацию (видео или GIF) в указанный чат.
        
        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется анимация.
            animation (Union[InputFile]): Файл анимации для отправки.
            caption (str, optional): Подпись к анимации.
            parse_mode (Union[str, ParseMode], optional): Режим форматирования текста подписи.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None], optional): Клавиатура, прикрепляемая к сообщению.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен быть дан ответ.
        
        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        parameters['animation'] = animation

        if caption is not None:
            parameters['caption'] = caption

        reply_markup = self.handle_reply_markup(reply_markup, async_mode=True)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}, ensure_ascii=False)
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'inline_keyboard': reply_markup.rows}, ensure_ascii=False)
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        data = aiohttp.FormData()

        for param in parameters:
            if param == 'reply_markup':
                data.add_field(param, json.loads(parameters[param]))
                continue
            data.add_field(param, str(parameters[param]))
        
        response = await self.__request__.post(f'https://api.telegram.org/bot{self.token}/sendAnimation', data=data)
        return Message((await response.json())['result'], self) if response is not None else None

    async def send_voice(self, chat_id: Union[int, str], voice: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет голосовое сообщение в указанный чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется сообщение.
            voice (Union[InputFile]): Файл голосового сообщения для отправки.
            caption (str, optional): Подпись к голосовому сообщению.
            parse_mode (Union[str, ParseMode], optional): Режим форматирования текста подписи.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None], optional): Клавиатура, прикрепляемая к сообщению.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен быть дан ответ.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        parameters['voice'] = voice

        if caption is not None:
            parameters['caption'] = caption

        reply_markup = self.handle_reply_markup(reply_markup, async_mode=True)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}, ensure_ascii=False)
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'inline_keyboard': reply_markup.rows}, ensure_ascii=False)
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        data = aiohttp.FormData()

        for param in parameters:
            if param == 'reply_markup':
                data.add_field(param, json.loads(parameters[param]))
                continue
            data.add_field(param, str(parameters[param]))
        
        response = await self.__request__.post(f'https://api.telegram.org/bot{self.token}/sendVoice', data=data)
        return Message((await response.json())['result'], self) if response is not None else None

    async def send_video_note(self, chat_id: Union[int, str], video_note: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет видеозаметку в указанный чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется видеозаметка.
            video_note (Union[InputFile]): Файл видеозаметки для отправки.
            caption (str, optional): Подпись к видеозаметке.
            parse_mode (Union[str, ParseMode], optional): Режим форматирования текста подписи.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None], optional): Клавиатура, прикрепляемая к сообщению.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен быть дан ответ.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        parameters['video_note'] = video_note

        if caption is not None:
            parameters['caption'] = caption

        reply_markup = self.handle_reply_markup(reply_markup, async_mode=True)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}, ensure_ascii=False)
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'inline_keyboard': reply_markup.rows}, ensure_ascii=False)
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        data = aiohttp.FormData()

        for param in parameters:
            if param == 'reply_markup':
                data.add_field(param, json.loads(parameters[param]))
                continue
            data.add_field(param, str(parameters[param]))
        
        response = await self.__request__.post(f'https://api.telegram.org/bot{self.token}/sendVideoNote', data=data)
        return Message((await response.json())['result'], self) if response is not None else None

    async def send_video(self, chat_id: Union[int, str], video: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет видео в указанный чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется видео.
            video (Union[InputFile]): Файл видео для отправки.
            caption (str, optional): Подпись к видео.
            parse_mode (Union[str, ParseMode], optional): Режим форматирования текста подписи.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None], optional): Клавиатура, прикрепляемая к сообщению.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен быть дан ответ.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        parameters['video'] = video

        if caption is not None:
            parameters['caption'] = caption

        reply_markup = self.handle_reply_markup(reply_markup, async_mode=True)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}, ensure_ascii=False)
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'inline_keyboard': reply_markup.rows}, ensure_ascii=False)
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        data = aiohttp.FormData()

        for param in parameters:
            if param == 'reply_markup':
                data.add_field(param, json.loads(parameters[param]))
                continue
            data.add_field(param, str(parameters[param]))

        response = await self.__request__.post(f'https://api.telegram.org/bot{self.token}/sendVideo', data=data)
        return Message((await response.json())['result'], self) if response is not None else None

    async def send_contact(self, chat_id: Union[int, str], number: Union[InputFile], first_name: str, last_name: str=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет контакт в указанный чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется контакт.
            number (Union[InputFile]): Номер телефона контакта.
            first_name (str): Имя контакта.
            last_name (str, optional): Фамилия контакта.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None], optional): Клавиатура, прикрепляемая к сообщению.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен быть дан ответ.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
        parameters = {
            "chat_id": chat_id,
            "first_name": first_name
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        parameters['number'] = number

        if last_name is not None: parameters['last_name'] = last_name

        reply_markup = self.handle_reply_markup(reply_markup, async_mode=True)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}, ensure_ascii=False)
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'inline_keyboard': reply_markup.rows}, ensure_ascii=False)

        response = await self.__request__.post(f'https://api.telegram.org/bot{self.token}/sendContact', json=parameters)
        return Message((await response.json())['result'], self) if response is not None else None

    async def send_dice(self, chat_id: Union[int, str], emoji: str, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет анимированный эмодзи в чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата.
            emoji (str): Эмодзи для отправки (допустимые значения: 🎲, 🎯, 🏀, ⚽, 🎳, 🎰).
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None], optional): Клавиатура для сообщения.
            reply_to_message_id (int, optional): ID сообщения, на которое должен быть дан ответ.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        if emoji not in ['🎲', '🎯', '🏀', '⚽', '🎳', '🎰']:
            raise TypeError(f'Эмодзи {emoji} не поддерживается.')

        reply_markup = self.handle_reply_markup(reply_markup, async_mode=True)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}, ensure_ascii=False)
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = json.dumps({'inline_keyboard': reply_markup.rows}, ensure_ascii=False)

        response = await self.__request__.post(f'https://api.telegram.org/bot{self.token}/sendDice', json=parameters)
        return Message((await response.json())['result'], self) if response is not None else None

    async def send_chat_action(self, chat_id: Union[int, str], action: Union[str, ChatAction]) -> bool:
        """
        Отправляет статус действия в чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата.
            action (Union[str, ChatAction]): Тип действия (см. EasyGram.types.ChatAction/EasyGram.Async.types.ChatAction).

        Returns:
            bool: True, если действие отправлено успешно, иначе False.
        """
        parameters = {
            "chat_id": chat_id,
            "action": action
        }

        response = await self.__request__.post(f'https://api.telegram.org/bot{self.token}/sendChatAction', json=parameters)
        return (await response.json())['ok'] if response is not None else False
    
    async def next_step_handler(self, chat_id: int, callback: Callable, *args):
        """
        Устанавливает обработчик следующего шага для сообщений от пользователя.

        Args:
            chat_id (int): Идентификатор чата.
            callback (Callable): Функция обратного вызова, которая будет вызвана при получении сообщения.
            args: Аргументы, передаваемые в функцию обратного вызова.

        Returns:
            None
        """
        self._next_step_handlers.append((str(chat_id), callback, args))
    
    async def query_next_step_handler(self, chat_id: int, callback: Callable, *args):
        """
        Устанавливает обработчик следующего шага для inline-запросов от пользователя.

        Args:
            chat_id (int): Идентификатор чата.
            callback (Callable): Функция обратного вызова, которая будет вызвана при нажатии на inline-кнопку.
            args: Аргументы, передаваемые в функцию обратного вызова.

        Returns:
            None
        """
        self._query_next_step_handlers.append((str(chat_id), callback, args))
    
    async def get_file(self, file_id: str) -> File:
        response = await self.__request__.get(f'https://api.telegram.org/bot{self.token}/getFile', json={'file_id': file_id})
        tojson = await response.json()

        return File(tojson['result']['file_id'], tojson['result']['file_unique_id'], tojson['result']['file_size'], tojson['result']['file_path'])
    
    async def download_file(self, file_path: str) -> BytesIO:
        response =  await self.__request__.get(f'https://api.telegram.org/file/bot{self.token}/'+file_path)
        return BytesIO(response)
    
    async def edit_message_reply_markup(self, chat_id: Union[int, str]=None, message_id: Union[int, str]=None, inline_message_id: Union[int, str]=None, reply_markup: Union[InlineKeyboardMarkup, InlineKeyboardButton, list[list[InlineKeyboardButton]]]=None) -> bool:
        """
        Меняет inline кнопки.

        Args:
            chat_id (int | str): Айди чата.
            message_id (int | str): Айди сообщения.
            inline_message_id (int | str): Требуется, если chat_id и message_id не указаны. Идентификатор встроенного сообщения
            reply_markup (types.InlineKeyboardMarkup | types.InlineKeyboardButton): Кнопки.
        Return:
            bool
        """

        parameters = {}

        if chat_id is not None:
            parameters['chat_id'] = chat_id
        
        if message_id is not None:
            parameters['message_id'] = message_id
        
        if inline_message_id:
            parameters['inline_message_id'] = inline_message_id

        if reply_markup is not None:
            if isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
            elif isinstance(reply_markup, InlineKeyboardButton):
                parameters['reply_markup'] = {'inline_keyboard': [[reply_markup.keyboard]]}
            elif isinstance(reply_markup, list):
                parameters['reply_markup'] = {'inline_keyboard': InlineKeyboardMarkup(builder=reply_markup)}
        
        response = await self.__request__.get(f'https://api.telegram.org/bot{self.token}/editMessageReplyMarkup', json=parameters)
        return response.ok

    async def polling(self, on_startup: Callable=None, threaded_run: bool=False, *args) -> None:
        """
        Запускает процесс опроса сервера Telegram для получения обновлений.

        Args:
            on_startup (Callable, optional): Функция, вызываемая при запуске опроса.
            threaded_run (bool, optional): Если True, опрос выполняется в отдельных потоках.
            thread_max_works (int, optional): Максимальное количество потоков.
            args: Дополнительные аргументы, передаваемые в функцию on_startup.

        Returns:
            None
        """

        if on_startup is not None:  asyncio.run(on_startup(args))

        while True:
            try:
                async with await self.__request__.get(f'https://api.telegram.org/bot{self.token}/getUpdates', params={"offset": self.offset, "timeout": 30, "allowed_updates": ["message", "callback_query", "poll"]}) as response:
                    if response.status != 200:
                        continue
                    
                    updates = response

                    updates = (await updates.json())["result"]

                for update in updates:
                    self.offset = update["update_id"] + 1

                    if update.get('message', False):
                        for indx, step in enumerate(self._next_step_handlers):
                            if str(update['message']['chat']['id']) == step[0]:
                                if threaded_run:
                                    self.__executor__.submit(self.__run_with_try_except__, step[1], Message(update['message'], self), *step[2])
                                else:
                                    self.__run_with_try_except__(step[1], Message(update['message'], self), *step[2])
                                
                                self._next_step_handlers.pop(indx)
                                break
                        
                        for handler_message in self._message_handlers:
                            if handler_message['filters'] is not None and not handler_message['filters'](Message(update['message'], self)):
                                continue

                            if handler_message['commands'] is not None:
                                if not update['message'].get('text', False):
                                    continue

                                if isinstance(handler_message['commands'], list):
                                    if not any(update['message']['text'].split()[0] == '/'+command for command in handler_message['commands']):
                                        continue
                                elif isinstance(handler_message['commands'], str):
                                    if not update['message']['text'].startswith('/'+handler_message['commands']):
                                        continue

                            if handler_message['content_types'] is not None:
                                if isinstance(handler_message['content_types'], str) and handler_message['content_types'].lower() != 'any':
                                    if not update['message'].get(handler_message['content_types'], False):
                                        continue
                                elif isinstance(handler_message['content_types'], list):
                                    if not any(update['message'].get(__type, False) and __type.lower() == 'any' for __type in handler_message['content_types']):
                                        continue
                            
                            if handler_message['allowed_chat_type'] is not None:
                                if isinstance(handler_message['allowed_chat_type'], str):
                                    if update['message']['chat']['type'] != handler_message['allowed_chat_type']:
                                        continue
                                elif isinstance(handler_message['allowed_chat_type'], (tuple, list)):
                                    if not any(update['message']['chat']['type'] == _chat_type for _chat_type in handler_message['allowed_chat_type']):
                                        continue

                            if handler_message['state'] is not None:
                                if update['message']['from']['id'] not in StatesGroup.user_registers:
                                    continue

                                if handler_message['state'] != StatesGroup.user_registers[update['message']['from']['id']]['state']:
                                    continue

                            message = Message(update['message'], self)
                            parameters = [message]
                            parameters.append(FSMContext(message.from_user.id))
                            
                            is_method = inspect.ismethod(handler_message['func'])
                            _parameters = list(inspect.signature(handler_message['func']).parameters)

                            if is_method and len(_parameters) > 0: _parameters.pop(0)

                            if len(_parameters) == 1: parameters.pop(1)

                            if threaded_run:
                                self.__executor__.submit(self.__run_with_try_except, handler_message['func'], *parameters)
                            else:
                                self.__run_with_try_except__(handler_message['func'], *parameters)
                                
                            break
                    elif update.get('callback_query', False):
                        for indx, step in enumerate(self._query_next_step_handlers):
                            if str(update['callback_query']['message']['chat']['id']) == step[0]:
                                if threaded_run:
                                    self.__executor__.submit(self.__run_with_try_except__, step[1], CallbackQuery(update['callback_query'], self), *step[2])
                                else:
                                    self.__run_with_try_except__(step[1], CallbackQuery(update['callback_query'], self), *step[2])
                                
                                self._query_next_step_handlers.pop(indx)
                                break

                        for callback in self._callback_query_handlers:
                            if callback['filters'] is not None and not callback['filters'](CallbackQuery(update['callback_query'], self)):
                                continue

                            if callback['allowed_chat_type'] is not None:
                                if isinstance(callback['allowed_chat_type'], str):
                                    if update['callback_query']['message']['chat']['type'] != callback['allowed_chat_type']:
                                        continue
                                elif isinstance(callback['allowed_chat_type'], (tuple, list)):
                                    if not any(update['callback_query']['message']['chat']['type'] == _chat_type for _chat_type in callback['allowed_chat_type']):
                                        continue

                            if callback['state'] is not None:
                                if update['callback_query']['message']['from']['id'] not in StatesGroup.user_registers:
                                    continue

                                if callback['state'] != StatesGroup.user_registers[update['callback_query']['message']['from']['id']]['state']:
                                    continue
                            
                            callback_query = CallbackQuery(update['callback_query'], self)
                            parameters = [callback_query]
                            parameters.append(FSMContext(callback_query.from_user.id))

                            is_method = inspect.ismethod(callback['func'])
                            _parameters = list(inspect.signature(callback['func']).parameters)

                            if is_method and len(_parameters) > 0: _parameters.pop(0)

                            if len(_parameters) == 1: parameters.pop(1)

                            if threaded_run:
                                self.__executor__.submit(self.__run_with_try_except__, callback['func'], *parameters)
                            else:
                                self.__run_with_try_except__(callback['func'], *parameters)
                            
                            break
                    elif update.get('poll', False):
                        for poll in self._poll_handlers:
                            if poll['filters'] is not None and not poll['filters'](Poll(update['poll'])):
                                continue
                            
                            _poll = Poll(update['poll'])

                            if threaded_run:
                                self.__executor__.submit(poll['func'], _poll)
                            else:
                                self.__run_with_try_except__(poll['func'], _poll)
                            
                            break
                    elif update.get('poll_answer', False):
                        for poll_answer in self._poll_handlers:
                            if poll_answer['filters'] is not None and not poll_answer['filters'](PollAnswer(update['poll_answer'])):
                                continue

                            if poll_answer['state'] is not None:
                                if update['poll_answer']['user']['id'] not in StatesGroup.user_registers:
                                    continue

                                if poll_answer['state'] != StatesGroup.user_registers[update['poll_answer']['user']['id']]['state']:
                                    continue
                            
                            _poll = PollAnswer(update['poll_answer'])

                            if threaded_run:
                                self.__executor__.submit(self.__run_with_try_except__, poll_answer['func'], _poll)
                            else:
                                self.__run_with_try_except__(poll_answer['func'], _poll)
                            
                            break
            except Exception as e:
                self.logger.error(traceback.format_exc())

    def executor(self, on_startup: Callable=None, threaded_run: bool=False, *args) -> None:
        """
        Запускает бота с возможностью использования многопоточности.

        Args:
            on_startup (Callable, optional): Функция, вызываемая при запуске.
            threaded_run (bool, optional): Если True, используется многопоточность.
            thread_max_works (int, optional): Максимальное количество потоков.
            args: Дополнительные аргументы.

        Returns:
            None
        """
        
        if on_startup is not None: self.__loop__.run_until_complete(on_startup(self))

        self.__loop__.run_until_complete(self.polling(threaded_run=threaded_run, *args))
    
    def __run_with_try_except__(self, func: Callable, *args):
        asyncio.run_coroutine_threadsafe(self.__work_lunch__(func, *args), self.__loop__)
    
    async def __work_lunch__(self, func: Callable, *args):
        try:
            await func(*args)
        except:
            self.logger.error(traceback.format_exc())