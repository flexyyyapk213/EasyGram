from typing import Union
from .Async.types import InlineKeyboardButton as asyncInlineKeyboardButton, KeyboardButton as asyncKeyboardButton, InlineKeyboardMarkup as asyncInlineKeyboardMarkup, ReplyKeyboardMarkup as asyncReplyKeyboardMarkup
from .types import InlineKeyboardButton as syncInlineKeyboardButton, KeyboardButton as syncKeyboardButton, InlineKeyboardMarkup as syncInlineKeyboardMarkup, ReplyKeyboardMarkup as syncReplyKeyboardMarkup

def handle_reply_markup(reply_markup: Union[asyncInlineKeyboardButton, syncInlineKeyboardButton, asyncKeyboardButton, syncKeyboardButton, str, list[list[Union[asyncInlineKeyboardButton, syncInlineKeyboardButton, asyncKeyboardButton, syncKeyboardButton, str]]]], async_mode: bool=False) -> Union[asyncInlineKeyboardMarkup, asyncReplyKeyboardMarkup, syncInlineKeyboardMarkup, syncReplyKeyboardMarkup, None]:
    """
    Args:
        reply_markup (Union[asyncInlineKeyboardButton, syncInlineKeyboardButton, asyncKeyboardButton, syncKeyboardButton, str, list[list[asyncInlineKeyboardButton, syncInlineKeyboardButton, asyncKeyboardButton, syncKeyboardButton, str]]]): Передаваеммая кнопка.str = KeyboardButton
        async_mode (bool): Чтобы определиться, EasyGram.Async.types.KeyboardButton или EasyGram.types.KeyboardButton
    Return:
        Union[asyncInlineKeyboardMarkup, asyncReplyKeyboardMarkup, syncInlineKeyboardMarkup, syncReplyKeyboardMarkup, None]
    """

    if isinstance(reply_markup, (asyncInlineKeyboardButton, syncInlineKeyboardButton)):
        if isinstance(reply_markup, asyncInlineKeyboardButton):
            _btn = asyncInlineKeyboardMarkup()
            _btn.add(reply_markup)

            return _btn
        else:
            _btn = syncInlineKeyboardMarkup()
            _btn.add(reply_markup)

            return _btn
    elif isinstance(reply_markup, (asyncKeyboardButton, syncKeyboardButton)):
        if isinstance(reply_markup, asyncKeyboardButton):
            _btn = asyncReplyKeyboardMarkup()
            _btn.add(reply_markup)

            return _btn
        else:
            _btn = syncReplyKeyboardMarkup()
            _btn.add(reply_markup)

            return _btn
    elif isinstance(reply_markup, (asyncInlineKeyboardMarkup, syncInlineKeyboardMarkup, asyncReplyKeyboardMarkup, syncReplyKeyboardMarkup)):
        return reply_markup
    elif isinstance(reply_markup, str):
        if async_mode:
            _btn = asyncReplyKeyboardMarkup()
        else:
            _btn = syncReplyKeyboardMarkup()

        _btn.add(reply_markup)

        return _btn
    elif isinstance(reply_markup, list):
        btns = []
        _type: Union[asyncInlineKeyboardButton, syncInlineKeyboardButton, asyncKeyboardButton, syncKeyboardButton, None] = None
        _kb_type: Union[asyncInlineKeyboardMarkup, syncInlineKeyboardMarkup, asyncReplyKeyboardMarkup, syncReplyKeyboardMarkup, None] = None
        kb = None

        for column in reply_markup:
            _btns = []
            __type = None

            for row in column:
                if handle_reply_markup(row) is None:
                    return None
                
                if isinstance(row, str):
                    if async_mode:
                        _btns.append(asyncKeyboardButton(row))

                        _kb_type = asyncReplyKeyboardMarkup
                        __type = asyncKeyboardButton
                    else:
                        _btns.append(syncKeyboardButton(row))

                        _kb_type = syncReplyKeyboardMarkup
                        __type = syncKeyboardButton
                elif isinstance(row, list):
                    return None
                elif isinstance(row, (asyncInlineKeyboardButton, syncInlineKeyboardButton, asyncKeyboardButton, syncKeyboardButton)):
                    _btns.append(row)

                    if isinstance(row, asyncInlineKeyboardButton):
                        _kb_type = asyncInlineKeyboardMarkup
                        __type = asyncInlineKeyboardButton
                    elif isinstance(row, syncInlineKeyboardButton):
                        _kb_type = syncInlineKeyboardMarkup
                        __type = syncInlineKeyboardButton
                    elif isinstance(row, asyncKeyboardButton):
                        _kb_type = asyncReplyKeyboardMarkup
                        __type = asyncKeyboardButton
                    elif isinstance(row, syncKeyboardButton):
                        _kb_type = syncReplyKeyboardMarkup
                        __type = syncKeyboardButton
                else:
                    return None
                
                if _type is None:
                    _type = __type
            
            if _type != None and _type != __type:
                return None
            
            btns.append(_btns.copy())

        kb = _kb_type()
        
        if _type is not None:
            for btn in btns:
                kb.add(*btn)
        
        return kb
    else:
        return None