from typing import Optional, Union, List, BinaryIO, Callable, Any
import requests
from .exception import ButtonParameterErorr, Telegram
import traceback
from io import BytesIO, IOBase
from pathlib import Path
import json
import logging
from copy import deepcopy

from .exception import (
    ButtonParameterErorr,
    Telegram,
    Unauthorized,
    BadRequest,
    Forbidden,
    TooManyRequests
)

class GetMe:
    """
    Этот класс используется для получения информации о боте.
    :param bot: Объект бота.
    """
    def __init__(self, bot):
        self.id: int = requests.get(f'https://api.telegram.org/bot{bot.token}/getMe').json()['result']['id']
        self.other = requests.get(f'https://api.telegram.org/bot{bot.token}/getMe').json()['result']

class KeyboardButton:
    """
    Этот класс используется для создания кнопки клавиатуры.
    :param text: Текст кнопки.
    :return: Созданная кнопка.
    """
    def __init__(self, text: Union[int, float, str]):
        self.keyboard = {'text': str(text)}

class ReplyKeyboardMarkup:
    """
    Этот класс используется для создания клавиатуры ответа.
    :param row_width: Количество кнопок в каждом ряду.
    :param resize_keyboard: Должна ли клавиатура изменять размер.
    """
    def __init__(self, row_width: int=3, resize_keyboard: bool=False, builder: list[list[Union[str, KeyboardButton]]]=None):
        self.rows = [] if builder is None else builder
        self.row_width = row_width
        self.resize_keyboard = resize_keyboard

        if builder:
            self.__check_builder__()

    def add(self, *args: Union[str, KeyboardButton]) -> None:
        """
        Этот метод используется для добавления кнопки в клавиатуру.
        :param args: Кнопки для добавления.
        :return: None
        """
        _butt = []

        for butt in args:
            if isinstance(butt, KeyboardButton):
                _butt.append(butt.keyboard)
            else:
                _butt.append({'text': butt})

            if len(_butt) == self.row_width:
                self.rows.append(_butt)
                _butt = []
        else:
            if _butt:
                self.rows.append(_butt)
    
    def __str__(self):
        return f"ReplyKeyboardMarkup(rows={json.dumps(self.rows, ensure_ascii=False)}, row_width={self.row_width}, resize_keyboard={self.resize_keyboard})"
    
    def __check_builder__(self):
        for column in self.rows:
            for row in column:
                if not isinstance(row, dict):
                    self.rows.clear()
                    raise TypeError('Неверный тип кнопки.')

class InlineKeyboardButton:
    """
    Этот класс используется для создания кнопки встроенной клавиатуры.
    :param text: Текст кнопки.
    :param url: URL, который должна открыть кнопка.
    :param callback_data: Данные, которые должны быть отправлены при нажатии на кнопку.
    """
    def __init__(self, text: Union[int, float, str], url: str=None, callback_data: str=None):
        self.keyboard = {'text': str(text)}

        if url is None and callback_data is None:
            raise ButtonParameterErorr('Для создания кнопки необходимо указать либо "url", либо "callback_data".')

        if url is not None and callback_data is not None:
            raise ButtonParameterErorr('Для создания кнопки необходимо указать либо "url", либо "callback_data"')

        if url is not None:
            self.keyboard.update({'url': str(url)})
        elif callback_data is not None:
            self.keyboard.update({'callback_data': str(callback_data)})

class InlineKeyboardMarkup:
    """
    Этот класс используется для создания встроенной клавиатуры.
    :param row_with: Количество рядов в клавиатуре.
    """
    def __init__(self, row_width: int=3, builder: list[list[InlineKeyboardButton]]=None):
        self.rows = [] if builder is None else deepcopy(builder)
        self.row_width = row_width
        self.storage: List = []

        if builder:
            self.__check_builder__()
        
            builder.clear()

    def add(self, *args: InlineKeyboardButton) -> None:
        """
        Этот метод используется для добавления кнопки встроенной клавиатуры.
        :param args: Кнопки для добавления.
        :return: None
        """
        _butt = []

        for butt in args:
            if isinstance(butt, InlineKeyboardButton):
                _butt.append(butt.keyboard)

            if len(_butt) == self.row_width:
                self.rows.append(_butt)
                _butt = []
        else:
            if _butt:
                self.rows.append(_butt)
    def add_tostorage(self, *args: InlineKeyboardButton) -> None:
        """
        Этот метод используется для добавления кнопок в хранилище, чтобы их можно было добавить в один ряд.
        :param args: Кнопки для добавления.
        :return: None
        """
        if not args: return None
        self.storage.extend(args)
    def add_keyboards(self) -> None:
        """
        Этот метод используется для добавления всех кнопок из хранилища в один ряд.
        :return: None
        """
        self.add(*self.storage)
        self.storage = []
    
    def __str__(self):
        return f"InlineKeyboardMarkup(rows={json.dumps(self.rows, ensure_ascii=False)}, row_width={self.row_width}, storage={json.dumps(self.storage, ensure_ascii=False, indent=4)})"

    def __check_builder__(self):
        for column in self.rows:
            for row in column:
                if not isinstance(row, dict):
                    self.rows.clear()
                    raise TypeError('Неверный тип кнопки.')

class ParseMode:
    """
    Этот класс используется для форматирования текста.
    """
    html: str = 'html'
    markdown: str = 'markdown'
    markdownv2: str = 'markdownv2'
    HTML: str = html
    MARKDOWN: str = markdown
    MARKDOWNV2: str = markdownv2
    MarkDown: str = markdown
    MarkDownV2: str = markdownv2

    @staticmethod
    def hbold(text: str) -> str:
        return '<b>' + text + '</b>'

    @staticmethod
    def hitalic(text: str) -> str:
        return '<i>' + text + '</i>'

    @staticmethod
    def hunderline(text: str) -> str:
        return '<u>' + text + '</u>'

    @staticmethod
    def hstrikeline(text: str) -> str:
        return '<s>' + text + '</s>'

    @staticmethod
    def hblockquote(text: str) -> str:
        return '<blockquote>' + text + '</blockquote>'

    @staticmethod
    def hcode(text: str) -> str:
        return '<code>' + text + '</code>'

    @staticmethod
    def hprecode(lang: str, text: str) -> str:
        return f'<pre><code class="{lang}">' + text + '</code></pre>'

class PollOption:
    """
    Этот класс используется для создания варианта ответа.
    :param text: Текст опции.
    :param text_parse_mode: Форматирования текста.
    """
    def __init__(self, text: Union[int, float, str], text_parse_mode: Union[str, ParseMode]=None):
        if len(text) > 1_000:
            try:
                raise Telegram('Слишком длинный текст.')
            except Telegram as e:
                traceback.print_exc(e)
                return

        self.text = text
        self.text_parse_mode = text_parse_mode

class InputFile:
    """
    Этот класс используется для безопасной вставки файла.
    :param file: Байт или объект класса Path.
    """
    def __init__(self, file: Union[IOBase, BinaryIO, BytesIO, Path]):
        if isinstance(file, (IOBase, BinaryIO, BytesIO)):
            self.file = file
        elif isinstance(file, Path):
            with open(file, 'rb') as f:
                self.file = BytesIO(f.read())
        elif isinstance(file, str):
            with open(file, 'rb') as f:
                self.file = BytesIO(f.read())
        else:
            raise TypeError('Unknow file type')

class ChatAction:
    """
    Этот класс используется для выполнения действий в чате.
    """
    TYPING = 'typing'
    UPLOAD_PHOTO = 'upload_photo'
    RECORD_VIDEO = 'record_video'
    UPLOAD_VIDEO = 'upload_video'
    RECORD_VOICE = 'record_voice'
    UPLOAD_VOICE = 'upload_voice'
    UPLOAD_DOCUMENT = 'upload_document'
    CHOOSE_STIKER = 'choose_sticker'
    FIND_LOCATION = 'find_location'
    RECORD_VIDEO_NOTE = 'record_video_note'
    UPLOAD_VIDEO_NOTE = 'upload_video_note'
    typing = 'typing'
    upload_photo = 'upload_photo'
    record_video = 'record_video'
    upload_video = 'upload_video'
    record_voice = 'record_voice'
    upload_voice = 'upload_voice'
    upload_document = 'upload_document'
    choose_sticker = 'choose_sticker'
    find_location = 'find_location'
    record_video_note = 'record_video_note'
    upload_video_note = 'upload_video_note'

class Poll:
    """
    Этот класс используется для создания опроса.
    :param poll: Опрос.
    """
    def __init__(self, poll: dict):
        self.id: Optional[int] = poll.get('id', None)
        self.question: Optional[str] = poll.get('question', None)
        self.question_entities: Optional[list] = poll.get('question_entities', None)
        self.options = poll.get('options', None)
        self.total_voter_count = poll.get('total_voter_count', None)
        self.is_closed = poll.get('is_closed', None)
        self.is_anonymous = poll.get('is_anonymous', None)
        self.type = poll.get('type', None)
        self.allows_multiple_answers = poll.get('allows_multiple_answers', None)
        self.correct_option_id = poll.get('correct_option_id', None)
        self.explanation = poll.get('explanation', None)
        self.explanation_entities = poll.get('explanation_entities', None)
        self.open_period = poll.get('open_period', None)
        self.close_date = poll.get('close_date', None)
    
    def __str__(self):
        return json.dumps({
            "id": self.id,
            "question": self.question,
            "question_entities": self.question_entities,
            "options": self.options,
            "total_voter_count": self.total_voter_count,
            "is_closed": self.is_closed,
            "is_anonymous": self.is_anonymous,
            "type": self.type,
            "allows_multiple_answers": self.allows_multiple_answers,
            "correct_option_id": self.correct_option_id,
            "explanation": self.explanation,
            "explanation_entities": self.explanation_entities,
            "open_period": self.open_period,
            "close_date": self.close_date
        }, ensure_ascii=False)

class PollAnswer:
    def __init__(self, poll_answer: dict):
        id: Optional[int] = poll_answer.get('poll_id', None)
        from_user: Optional[User] = User(poll_answer['user']) if poll_answer.get('user', False) else None
        option_ids: Optional[list[int]] = poll_answer.get('option_ids', None)
    
    def __str__(self):
        return json.dumps({
            'id': self.id,
            'from_user': self.from_user,
            'option_ids': self.option_ids
        }, ensure_ascii=False)

class Message:
    """
    Класс Message.
    :param message: сообщение
    :param bot: объект бота
    """
    def __init__(self, message: dict, bot):
        self.message_id: Optional[int] = message.get('message_id', None)
        self.from_user: Optional[User] = User(message['from']) if message.get('from', False) else None
        self.chat: Optional[Chat] = Chat(message['chat']) if message.get('chat', False) else None
        self.date: Optional[int] = message.get('date', None)
        self.text: Optional[str] = message.get('text', None)
        self.reply_to_message: Optional[Message] = Message(message['reply_to_message'], bot) if message.get('reply_to_message', False) else None
        self.is_bot: Optional[bool] = message.get('is_bot', None)
        self.caption: Optional[str] = message.get('caption', None)
        self.user_id: Optional[int] = getattr(self.from_user, 'id', None)
        self.chat_id: Optional[str] = getattr(self.chat, 'id', None)
        self.poll: Optional[Poll] = Poll(message['poll']) if message.get('poll', False) else None
        self.poll_answer: Optional[PollAnswer] = PollAnswer(message['poll_answer']) if message.get('poll_answer', False) else None
        self._other: dict = message

        self.bot = bot

    def answer(self, text: str, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, parse_mode: str=None, disable_web_page_preview: bool=False) -> 'Message':
        return self.bot.send_message(self.chat.id, text, reply_markup, parse_mode, disable_web_page_preview=disable_web_page_preview)
    
    def edit(self, text: str, reply_marlup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, parse_mode: str=None, disable_web_page_preview: bool=False) -> bool:
        return self.bot.edit_message.text(self.chat.id, self.message_id, text, reply_marlup, parse_mode, disable_web_page_preview=disable_web_page_preview)

    def delete(self):
        self.bot.delete_message(self.chat.id, self.message_id)
    
    def send_poll(self, question: Union[int, float, str], options: Union[List[PollOption], List[str]], question_parse_mode: Union[str, ParseMode]=None, is_anonymous: bool=True, type: str='regular', allows_multiple_answers: bool=False, correct_option_id: int=0, explanation: str=None, explanation_parse_mode: Union[str, ParseMode]=None, open_period: int=None, is_closed: bool=False, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None) -> 'Message':
        return self.bot.send_poll(self.chat.id, question, options, question_parse_mode, is_anonymous, type, allows_multiple_answers, correct_option_id, explanation, explanation_parse_mode, open_period, is_closed, reply_markup)
    
    def send_audio(self, audio: Union[IOBase, BytesIO, BinaryIO, str], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None) -> 'Message':
        return self.bot.send_audio(self.chat.id, audio, caption, parse_mode, reply_markup)
    
    def send_document(self, document: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None) -> 'Message':
        return self.bot.send_document(self.chat.id, document, caption, parse_mode, reply_markup)
    
    def send_animation(self, animation: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None) -> 'Message':
        return self.bot.send_animation(self.chat.id, animation, caption, parse_mode, reply_markup)
    
    def send_voice(self, voice: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None) -> 'Message':
        return self.bot.send_voice(self.chat.id, voice, caption, parse_mode, reply_markup)
    
    def send_video(self, video: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None) -> 'Message':
        return self.bot.send_video(self.chat.id, video, caption, parse_mode, reply_markup)
    
    def send_video_note(self, video_note: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None) -> 'Message':
        return self.bot.send_video_note(self.chat.id, video_note, caption, parse_mode, reply_markup)
    
    def send_paid_media(self, paid_media: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None) -> 'Message':
        return self.bot.send_paid_media(self.chat.id, paid_media, caption, parse_mode, reply_markup)
    
    def send_contact(self, number: str, first_name: str, last_name: str=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None) -> 'Message':
        return self.bot.send_contact(self.chat.id, number, first_name, last_name, reply_markup)
    
    def send_dice(self, emoji: str, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None) -> 'Message':
        return self.bot.send_dice(self.chat.id, emoji, reply_markup)
    
    def send_chat_action(self, action: Union[ChatAction, str]):
        self.bot.send_chat_action(self.chat.id, action)
    
    def reply(self, text: str, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, list[list[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]], str, None]=None, parse_mode: str=None, disable_web_page_preview: bool=False) -> 'Message':
        return self.bot.send_message(self.chat.id, text, reply_markup, parse_mode, reply_to_message_id=self.message_id, disable_web_page_preview=disable_web_page_preview)

    def edit_reply_markup(self, message_id: Union[int, str]=None, inline_message_id: Union[int, str]=None, reply_markup: Union[InlineKeyboardMarkup, InlineKeyboardButton, list[list[InlineKeyboardButton]]]=None) -> bool:
        return self.bot.edit_message_reply_markup(self.chat.id, message_id, inline_message_id, reply_markup)
    
    def __str__(self):
        return json.dumps({
            'message_id': self.message_id,
            'from_user': str(self.from_user),
            'chat': str(self.chat),
            'date': self.date,
            'text': self.text,
            'reply_to_message': str(self.reply_to_message),
            'is_bot': self.is_bot,
            'caption': self.caption,
            'other': self._other
        }, ensure_ascii=False)

class CallbackQuery:
    def __init__(self, callback_query: dict, bot):
        self.id: Optional[int] = callback_query.get('id', None)
        try:
            callback_query['message']['from']['id'] = callback_query['from']['id']
        except:
            pass
        self.message: Optional[Message] = Message(callback_query.get('message', None), bot)
        self.from_user: Optional[User] = User(callback_query['from']) if callback_query.get('from', False) else None
        self.chat: Optional[Chat] = Chat(callback_query['message']['chat']) if callback_query.get('message', {}).get('chat', False) else None
        self.data: str = callback_query['data']
        self.user_id: Optional[int] = getattr(self.from_user, 'id', None)
        self.chat_id: Optional[str] = getattr(self.chat, 'id', None)
        self._other: dict = callback_query

        self.bot = bot

    def answer(self, text: Union[str, int, float], show_alert: bool=False):
        self.bot.answer_callback_query(self.id, str(text), show_alert)
        
    def __str__(self):
        return json.dumps({
            'id': self.id,
            'message': str(self.message) if self.message else None,
            'from_user': str(self.from_user) if self.from_user else None,
            'chat': str(self.chat) if self.chat else None,
            'data': self.data,
            'other': self._other
        }, ensure_ascii=False)

class User:
    """
    User object.
    """
    def __init__(self, user: dict):
        self.id: Optional[int] = user.get('id', None)
        self.is_bot: Optional[bool] = user.get('is_bot', None)
        self.first_name: Optional[str] = user.get('first_name', None)
        self.username: Optional[str] = user.get('username', None)
        self.last_name: Optional[str] = user.get('last_name', None)
        
    def __str__(self):
        return json.dumps({
            'id': self.id,
            'is_bot': self.is_bot,
            'first_name': self.first_name,
            'username': self.username,
            'last_name': self.last_name
        }, ensure_ascii=False)

class Chat:
    """
    Chat object.
    """
    def __init__(self, chat: dict):
        self.id: Optional[int] = chat.get('id', None)
        self.first_name: Optional[str] = chat.get('first_name', None)
        self.title: Optional[str] = self.first_name
        self.username: Optional[str] = chat.get('username', None)
        self.type: Optional[str] = chat.get('type', None)
        
    def __str__(self):
        return json.dumps({
            'id': self.id,
            'first_name': self.first_name,
            'title': self.title,
            'username': self.username,
            'type': self.type
        }, ensure_ascii=False)

class ChatType:
    def __init__(self):
        self.private = 'private'
        self.group = 'group'
        self.supergroup = 'supergroup'
        self.channel = 'channel'
        
    def __str__(self):
        return json.dumps({
            'private': self.private,
            'group': self.group,
            'supergroup': self.supergroup,
            'channel': self.channel
        })

class ContentType:
    def __init__(self):
        self.text = 'text'
        self.photo = 'photo'
        self.video = 'video'
        self.audio = 'audio'
        self.document = 'document'
        self.animation = 'animation'
        self.voice = 'voice'
        self.video_note = 'video_note'
        self.location = 'location'
        self.contact = 'contact'
        self.sticker = 'sticker'
        self.poll = 'poll'
        self.dice = 'dice'
        self.game = 'game'
        self.invoice = 'invoice'
        self.venue = 'venue'
    
    def __str__(self) -> str:
        return json.dumps({
            'text': self.text,
            'photo': self.photo,
            'video': self.video,
            'audio': self.audio,
            'document': self.document,
            'animation': self.animation,
            'voice': self.voice,
            'video_note': self.video_note,
            'location': self.location,
            'contact': self.contact,
            'sticker': self.sticker,
            'poll': self.poll,
            'dice': self.dice,
            'game': self.game,
            'invoice': self.invoice,
            'venue': self.venue
        }, ensure_ascii=False)

class BotCommand:
    def __init__(self, command: str, description: str):
        self.command = command
        self.description = description

class BotCommandScopeDefault:
    def __init__(self):
        self.type = 'default'

class BotCommandScopeAllPrivateChats:
    def __init__(self):
        self.type = 'all_private_chats'

class BotCommandScopeAllGroupChats:
    def __init__(self):
        self.type = 'all_group_chats'

class BotCommandScopeAllChatAdministrators:
    def __init__(self):
        self.type = 'all_chat_administrators'

class BotCommandScopeChat:
    def __init__(self, chat_id: Union[int, str]):
        self.type = 'chat'
        self.chat_id = chat_id

class BotCommandScopeChatAdministrators:
    def __init__(self, chat_id: Union[int, str]):
        self.type = 'chat_administrators'
        self.chat_id = chat_id

class BotCommandScopeChatMember:
    def __init__(self, chat_id: Union[int, str], user_id: int):
        self.type = 'chat_member'
        self.chat_id = chat_id
        self.user_id = user_id

class Request:
    def __init__(self, log_level: int=logging.INFO, timeout: int=None):
        """
        Args:
            log_level (int): Logging level
            timeout (int, optional): The maximum waiting time
        
        Raises:
            Unauthorized
        """
        self.__session__: requests.Session = requests.Session()

        self.timeout = timeout

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

    def get(self, url: str, **kwargs: Any) -> Union[requests.Response, bytes]:
        with self.__session__.get(url, **kwargs, timeout=self.timeout) as response:
            content_type = response.headers.get('Content-Type', '').lower()
            self.logger.debug(f'Request (get) to {url} with parameters {kwargs}: Successfully')

            if 'application/json' in content_type:
                _result = response.json()

                if not _result['ok']:
                    error_description = _result['description'].lower()
                    
                    if error_description == 'unauthorized':
                        raise Unauthorized(error_description)
                    elif error_description.startswith('bad request'):
                        raise BadRequest(error_description)
                    elif error_description.startswith('forbidden'):
                        raise Forbidden(error_description)
                    elif error_description.startswith('too many requests'):
                        raise TooManyRequests(error_description, value=_result['parameters']['retry_after'])
                    else:
                        raise Telegram(error_description)

                return response
            else:
                return response.content
    
    def post(self, url: str, **kwargs: Any) -> requests.Response:
        with self.__session__.post(url, **kwargs, timeout=self.timeout) as response:
            content_type = response.headers.get('Content-Type', '').lower()
            self.logger.debug(f'Request (post) to {url} with parameters {kwargs}: Successfully')

            if 'application/json' in content_type:
                _result = response.json()

                if not _result['ok']:
                    error_description = _result['description'].lower()
                    
                    if error_description == 'unauthorized':
                        raise Unauthorized(error_description)
                    elif error_description.startswith('bad request'):
                        raise BadRequest(error_description)
                    elif error_description.startswith('forbidden'):
                        raise Forbidden(error_description)
                    elif error_description.startswith('too many requests'):
                        raise TooManyRequests(error_description, value=_result['parameters']['retry_after'])
                    else:
                        raise Telegram(error_description)

                return response
            else:
                return response.content

class File:
    def __init__(self, file_id: str, file_unique_id: str, file_size: str, file_path: str):
        """
        `file_id` (str): Identifier for this file, which can be used to download or reuse the file.
        
        `file_unique_id` (str): Unique identifier for this file, which is supposed to be the same over time and for different bots. Can't be used to download or reuse the file.

        `file_size` (int): Optional. File size in bytes. It can be bigger than 2^31 and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or double-precision float type are safe for storing this value.

        `file_path` (str): Optional. File path. Use `https://api.telegram.org/file/bot<token>/<file_path>` or `bot.download_file(file_path)` to get the file.
        """
        self.file_id: str = file_id
        self.file_unique_id: str = file_unique_id
        self.file_size: int = file_size
        self.file_path: str = file_path