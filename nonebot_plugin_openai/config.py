from pydantic import Extra, BaseModel
from typing import Optional


class Config(BaseModel, extra=Extra.ignore):
    openai_api_key: Optional[str] = ""
    openai_model_name: Optional[str] = "gpt-4-1106-preview"
    openai_model_image_name: Optional[str] = "gpt-4-vision-preview"
    openai_max_history_limit: Optional[int] = 5
    openai_http_proxy: Optional[str] = None
    enable_private_chat: bool = True
    chatgpt_turbo_public: bool = False  # 群聊是否开启公共会话


class ConfigError(Exception):
    pass
