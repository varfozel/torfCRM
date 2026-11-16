from typing import Any, Dict, Optional, Union
from aiogram.methods.base import TelegramMethod
from aiogram.types import InlineKeyboardMarkup, Message


class SendWidget(TelegramMethod[Message]):
    """
    Telegram Bot API 10.4 method to send an interactive HTML Widget inside a chat bubble.
    """
    __returning__ = Message
    __api_method__ = "sendWidget"

    chat_id: Union[int, str]
    html: str
    chat_data: Optional[str] = None
    caption: Optional[str] = None
    parse_mode: Optional[str] = None
    protect_content: Optional[bool] = True
    reply_markup: Optional[InlineKeyboardMarkup] = None


class AnswerWidgetQuery(TelegramMethod[bool]):
    """
    Responds to a widget query sent by TelegramWidget.request() on the client.
    Must be called within 15 seconds.
    """
    __returning__ = bool
    __api_method__ = "answerWidgetQuery"

    widget_query_id: str
    text: Optional[str] = None
    show_alert: Optional[bool] = False
    data: Optional[str] = None


class EditMessageWidgetData(TelegramMethod[bool]):
    """
    Dynamically edits the state/chat_data of an existing widget message without creating a new message.
    Triggers chatDataChanged event in the client widget.
    """
    __returning__ = bool
    __api_method__ = "editMessageWidgetData"

    chat_id: Union[int, str]
    message_id: int
    chat_data: str
