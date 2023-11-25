import nonebot
from openai import AsyncOpenAI
from nonebot.typing import T_State
from nonebot import on_command, logger, on_message
from nonebot.params import CommandArg
from nonebot.rule import to_me
from nonebot.rule import Rule
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent, MessageEvent
from .config import Config, ConfigError

# 配置导入
plugin_config = Config.parse_obj(nonebot.get_driver().config.dict())

if plugin_config.openai_http_proxy:
    proxy = {'http': plugin_config.openai_http_proxy, 'https': plugin_config.openai_http_proxy}
else:
    proxy = ""

if not plugin_config.openai_api_key:
    raise ConfigError("请设置 openai_api_key")

api_key = plugin_config.openai_api_key
model_id = plugin_config.openai_model_name
model_id_image = plugin_config.openai_model_image_name
max_limit = plugin_config.openai_max_history_limit
public = plugin_config.chatgpt_turbo_public
session = {}

async def is_at_in_group(bot: Bot, event: GroupMessageEvent) -> bool:
    if isinstance(event, GroupMessageEvent):
        return event.is_tome()  # 检查机器人是否被 @
    return False


# 带上下文的聊天
chat_record = on_command("chat", block=False, priority=1)
# 图片 
chat_image = on_message(rule=to_me(), block=False, priority=99)
chat_image_group = on_message(rule=Rule(is_at_in_group), block=False, priority=99)

# 清除历史记录
clear_request = on_command("clear", block=True, priority=1)


#小组图片处理
@chat_image_group.handle()
async def first_handle(bot: Bot, event: GroupMessageEvent, state: T_State):
    state["waiting_for_image"] = True  # 设置状态

@chat_image_group.got("next_message")
async def handle_next_message(bot: Bot, event: GroupMessageEvent, state: T_State):
    if state.get("waiting_for_image"):
        image_urls = []
        for segment in event.get_message():
            if segment.type == 'image':
                image_url = segment.data.get('url')  # 提取图片 URL
                if image_url:
                    image_urls.append(image_url)
        
        result = await get_res(image_urls)
        state["waiting_for_image"] = False  # 重置状态
        await chat_image_group.finish(result) 
    else:
        state["waiting_for_image"] = False
# 根据消息类型创建会话id
def create_session_id(event):
    if isinstance(event, PrivateMessageEvent):
        session_id = f"Private_{event.user_id}"
    elif public:
        session_id = event.get_session_id().replace(f"{event.user_id}", "Public")
    else:
        session_id = event.get_session_id()
    return session_id



# 带记忆的聊天
@chat_record.handle()
async def _(event: MessageEvent, msg: Message = CommandArg()):

    # 若未开启私聊模式则检测到私聊就结束
    if isinstance(event, PrivateMessageEvent) and not plugin_config.enable_private_chat:
        chat_record.finish("对不起，私聊暂不支持此功能。")

    # 检测是否填写 API key
    if api_key == "":
        await chat_record.finish(MessageSegment.text("请先配置openai_api_key"), at_sender=True)
    
    # 初始化会话id
    session_id = create_session_id(event)

    # 初始化保存空间
    if session_id not in session:
        session[session_id] = {"content": [], "count": 0}

    #logger.info("成功载入1")
    # 提取提问内容
    message_content = msg.extract_plain_text()
    if message_content.strip() == "":
       return  # 如果消息内容为空，直接返回而不进行后续处理
    # 更新会话实例的内容
    session[session_id]["content"].append({"role": "user", "content": message_content})
    #logger.info("成功载入2")
    # 更新计数
    session[session_id]["count"] += 1
    # 检查是否达到对话上限
    if session[session_id]["count"] >= max_limit:
        session[session_id]["content"] = []  # 清空聊天记录
        session[session_id]["count"] = 0     # 重置计数

    
    # 发送请求到 OpenAI
    client = AsyncOpenAI(api_key=api_key)
    try:
        res_ = await client.chat.completions.create(
            model=model_id,
            messages=session[session_id]["content"]
        )
        res = res_.choices[0].message.content
    except Exception as error:
        await chat_record.finish(str(error), at_sender=True)

    await chat_record.finish(MessageSegment.text(res), at_sender=True)

#图片处理个人
@chat_image.handle()
async def _(event: PrivateMessageEvent):
    image_urls = []  # 用于存储图片 URL

    # 检查消息中是否包含图片
    message = event.get_message()
    for segment in message:
        if segment.type == 'image':
            image_url = segment.data.get('url')  # 提取图片 URL
            if image_url:
                image_urls.append(image_url)
        # 使用 OpenAI API 处理图片
    
    result = await get_res(image_urls)
    await chat_image.finish(result)

    
@clear_request.handle()
async def _(event: MessageEvent):
    del session[create_session_id(event)]
    await clear_request.finish(MessageSegment.text("成功清除历史记录！"), at_sender=True)

async def get_res(image_urls):
    client = AsyncOpenAI(api_key=api_key)  # 确保替换为您的 API 密钥

    response = await client.chat.completions.create(
        model= model_id_image,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "这是什么，用中文回答?"},
                    {"type": "image_url", "image_url": {"url": image_urls[0]}},
                ],
            }
        ], max_tokens=1000,
    )
    result = response.choices[0].message.content
    return result
