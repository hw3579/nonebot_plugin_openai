仅仅是一个测试版 还有许多尚未整理的东西 后面整理好会好看很多 现在将就看看

更新于2023.11.25

从项目
https://github.com/Alpaca4610/nonebot_plugin_chatgpt_turbo
改进而来 
（你知道为什么改进！openai的api调用更新了原来的用不了了！！！）
约等于半个重写

简单写一下使用方法 

原来文档里面的.env环境变量修改如下

保持不变的：

    OPENAI_API_KEY = key
    OPENAI_MAX_HISTORY_LIMIT = 30   # 保留与每个用户的聊天记录条数
    ENABLE_PRIVATE_CHAT = True   # 私聊开关，默认开启，改为False关闭

有修改的：

    OPENAI_MODEL_NAME = "gpt-3.5-turbo" 
    -> 改成了openai_model_name: Optional[str] = "gpt-4-1106-preview"

新增加的：

    openai_model_image_name: Optional[str] = "gpt-4-vision-preview"

删除的：

    OPENAI_HTTP_PROXY = "http://127.0.0.1:8001"    
    # 请使用代理访问api，中国大陆/香港IP调用API有几率会被封禁  #当时为了调试方便去掉了代理部分


使用方法

1.删除了不带记忆的聊天（现在token价格下来了，当然不能失忆）

2.带记忆的触发命令依然是chat+词语

3.关于图片处理 私聊会直接解析图片
群聊需要在@之后 下一个消息发送图片

踩过的坑

openai官网的api手册没有异步调用！！！！！（原来的OpenAI.completions.acreate根本用不了）
我查他们的github源码之后才发现调用方法是

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=api_key)
    #注意后面编程需要加上async和await关键字