from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field
from aiogram.types import Message, User


class WidgetQuery(BaseModel):
    """
    Update payload received when a user interacts with an HTML Widget via TelegramWidget.request().
    """
    model_config = ConfigDict(populate_by_name=True)

    id: str
    from_user: User = Field(alias="from")
    message: Optional[Message] = None
    data: str
    chat_instance: Optional[str] = None


class WidgetActionPayload(BaseModel):
    """
    Structured payload decoded from widget interaction.
    """
    action: str
    tab: Optional[str] = None
    order_id: Optional[int] = None
    customer_id: Optional[int] = None
    status: Optional[str] = None
    filter: Optional[str] = None
    period: Optional[str] = None
    date: Optional[str] = None
    page: Optional[int] = 1
    query: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
