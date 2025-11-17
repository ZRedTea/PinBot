import nonebot
from nonebot.adapters.onebot.v11 import PokeNotifyEvent

from .config import Config

from nonebot import on_notice, on_message, logger
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Bot, Event, Message

import random

__plugin_meta__ = PluginMetadata(
    name="PinBot_funPlugin",
    description="拼好窝Bot的综合娱乐插件",
    usage="",
    config=Config,
)

GROUPID = 765024918

poke_reply = on_notice(priority=3,block=False)
ban_repeat = on_message(priority=1,block=False)

message_queue = []

@poke_reply.handle()
async def reply(event: PokeNotifyEvent):
    if event.sub_type == "poke" and event.target_id == event.self_id:
        logger.info("【拼Bot娱乐插件】触发器 | 触发->戳一戳 [poke_reply]")
        MESSAGES = []
        with open("REPLYS_WHEN_POKE.txt", "r", encoding="UTF-8") as f:
            for line in f.read().splitlines():
                if line != "":
                    MESSAGES.append(line)
            f.close()
        reply_msg = random.choice(MESSAGES)
        await poke_reply.finish(reply_msg)

@ban_repeat.handle()
async def ban(bot: Bot, event: Event):
    if event.group_id == GROUPID:
        message_queue.append(event.get_message())
        if len(message_queue) >= 3:
            last_message = message_queue[len(message_queue) - 1]
            times = 1
            while True:
                if message_queue[len(message_queue) - (times + 1)] == last_message:
                    times += 1
                else :
                    break
            if len(message_queue) >= 100:
                message_queue.clear()
            if times >= 3:
                num = random.randint(1,100)
                if num <= (times * times):
                    logger.info("【拼Bot娱乐插件】触发器 | 触发->复读禁言 [ban_repeat]")
                    duration = random.randint(1,times)
                    await bot.set_group_ban(group_id=event.group_id, user_id=event.user_id,duration=duration*60)
                    await ban_repeat.finish(f"恭喜幸运儿因复读喜提禁言{duration}分钟")
            else:
                await ban_repeat.finish()
