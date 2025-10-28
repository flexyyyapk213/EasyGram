"""
Синхронная версия
"""

__name__ = 'EasyGram'
__version__ = '0.0.5b1'

from typing import Union, Callable, List, Tuple, Any
import traceback

from .types import (
    Message,
    User,
    ReplyKeyboardMarkup,
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
    ParseMode,
    PollOption,
    InputFile,
    ChatAction,
    Poll,
    Request,
    File,
    PollAnswer,
    InlineKeyboardButton
)

from .exception import Telegram

from concurrent.futures import ThreadPoolExecutor

import traceback

from .state import StatesGroup, FSMContext, State

import logging

import inspect

from io import BytesIO

from .utils import handle_reply_markup

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
    'SyncBot',
    'File'
]

class SyncBot:
    offset = 0
    _message_handlers = []
    _callback_query_handlers = []
    _next_step_handlers = []
    _query_next_step_handlers = []
    _poll_handlers = []
    _poll_answer_handlers = []
    _request = Request(timeout=35)

    def __init__(self, token: str, log_level: int=logging.DEBUG):
        """
        Args:
            token (str): Токен для аутентификации запросов к API Telegram.
            log_level (int): Уровень логирования.
        """
        self.token = token

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        self._request.logger.setLevel(log_level)
        
        try:
            self.me = self.get_me()
        except (TimeoutError, ConnectionError) as e:
            traceback.print_exc()
        except Exception as e:
            raise Telegram('The token is incorrectly set.')

        self.logger.debug(f'The bot is launched with user name @{self.me.username}')

    def get_me(self) -> User:
        """
        Получает информацию о боте из Telegram.

        Returns:
            User: Объект, представляющий бота.
        """

        response = self._request.get(f'https://api.telegram.org/bot{self.token}/getMe')

        return User(response.json()['result'])

    def set_my_commands(self, commands: List[BotCommand], scope: Union[BotCommandScopeChat, BotCommandScopeDefault, BotCommandScopeChatMember, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats, BotCommandScopeChatAdministrators, BotCommandScopeAllChatAdministrators]=None, language_code: str=None) -> bool:
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
            'commands': [{'command': command.command, 'description': command.description} for command in commands]
        }

        if scope:
            parameters['scope'] = {"type": scope.type}
            if hasattr(scope, 'chat_id'):
                parameters['scope'].update({"chat_id": scope.chat_id})
            if hasattr(scope, 'user_id'):
                parameters['scope'].update({"user_id": scope.user_id})

        if language_code:
            parameters['language_code'] = language_code

        response = self._request.post(f'https://api.telegram.org/bot{self.token}/setMyCommands', json=parameters)

        return response.json()['ok']

    def send_message(self, chat_id: Union[int, str], text: Union[int, float, str], reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]]], str]=None, parse_mode: Union[str, ParseMode]=None, reply_to_message_id: int=None, disable_web_page_preview: bool=False) -> Message:
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

        reply_markup = handle_reply_markup(reply_markup)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = self._request.post(f"https://api.telegram.org/bot{self.token}/sendMessage", json=parameters)

        return Message(response.json()['result'], self)

    def send_photo(self, chat_id: Union[int, str], photo: Union[InputFile], caption: Union[int, float, str]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, parse_mode: Union[str, ParseMode]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет фотографию в чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата.
            photo (Union[InputFile]): Файл фотографии.
            caption (Union[int, float, str], optional): Подпись к фотографии.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup], optional): Клавиатура для сообщения.
            parse_mode (str, optional): Режим форматирования текста подписи.
            photo_name (str, optional): Имя файла фотографии.
            reply_to_message_id (int, optional): Если указан, сообщение будет отправлено как ответ на указанное сообщение.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
        parameters = {
            "chat_id": chat_id
        }

        files = {}

        files['photo'] = photo.file

        if caption is not None:
            parameters['caption'] = caption

        reply_markup = handle_reply_markup(reply_markup)
        
        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = self._request.post(f"https://api.telegram.org/bot{self.token}/sendPhoto", data=parameters, files=files)

        return Message(response.json()['result'], self)

    def message(self, _filters: Callable[[Message], Any]=None, content_types: Union[str, List[str]]=None, commands: Union[str, List[str]]=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None, state: State=None) -> Callable:
        """
        Декоратор для обработки входящих сообщений.

        Args:
            _filters (Callable[[Message], any], optional): Функция фильтрации сообщений.
            content_types (Union[str, List[str]], optional): Типы контента, которые должен обрабатывать обработчик.
            commands (Union[str, List[str]], optional): Команды, на которые должен реагировать обработчик.
            allowed_chat_type (Union[List[str], Tuple[str], str], optional): Типы чатов, в которых активен обработчик.
            state (StateRegExp, optional): Состояние в контексте машины состояний.

        Returns:
            Callable: Функция-обертка, которая регистрирует обработчик сообщений.
        """

        def wrapper(func):
            self._message_handlers.append({
                'func': func, 
                'filters': _filters, 
                'content_types': content_types, 
                'commands': commands, 
                'allowed_chat_type': allowed_chat_type, 
                'state': state
                })
        return wrapper

    def message_handler(self, _filters: Callable[[Message], Any]=None, content_types: Union[str, List[str]]=None, commands: Union[str, List[str]]=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None, state: State=None) -> Callable:
        """
        Декоратор для обработки входящих сообщений.Для миграции из pyTelegramBotAPI в EasyGram
        :param _filters: лямбда
        :param content_types: тип сообщения
        :param commands: команды(без префикса)
        :param allowed_chat_type: тип группы
        :param state: поле State
        :return: Функцию которую нужно вызвать
        """

        def wrapper(func):
            self._message_handlers.append({
                'func': func, 
                'filters': _filters, 
                'content_types': content_types, 
                'commands': commands, 
                'allowed_chat_type': allowed_chat_type, 
                'state': state
                })
        return wrapper

    def callback_query(self, _filters: Callable[[CallbackQuery], Any]=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None, state: State=None) -> Callable:
        """
        Декоратор для обработки вызовов InlineKeyboardMarkup кнопки.
        :param _filters: лямбда
        :param allowed_chat_type: тип группы
        :param state: поле State
        :return: Функцию которую нужно вызвать
        """

        def wrapper(func):
            self._callback_query_handlers.append({
                'func': func, 
                'filters': _filters, 
                'allowed_chat_type': allowed_chat_type, 
                'state': state
                })
        return wrapper

    def callback_query_handler(self, _filters: Callable[[CallbackQuery], Any]=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None, state: State=None) -> Callable:
        """
        Декоратор для обработки вызовов InlineKeyboardMarkup кнопки.Для миграции из pyTelegramBotAPI в EasyGram
        :param _filters: лямбда
        :param allowed_chat_type: тип группы
        :param state: поле State
        :return: Функцию которую нужно вызвать
        """

        def wrapper(func):
            self._callback_query_handlers.append({
                'func': func, 
                'filters': _filters, 
                'allowed_chat_type': allowed_chat_type, 
                'state': state
                })
        return wrapper
    
    def poll_handler(self, _filters: Callable[[Poll], Any]=None) -> Callable:
        """
        Декоратор для обработки опросов.Для миграции из pyTelegramBotAPI в EasyGram
        :param _filters: лямбда
        :return: Callable
        """

        def wrapper(func):
            self._poll_handlers.append({
                'func': func, 
                'filters': _filters
                })
        return wrapper
    
    def poll(self, _filters: Callable[[Poll], Any]=None) -> Callable:
        """
        Декоратор для обработки обновления данных опросов.
        :param _filters: лямбда
        :return: Callable
        """

        def wrapper(func):
            self._poll_handlers.append({
                'func': func, 
                'filters': _filters
                })
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

    def answer_callback_query(self, query_id: Union[int, str], text: Union[int, float, str]=None, show_alert: bool=False) -> bool:
        """
        Отправляет ответ на callback-запрос от пользователя.
        :param chat_id: Идентификатор чата, может быть целым числом или строкой.
        :param text: Текст сообщения, который будет показан пользователю в ответ на callback-запрос.
        :param show_alert: Если True, сообщение будет отображаться в виде всплывающего окна (alert).
        :return: Возвращает True, если запрос был успешным, иначе False.
        """
        parameters = {
            'callback_query_id': query_id,
            'text': str(text),
            'show_alert': show_alert
        }

        response = self._request.post(f"https://api.telegram.org/bot{self.token}/answerCallbackQuery", json=parameters)

        return response.json()['result']

    def delete_message(self, chat_id: Union[int, str], message_id: int) -> bool:
        """
        Удаляет сообщения.
        - Сообщение можно удалить, только если оно было отправлено менее 48 часов назад.
        - Сообщение в приватном чате можно удалить, только если оно было отправлено более 24 часов назад.
        :param chat_id: Айди чата
        :param message_id: Айди сообщения
        :return: Булевое значение
        """
        parameters = {
            'chat_id': chat_id,
            'message_id': message_id
        }

        response = self._request.post(f"https://api.telegram.org/bot{self.token}/deleteMessage", json=parameters)

        return response.json()['result']

    def edit_message_text(self, chat_id: Union[int, str], message_id: int, text: Union[int, float, str], parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, disable_web_page_preview: bool=False) -> bool:
        """
        Редактирование сообщения.Обратите внимание, что деловые сообщения, которые не были отправлены ботом и не содержат встроенной клавиатуры, можно редактировать только в течение 48 часов с момента отправки.
        :param chat_id: Айди чата
        :param message_id: Айди сообщения
        :param text: Текст
        :param parse_mode: Форматирования текста
        :param reply_markup: Кнопки
        :return: Булевое значение
        """

        parameters = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": str(text),
            "link_preview_options": {
                "is_disabled": disable_web_page_preview
            }
        }

        reply_markup = handle_reply_markup(reply_markup)

        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        response = self._request.post(f"https://api.telegram.org/bot{self.token}/editMessageText", json=parameters)

        return response.json()['result']

    def send_poll(self, chat_id: Union[int, str], question: Union[int, float, str], options: Union[List[PollOption], List[str]], question_parse_mode: Union[str, ParseMode]=None, is_anonymous: bool=True, type: str='regular', allows_multiple_answers: bool=False, correct_option_id: int=0, explanation: str=None, explanation_parse_mode: Union[str, ParseMode]=None, open_period: int=None, is_closed: bool=False, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправка опроса
        :param chat_id: Айди чата
        :param question: Вопрос
        :param options: Варианты
        :param question_parse_mode: Тип форматирования в вопросе
        :param is_anonymous: Анонимный опрос
        :param type: Тип опроса
        :param allows_multiple_answers: Выбор несколько вариантов
        :param correct_option_id: Правильный вариант(в индексах)
        :param explanation: Объяснение
        :param explanation_parse_mode: Тип форматирования в объяснениях
        :param open_period: Сколько будет доступен выбор вариантов
        :param is_closed: Закрыт
        :param reply_markup: Кнопка
        :param reply_to_message_id: Ответ на сообщение
        :return: Message
        """
        parameters = {
            "chat_id": chat_id,
            "question": str(question),
            "type": type,
            "allows_multiple_answers": allows_multiple_answers,
            "is_closed": is_closed,
            "is_anonymous": is_anonymous
        }

        reply_markup = handle_reply_markup(reply_markup)

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

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        if open_period is not None:
            parameters['open_period'] = open_period
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id
        
        if question_parse_mode is not None:
            parameters['question_parse_mode'] = question_parse_mode

        response = self._request.post(f"https://api.telegram.org/bot{self.token}/sendPoll", json=parameters)

        return Message(response.json()['result'], self)

    def send_audio(self, chat_id: Union[int, str], audio: Union[InputFile], title: str=None, caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправка аудио
        :param chat_id: Айди чата
        :param audio: Аудио
        :param title: Имя файла
        :param caption: Описание
        :param parse_mode: Тип форматирования
        :param reply_markup: Кнопка
        :param reply_to_message_id: Ответ на сообщение
        :return: Message
        """
        parameters = {
            "chat_id": chat_id
        }

        files = {

        }

        if isinstance(audio, str):
            with open(audio, 'rb') as f:
                files['audio'] = f
                parameters['title'] = f.name if title is None else title
        else:
            files['audio'] = audio
            parameters['title'] = 'audio' if title is None else title

        if caption is not None:
            parameters['caption'] = caption

        reply_markup = handle_reply_markup(reply_markup)
        
        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = self._request.post(f'https://api.telegram.org/bot{self.token}/sendAudio', data=parameters, files=files)

        return Message(response.json()['result'], self)

    def send_document(self, chat_id: Union[int, str], document: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправка документа
        :param chat_id: Айди чата
        :param document: Документ
        :param caption: Описание
        :param parse_mode: Тип форматирования
        :param reply_markup: Кнопка
        :param reply_to_message_id: Ответ на сообщение
        :return: Message
        """
        parameters = {
            "chat_id": chat_id
        }

        files = {

        }

        files['document'] = document.file

        if caption is not None:
            parameters['caption'] = caption

        reply_markup = handle_reply_markup(reply_markup)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = self._request.post(f'https://api.telegram.org/bot{self.token}/sendDocument', data=parameters, files=files)

        return Message(response.json()['result'], self)

    def send_animation(self, chat_id: Union[int, str], animation: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправка видео/гифки
        :param chat_id: Айди чата
        :param animation: Гифка/Видео
        :param caption: Описание
        :param parse_mode: Тип форматирования
        :param reply_markup: Кнопка
        :param reply_to_message_id: Ответ на сообщение
        :return: Message
        """
        parameters = {
            "chat_id": chat_id
        }

        files = {

        }

        files['animation'] = animation.file

        if caption is not None:
            parameters['caption'] = caption

        reply_markup = handle_reply_markup(reply_markup)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = self._request.post(f'https://api.telegram.org/bot{self.token}/sendAnimation', data=parameters, files=files)

        return Message(response.json()['result'], self)

    def send_voice(self, chat_id: Union[int, str], voice: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправка голосового сообщения
        :param chat_id: Айди чата
        :param voice: Голосовое сообщение
        :param caption: Описание
        :param parse_mode: Тип форматирования
        :param reply_markup: Кнопка
        :param reply_to_message_id: Ответ на сообщение
        :return: Message
        """
        parameters = {
            "chat_id": chat_id
        }

        files = {

        }

        files['voice'] = voice.file

        if caption is not None:
            parameters['caption'] = caption

        reply_markup = handle_reply_markup(reply_markup)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = self._request.post(f'https://api.telegram.org/bot{self.token}/sendVoice', data=parameters, files=files)

        return Message(response.json()['result'], self)

    def send_video(self, chat_id: Union[int, str], video: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправка видео
        :param chat_id: Айди чата
        :param video: Видео
        :param caption: Описание
        :param parse_mode: Тип форматирования
        :param reply_markup: Кнопка
        :param reply_to_message_id: Ответ на сообщение
        :return: Message
        """
        parameters = {
            "chat_id": chat_id
        }

        files = {

        }

        files['video'] = video.file

        if caption is not None:
            parameters['caption'] = caption

        reply_markup = handle_reply_markup(reply_markup)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = self._request.post(f'https://api.telegram.org/bot{self.token}/sendVideo', data=parameters, files=files)

        return Message(response.json()['result'], self)

    def send_video_note(self, chat_id: Union[int, str], video_note: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправка кружка
        :param chat_id: Айди чата
        :param video_note: Кружок
        :param caption: Описание
        :param parse_mode: Тип форматирование
        :param reply_markup: Кнопка
        :param reply_to_message_id: Ответ на сообщение
        :return: Message
        """
        parameters = {
            "chat_id": chat_id
        }

        files = {

        }

        files['video_note'] = video_note.file

        if caption is not None:
            parameters['caption'] = caption

        reply_markup = handle_reply_markup(reply_markup)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = self._request.post(f'https://api.telegram.org/bot{self.token}/sendVideoNote', data=parameters, files=files)

        return Message(response.json()['result'], self)

    def send_contact(self, chat_id: Union[int, str], number: str, first_name: str, last_name: str=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправка контактов
        :param chat_id: Айди чата
        :param number: Номер
        :param first_name: Имя контакта
        :param last_name: Фамилия контакта
        :param reply_markup: Кнопка
        :param reply_to_message_id: Ответ на сообщение
        :return: Message
        """
        parameters = {
            "chat_id": chat_id,
            "first_name": first_name
        }

        parameters['number'] = number

        if last_name is not None: parameters['last_name'] = last_name
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        reply_markup = handle_reply_markup(reply_markup)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        response = self._request.post(f'https://api.telegram.org/bot{self.token}/sendContact', json=parameters)

        return Message(response.json()['result'], self)

    def send_dice(self, chat_id: Union[int, str], emoji: str, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправка анимирующих эмодзи
        :param chat_id: Айди чата
        :param emoji: Эмодзи: 🎲, 🎯, 🏀, ⚽, 🎳, 🎰
        :param reply_markup: Кнопка
        :param reply_to_message_id: Ответ на сообщение
        :return: Message
        """
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        if emoji not in ['🎲', '🎯', '🏀', '⚽', '🎳', '🎰']:
            raise TypeError(f'Такой эмодзи {emoji} не допускается.')

        reply_markup = handle_reply_markup(reply_markup)

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        response = self._request.post(f'https://api.telegram.org/bot{self.token}/sendDice', json=parameters)

        return Message(response.json()['result'], self)

    def send_chat_action(self, chat_id: Union[int, str], action: Union[str, ChatAction]) -> None:
        """
        Установка статуса на определённое время
        :param chat_id: Айди чата
        :param action: Действие.Смотреть тип дествий в EasyGram.types.ChatAction/EasyGram.Async.types.ChatAction
        :return: None
        """
        parameters = {
            "chat_id": chat_id,
            "action": action
        }

        response = self._request.post(f'https://api.telegram.org/bot{self.token}/sendChatAction', json=parameters)
    
    def next_step_handler(self, chat_id: int, callback: Callable, *args) -> None:
        """
        Ставит 'триггер'.Как только определённый пользователь отправит сообщение вызывается функция
        :param chat_id: Айди чата
        :param callback: Функция
        :param args: Параметры к функции
        :return: None
        """
        self._next_step_handlers.append((str(chat_id), callback, args))
    
    def query_next_step_handler(self, chat_id: int, callback: Callable, *args):
        """
        Ставит 'триггер'.Как только определённый пользователь нажмёт на Inline кнопку вызывается функция.
        :param chat_id: Айди чата.
        :param callback: Функция.
        :param args: Параметры к функции.
        :return: None
        """
        self._query_next_step_handlers.append((str(chat_id), callback, args))
    
    def get_file(self, file_id: str) -> File:
        response = self._request.get(f'https://api.telegram.org/bot{self.token}/getFile', json={'file_id': file_id}).json()
        return File(response['result']['file_id'], response['result']['file_unique_id'], response['result']['file_size'], response['result']['file_path'])

    def download_file(self, file_path: str) -> BytesIO:
        if not file_path.startswith('https://api.telegram.org/file/'):
            raise ValueError('file_path не является ссылкой из телеграма.')

        response = self._request.get(file_path)
        return BytesIO(response)

    def edit_message_reply_markup(self, chat_id: Union[int, str]=None, message_id: Union[int, str]=None, inline_message_id: Union[int, str]=None, reply_markup: Union[InlineKeyboardMarkup, InlineKeyboardButton, list[list[InlineKeyboardButton]]]=None) -> bool:
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
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.keyboard}
            elif isinstance(reply_markup, list):
                parameters['reply_markup'] = {'inline_keyboard': InlineKeyboardMarkup(builder=reply_markup)}
        
        response = self._request.get(f'https://api.telegram.org/bot{self.token}/editMessageReplyMarkup', json=parameters)
        return response.ok()

    def polling(self, on_startup: Callable=None, threaded_run: bool=False, thread_max_works: int=10, *args) -> None:
        """
        Запускает процесс опроса событий, выполняя указанную функцию при старте.

        :param on_startup: Функция, которая будет вызвана при запуске опроса (например, для инициализации).
        :param args: Дополнительные аргументы, которые будут переданы в функцию on_startup.
        :param threaded_run: Запуск с потоком.
        :param thread_max_works: Ограничения по потокам(!Чем больше потоков запустится, тем сильнее нагружается процессор!)
        :return: Ничего не возвращает.
        """
        if on_startup is not None:  on_startup(*args)

        if threaded_run:
            executor = ThreadPoolExecutor(thread_max_works)

        while True:
            try:
                updates = self._request.get(f'https://api.telegram.org/bot{self.token}/getUpdates', params={"offset": self.offset, "timeout": 30, "allowed_updates": ["message", "callback_query", "poll", "poll_answer"]})
            except Exception as e:
                traceback.print_exc()
                continue

            if updates.status_code != 200:
                continue

            updates = updates.json()['result']

            for update in updates:
                try:
                    self.offset = update["update_id"] + 1

                    if update.get('message', False):
                        
                        for indx, step in enumerate(self._next_step_handlers):
                            if str(update['message']['chat']['id']) == step[0]:
                                if threaded_run:
                                    executor.submit(step[1], Message(update['message'], self), *step[2])
                                else:
                                    self.__run_func_with_try_except__(step[1], Message(update['message'], self), *step[2])
                                
                                self._next_step_handlers.pop(indx)
                                break
                        
                        for handler_message in self._message_handlers:
                            if handler_message['filters'] is not None and not handler_message['filters'](Message(update['message'], self)):
                                continue

                            if handler_message['commands'] is not None:
                                if not update['message'].get('text', False):
                                    continue

                                if isinstance(handler_message['commands'], list):
                                    if not any(update['message']['text'].split()[0] == '/' + command for command in handler_message['commands']):
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
                                executor.submit(self.__run_func_with_try_except__, [handler_message['func'], *parameters])
                            else:
                                self.__run_func_with_try_except__(handler_message['func'], *parameters)
                            
                            break
                    elif update.get('callback_query', False):
                        for indx, step in enumerate(self._query_next_step_handlers):
                            if str(update['message']['chat']['id']) == step[0]:
                                if threaded_run:
                                    executor.submit(step[1], CallbackQuery(update['callback_queyr'], self), *step[2])
                                else:
                                    step[1](CallbackQuery(update['callback_queyr'], self), *step[2])
                                
                                self._queyr_next_step_handlers.pop(indx)
                                break

                        for callback in self._callback_query_handlers:
                            if callback['filters'] is not None and not callback['filters'](Message(update['callback_query'], self)):
                                continue

                            if callback['allowed_chat_type'] is not None:
                                if isinstance(callback['allowed_chat_type'], str):
                                    if update['callback_query']['chat']['type'] != callback['allowed_chat_type']:
                                        continue
                                elif isinstance(callback['allowed_chat_type'], (tuple, list)):
                                    if not any(update['callback_query']['chat']['type'] == _chat_type for _chat_type in callback['allowed_chat_type']):
                                        continue
                            
                            if callback['state'] is not None:
                                if update['message']['from']['id'] not in StatesGroup.user_registers:
                                    continue

                                if callback['state'] != StatesGroup.user_registers[update['message']['from']['id']]['state']:
                                    continue
                            
                            callback_query = CallbackQuery(update['callback_query'], self)
                            parameters = [callback_query]
                            parameters.append(FSMContext(callback_query.from_user.id))

                            is_method = inspect.ismethod(callback['func'])
                            _parameters = list(inspect.signature(callback['func']).parameters)

                            if is_method and len(_parameters) > 0: _parameters.pop(0)

                            if len(_parameters) == 1: parameters.pop(1)

                            if threaded_run:
                                executor.submit(self.__run_func_with_try_except__, [callback['func'], *parameters])
                            else:
                                self.__run_func_with_try_except__(callback['func'], *parameters)
                            
                            break
                    elif update.get('poll', False):
                        for poll in self._poll_handlers:
                            if poll['filters'] is not None and not poll['filters'](Poll(update['poll'])):
                                continue
                            
                            _poll = Poll(update['poll'])

                            if threaded_run:
                                executor.submit(self.__run_func_with_try_except__, [poll['func'], *parameters])
                            else:
                                self.__run_func_with_try_except__(poll['func'], *parameters)
                            break
                    elif update.get('poll_answer', False):
                        for poll_answer in self._poll_answer_handlers:
                            if poll_answer['filters'] is not None and not poll_answer['filters'](PollAnswer(update['poll_answer'])):
                                continue
                            
                            if poll_answer['state'] is not None:
                                if update['poll_answer']['user']['id'] not in StatesGroup.user_registers:
                                    continue

                                if poll_answer['state'] != StatesGroup.user_registers[update['poll_answer']['user']['id']]['state']:
                                    continue
                            
                            _poll = PollAnswer(update['poll'])

                            if threaded_run:
                                executor.submit(self.__run_func_with_try_except__, [poll['func'], _poll])
                            else:
                                self.__run_func_with_try_except__(poll['func'], _poll)
                            break
                except Exception as e:
                    self.logger.error(traceback.format_exc())
    
    def start_polling(self, on_startup: Callable=None, threaded_run: bool=False, thread_max_works: int=10, *args) -> None:
        self.polling(on_startup, threaded_run, thread_max_works, *args)
    
    def __run_func_with_try_except__(self, func: Callable, *args):
        """
        Функция для логирования.
        """

        try:
            func(*args)
        except:
            self.logger.error(traceback.format_exc())