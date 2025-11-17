from .config import Config
from .model import User, PlayerStatus, serialize_player, deserialize_player
from .model import Machine, serialize_machine, deserialize_machine, search_machine

from nonebot import get_plugin_config, logger, require, get_bot
from nonebot.adapters.onebot.v11 import GroupIncreaseNoticeEvent, MessageSegment, Bot, Event, Message
from nonebot.plugin import PluginMetadata, on_command, on_notice
from nonebot.params import CommandArg
from nonebot.rule import to_me

from typing import List, Dict, Any
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import json
import os

__plugin_meta__ = PluginMetadata(
    name="PinBot_MainPlugin",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

VERSION = "Release 1.203.b"
R_TIME  = "2025.09.06 15:10"
R_TIPS  = f"""{VERSION} 更新公告
1.修复戳一戳功能
2.增加更多别名
————拼好窝BOT————"""

#############设置列表##############

time_format = "%Y-%m-%d %H:%M:%S"          #出勤退勤记录时长的时间格式
base_path = os.path.dirname(__file__)
save_path = os.path.join(base_path, "saves")
data_path = os.path.join(base_path, "datas")
cost_in_weekday = {
    "playing": 4,
    "waiting": 2,
    "threshold": 20
}
cost_in_weekend = {
    "playing" : 6,
    "waiting" : 3,
    "threshold" : 28
}
PLACENAME = "拼好窝"                       #音游窝名称
#ser = Serial("COM5", 9600, timeout=1)    #串口设置

ADMINS = [167047679,2655548416]
PERMISSION_GROUPS = { #权限组
    "SUPER_ADMIN" : [167047679,2655548416],
    "PERMISSION" : [167047679,2655548416],
}

GROUPID = 765024918

##################################

scheduler = require('nonebot_plugin_apscheduler').scheduler

def get_time(time1, time2):
    sec = int((time1 - time2).total_seconds())
    return sec // 60 + 1

def is_weekend() -> bool:
    """
    判断当前是否为周末

    Returns:
        bool: True - 周末, False - 周中
    """
    current_weekday = datetime.today().weekday()
    return current_weekday >= 5

def compute_real_cost(need_cost, had_cost, max_cost):
    if(need_cost + had_cost) >= max_cost:
        return max_cost - had_cost if max_cost - had_cost >= 0 else 0
    else:
        return need_cost

def compute_cost_and_time(player : User, current_time : datetime):
    """
    统一的计时计费函数

    Args:
        player: 玩家对象
        current_time: 当前时间

    Returns:
        dict: 包含时长，费用等信息
    """
    # 计费参数
    cost_param = cost_in_weekend if is_weekend() else cost_in_weekday

    # 获取用户开始时间和当前状态
    start_time = player.getStartTime()
    now_status = player.getStatus()

    # 计算游玩时长
    total_minutes = get_time(current_time, start_time)

    if now_status == PlayerStatus.WAITING:
        if total_minutes % 60 > 30:
            billing_hours = total_minutes // 60 + 1
        else:
            billing_hours = total_minutes // 60
    else:
        if total_minutes % 60 > 10:
            billing_hours = total_minutes // 60 + 1
        else:
            billing_hours = total_minutes // 60

    # 计算基础费用和实际费用
    need_cost = billing_hours * cost_param[now_status]
    real_cost = compute_real_cost(need_cost, player.getCost(), cost_param["threshold"])

    return {
        "total_minutes": total_minutes,   # 实际游玩时长
        "billing_hours": billing_hours,   # 计费游玩时长
        "base_cost": need_cost,           # 基础费用
        "real_cost": real_cost,           # 实际费用
        "rate": cost_param[now_status],   # 费率
    }

def sort_users_by_playing_time() -> Dict[int, User]:
    """
    按用户游戏时长降序排列用户

    Returns:
        dict: 排名索引 -> 用户对象的字典
    """
    sorted_users = sorted(
        users.values(),
        key=lambda user: user.getMins(),
        reverse=True
    )

    # 转换为排名字典
    sorted_users = {rank+1: user for rank, user in enumerate(sorted_users)}

    return sorted_users


def Authorized(id : int, need_permission : str, permission_groups : Dict[str, Any]) -> bool:
    """判断某id是否有权限进行操作
    input:
    id : 要判断的用户id(QQ号)
    need_permission : 要判断的权限类型

    return:
    有权限 True
    无权限 False"""
    if id in permission_groups["SUPER_ADMIN"]:
        return True

    if id in permission_groups[need_permission]:
        return True

    return False

###BOT命令###
bot_version   = on_command("版本信息",rule=to_me(), aliases={"查询版本"})
bot_versiontip= on_command("更新公告",rule=to_me(), aliases={"版本公告","更新日志","版本日志"})

###个人命令###
user_help     = on_command("帮助", rule=to_me(), aliases={"help"})
user_register = on_command("注册", rule=to_me(), aliases={"创建账号"})
user_ranklist = on_command("排行", rule=to_me())
user_info     = on_command("我的", rule=to_me(), aliases={"查询","info"})
user_rename   = on_command("改名", rule=to_me())

###机台命令###
machine_info  = on_command("所有机台", rule=to_me())
machine_search= on_command("查询机台", rule=to_me())
put_card      = on_command("开始排卡", rule=to_me(), aliases={"kspk","排卡"})
pop_card      = on_command("退出排卡", rule=to_me(), aliases={"tcpk","退卡"})
check_card    = on_command("查询排卡", rule=to_me(), aliases={"查卡","几卡"})
next_card     = on_command("结束游玩", rule=to_me())

###窝内命令###
check_place    = on_command("场况", rule=to_me(), aliases={"phwj","几个人"})
start_waitting = on_command("入场", rule=to_me())
start_shukkin  = on_command("出勤", rule=to_me())
stop_shukkin   = on_command("退场", rule=to_me(), aliases={"退勤"})
open_door      = on_command("开门", rule=to_me(), aliases={"km"}) ###废案###

###权限命令###
permission_arrearage_check = on_command("欠款查询", rule=to_me())

###管理命令###
admin_initialize = on_command("初始化主插件", rule=to_me())
admin_addbalance = on_command("增加余额", rule=to_me(), aliases={"添加余额","充值余额"})
admin_setbalance = on_command("设置余额", rule=to_me(), aliases={"更改余额"})
admin_dowSave    = on_command("保存存档", rule=to_me())
admin_getSave    = on_command("读取存档", rule=to_me(), aliases={"恢复存档","载入存档","加载存档"})
admin_stop_nocost= on_command("管理无花费退勤", rule=to_me())
admin_stop_withcost = on_command("管理有花费退勤", rule=to_me())
admin_start      = on_command("管理出勤", rule=to_me())
admin_setCost    = on_command("管理消费", rule=to_me())

admin_ban        = on_command("封禁", rule=to_me())
admin_unban      = on_command("解封", rule=to_me())

#机台#
admin_machine_on = on_command("开启机台", rule=to_me())
admin_machine_off= on_command("关闭机台", rule=to_me())

###功能性命令###
auto_welcome     = on_notice()

users = {}      #用户字典 Dict[user_id, user]
machines = []   #机台列表

################################################
##################定时任务########################
################################################



@scheduler.scheduled_job(CronTrigger.from_crontab("0 8 * * *"))
async def autosave():
    bot = get_bot()
    logger.info(f"【拼Bot核心插件】自动化 | 触发->每日清场[daily_clear]")
    logger.info(f"【拼Bot核心插件】自动化 | daily_clear > 开始自动退勤所有人")
    for user in users.values():
        if user.is_online():
            result = compute_cost_and_time(user, datetime.now())

            user.allTimeAdd =
            logger.info(f"【拼Bot核心插件】自动化 | daily_clear > 已退勤 {user.getNickname()}")
        user.costClear()

    serialized_users = {qq: serialize_player(player) for qq, player in users.items()}
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"autosave_{today}.sav"
        filepath = os.path.join(save_path, filename)
        with open(filepath, "w", encoding="UTF-8") as f:
            json.dump(serialized_users, f, ensure_ascii=False, indent=4)
        logger.info(f"【拼Bot核心插件】自动化 | daily_clear > 自动存档数据已保存至于 {filename}")
        await bot.send_group_msg(group_id=GROUPID,message=f"【自动保存】数据已保存至 {filename}")
    except Exception as e:
        await bot.send_group_msg(group_id=GROUPID,message=f"【自动保存】保存时发生错误:{e}")

@scheduler.scheduled_job(CronTrigger.from_crontab("0 * * * *"))
async def autoreminder():
    bot = get_bot()
    logger.info(f"【拼Bot核心插件】自动化 | 触发->整点播报[hourly_check]")
    if not (int(datetime.now().strftime("%H")) <= 8 or int(datetime.now().strftime("%H")) > 22):
        num = 0
        for user in users.values():
            if user.getStatus():
                num += 1
        await bot.send_group_msg(group_id=GROUPID,message=f"【整点播报】{datetime.now().strftime('%H')}时拼好窝内人数为{num}")

@auto_welcome.handle()
async def handle_group_increase(event: GroupIncreaseNoticeEvent):
    logger.info("【拼Bot核心插件】触发器 | 触发->自动欢迎功能 [auto_welcome]")
    if event.notice_type == "group_increase":
        user_id = int(event.user_id)
        group_id = int(event.group_id)

        if group_id == GROUPID:
            message = Message([
                MessageSegment.text("————自动欢迎————\n"),
                MessageSegment.text("欢迎 "),
                MessageSegment.at(user_id),
                MessageSegment.text(" 加入拼好窝玩家交流群！\n"),
                MessageSegment.text("新人请查看 群文件-管理细则 文件夹中的管理细则文件\n"),
                MessageSegment.text("有不懂的问题可以询问管理员\n"),
                MessageSegment.text("————拼好窝BOT————")
            ])
            await auto_welcome.finish(message)

################################################
##################BOT部分########################
################################################



@bot_version.handle()
async def _(bot: Bot, event: Event):
    logger.info("【拼Bot核心插件】指令器 | 触发->版本信息 [bot_version]")
    message = "————版本信息————\n"
    message += f"目前版本: {VERSION}\n"
    message += f"更新时间: {R_TIME}\n"
    message += "————拼好窝BOT————"
    await bot_version.finish(message)

@bot_versiontip.handle()
async def _(bot: Bot, event: Event):
    logger.info("【拼Bot核心插件】指令器 | 触发->更新公告 [bot_versiontip]")
    await bot_versiontip.finish(R_TIPS)


################################################
##################个人部分########################
################################################



@user_help.handle()
async def _(bot: Bot, event: Event):
    logger.info("【拼Bot核心插件】指令器 | 触发->用户帮助 [user_help]")
    await user_help.send("""————指令菜单————
///个人相关///
创建账号: /注册 [昵称]
查询信息: /我的 或 /查询 [id]
时长排行: /排行
修改昵称: /改名 [昵称]

///出勤相关///
查询场况: /场况
入场退场: /入场 & /退勤
游玩机台: /出勤

///排卡相关///
进行排卡: /开始排卡 [机台名]
离开排卡: /退出排卡 [机台名]
下名玩家: /结束游玩 [机台名]
排卡人数: /查询排卡 [机台名]

///机台相关///
查看所有: /所有机台
查询机台: /查询机台 [机台名]
————拼好窝BOT————""")
    await user_help.finish()

@user_info.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发->用户信息 [user_info]")
    if user_id := args.extract_plain_text():
        user_id = int(user_id)
    else:
        user_id = int(event.get_user_id())

    if(user_id not in users):
        await user_info.finish(f"{user_id} 尚未注册")

    thisUser = users[user_id]
    await user_info.send(f"""————个人信息————
用户编号:{user_id}
用户昵称:{thisUser.getNickname()}
用户状态:{("正在出勤" if thisUser.getType() == 1 else "在场等待") if thisUser.getStatus() else "退勤"} {f"\n开始时间:{thisUser.getStartTime()}" if thisUser.getStatus() else ""}
用户余额:{thisUser.getBalance()} 元
今日消费:{thisUser.getCost()[0]}元
游玩时长:{thisUser.getDay()}天{thisUser.getHour()}小时{thisUser.getMin()}分钟
————拼好窝BOT————""")
    await user_info.finish()

@user_ranklist.handle()
async def _(bot: Bot, event: Event):
    logger.info("【拼Bot核心插件】指令器 | 触发->用户排行 [user_ranklist]")
    sorted_users = sort_users_by_playing_time()
    count = 0
    message = ""
    for id in sorted_users:
        user = sorted_users[id]
        count += 1
        message += f"{count}. {user.getNickname()} : {user.getDay()}天{user.getHour()}小时{user.getMin()}分钟\n"
        if count % 10 == 0:
            break

    await user_ranklist.finish(message)

@user_register.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发->用户注册 [user_register]")
    user_id = int(event.get_user_id())

    if nickname := args.extract_plain_text():
        pass
    else:
        nickname = f"{PLACENAME}用户{len(users) + 1}"
    users[user_id] = User(nickname, user_id)
    logger.debug(users)
    logger.info(f"【拼Bot核心插件】指令器 | user_register > 用户{user_id} 创建账号完毕")
    await user_register.finish(f"创建账号成功，玩家 {user_id} 的昵称为 {users[user_id].getNickname()}")

@user_rename.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info(f"【拼Bot核心插件】指令器 | 触发->用户改名 [user_rename]")
    user_id = int(event.get_user_id())
    if nickname := args.extract_plain_text():
        pass
    else:
        await user_rename.finish("请输入新昵称")

    if user_id not in users:
        await user_rename.finish(f"{user_id} 尚未注册")

    users[user_id].changeName(nickname)
    await user_rename.finish(f"{user_id} 的昵称已改为 {users[user_id].getNickname()}")



################################################
##################机台部分########################
################################################



@machine_info.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info(f"【拼Bot核心插件】指令器 | 触发->所有机台 [machine_info]")
    info = "————所有机台————\n"
    for machine in machines:
        info += f"{machine.getName()}[{machine.getType()}] —— {"良好" if machine.getStatu() else "维护中"}\n"
    info += "————拼好窝BOT————"
    await machine_info.finish(info)

@machine_search.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info(f"【拼Bot核心插件】指令器 | 触发->查询机台 [machine_search]")
    args = args.extract_plain_text().split()
    if(len(args) != 1):
        await machine_search.finish("请按照 >> 查询机台 [机台名] << 的格式输入")

    search_name = args[0]
    searched_machines = []
    for machine in machines:
        if search_name in machine.getName():
            searched_machines.append(machine)

    if len(searched_machines) == 0:
        await machine_search.finish("未找到该名称的机台")
    elif len(searched_machines) == 1:
        machine = searched_machines[0]
        info = "————机台信息————\n"
        info += f"机台名:{machine.getName()}\n"
        info += f"类型: {machine.getType()}\n"
        info += f"状态: {"良好" if machine.getStatu() else "维护中"}\n"
        info += f"描述: {machine.getDescription()}\n"
        info += f"————拼好窝BOT————"
        await machine_search.finish(info)
    else:
        await machine_search.finish("有多台同名机台")

@put_card.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发->开始排卡 [put_card]")
    args = args.extract_plain_text().split()
    user_id = int(event.get_user_id())
    if(len(args) != 1):
        await put_card.finish("请按照 >> 开始排卡 [机台名] << 的格式输入")
    if(not users[user_id].getStatus()):
        await put_card.finish("您尚未入场")

    machine_name = args[0]
    index = search_machine(machines,machine_name)
    if(index == -1):
        await put_card.finish(f"未找到该机台")
    else:
        thisMachine = machines[index]
        if user_id in thisMachine.getCards():
            await put_card.finish(f"{users[user_id].getNickname()} 已在 {machine_name} 上排卡\n目前第 {thisMachine.getCardsNo(user_id)} 位")
        thisMachine.putCard(user_id)
        await put_card.finish(f"{users[user_id].getNickname()} 开始在 {machine_name} 上排卡\n目前第 {len(thisMachine.getCards())} 位")

@pop_card.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发->退出排卡 [pop_card]")
    args = args.extract_plain_text().split()
    user_id = int(event.get_user_id())
    if(len(args) != 1):
        await pop_card.finish("请按照 >> 退出排卡 [机台名] << 的格式输入")

    machine_name = args[0]
    index = search_machine(machines, machine_name)
    if (index == -1):
        await pop_card.finish(f"未找到该机台")
    else:
        thisMachine = machines[index]
        if user_id not in thisMachine.getCards():
            await pop_card.finish(f"{users[user_id].getNickname()} 尚未在 {machine_name} 上排卡")
        thisMachine.popCard(user_id)
        await pop_card.finish(f"{users[user_id].getNickname()} 已退出 {machine_name} 的排卡")

@next_card.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发->结束游玩 [next_card]")
    args = args.extract_plain_text().split()
    user_id = int(event.get_user_id())
    if(len(args) != 1):
        await next_card.finish("请按照 >> 结束游玩 [机台名] << 的格式输入")
    machine_name = args[0]
    index = search_machine(machines, machine_name)
    if (index == -1):
        await next_card.finish("未找到该机台")
    else:
        thisMachine = machines[index]
        firstPlayer = thisMachine.getCards()[0]
        if(user_id != firstPlayer):
            await next_card.finish(f"您没有在游玩该机台，当前游玩玩家为 {users[firstPlayer].getInfo()}")
        else:
            thisMachine.nextCard()
            nowPlayer = thisMachine.getCards()[0]
            message = Message([
                MessageSegment.text("到 "),
                MessageSegment.at(nowPlayer),
                MessageSegment.text(f" 游玩 {thisMachine.getName()} 了！"),
            ])
            await next_card.finish(message)

@check_card.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发->查询排卡 [check_card]")
    args = args.extract_plain_text().split()
    user_id = int(event.get_user_id())
    if(len(args) != 1):
        await check_card.finish("请按照 >> 查询排卡 [机台名] << 的格式输入")

    machine_name = args[0]
    index = search_machine(machines, machine_name)
    if (index == -1):
        await check_card.finish("未找到该机台")
    else:
        thisMachine = machines[index]
        Cards = thisMachine.getCards()
        if len(Cards) == 0:
            await check_card.finish("该机台没有人排卡")
        message = f"————{thisMachine.getName()}排卡板————\n"
        message += f"[正在游玩]: {users[Cards[0]].getInfo()}\n"
        if len(Cards) > 1:
            count = 1
            message += "[正在排卡]\n"
            for id in Cards[1:]:
                message += f"{count}. {users[id].getInfo()}\n"
                count += 1
        else:
            message += "[正在排卡]\n无\n"
        message += f"————拼好窝BOT————"
        await check_card.finish(message)


################################################
##################出勤部分########################
################################################



@start_shukkin.handle()
async def _(bot: Bot, event: Event):
    logger.info("【拼Bot核心插件】指令器 | 触发->用户出勤 [start_shukkin]")
    user_id = int(event.get_user_id())
    time = datetime.now().strftime(time_format)
    time = datetime.strptime(time, time_format)
    if user_id not in users:
        await start_shukkin.finish(f"您尚未注册，请先发送 >> 注册 [用户名] << 注册账户")

    thisUser = users[user_id]

    if thisUser.isBanned():
        await start_shukkin.finish(f"出勤失败，{thisUser.getInfo()} 已被封禁")
    if thisUser.getBalance() < -10:
        await start_shukkin.finish(f"出勤失败，{thisUser.getInfo()} 欠费超过10元")

    if not thisUser.getStatus():
        thisUser.typeShukkin()
        thisUser.online()
        thisUser.setStartTime(time)
        await start_shukkin.finish(f"请不要大力拍打或滑动哦\n出勤成功，{thisUser.getInfo()} 于 {time} 开始出勤")
    else:
        if thisUser.getType() == 2:
            duration = get_time(time, users[user_id].getStartTime())
            thisUser.allTimeAdd(duration)
            if (duration % 60 > 10):
                duration = duration // 60 + 1
            else:
                duration = duration // 60
            needReduce = duration * COSTPERTIME[2]
            realReduce = compute_real_cost(needReduce, thisUser.getCost()[0], 15)
            if duration <= 30:
                realReduce = 0
            thisUser.balanceReduce(realReduce)
            thisUser.costAdd(0, realReduce)
            thisUser.typeShukkin()
            thisUser.setStartTime(time)
            await start_shukkin.finish(f"已将 {thisUser.getNickname()}[{user_id}] 从等待转换为出勤，今日已消费 {thisUser.getCost()[0]} 元，剩余 {thisUser.getBalance()} 元")
        else:
            await start_shukkin.finish(f"出勤失败，{thisUser.getNickname()}[{user_id}] 已于 {thisUser.getStartTime()} 开始出勤")


@start_waitting.handle()
async def _(bot: Bot, event: Event):
    logger.info("【拼Bot核心插件】指令器 | 触发->用户入场 [start_waitting]")

    user_id = int(event.get_user_id())
    time = datetime.now().strftime(time_format)
    time = datetime.strptime(time, time_format)
    if user_id not in users:
        await start_waitting.finish(f"您尚未注册，请先创建账号")

    thisUser = users[user_id]

    if thisUser.isBanned():
        await start_waitting.finish(f"入场失败，{thisUser.getInfo()} 已被封禁")
    if thisUser.getBalance() < -10:
        await start_waitting.finish(f"入场失败，{thisUser.getInfo()} 欠费超过10元")

    if not thisUser.getStatus():
        # flag = 0
        # for user in users.values():
        #     if(user.getStatus() and user.getType() == 1):
        #         flag = 1

        thisUser.typeWaiting()
        thisUser.online()
        thisUser.setStartTime(time)
        await start_waitting.finish(f"如果要游玩机台请发送 出勤 来出勤哦\n入场成功，{thisUser.getNickname()}[{user_id}] 于 {time} 入场")
    else:
        if thisUser.getType() == 2:
            await start_waitting.finish(f"入场失败， {thisUser.getNickname()}[{user_id}] 已于 {thisUser.getStartTime()} 入场")
        else:
            await start_waitting.finish(f"出勤后不能再改回等待状态")

@stop_shukkin.handle()
async def _(bot: Bot, event: Event):
    logger.info("【拼Bot核心插件】指令器 | 触发->用户退场 [stop_shukkin]")
    user_id = int(event.get_user_id())
    time = datetime.now()
    logger.debug(type(time))
    if user_id not in users:
        await stop_shukkin.finish(f"您尚未注册，请先创建账号")

    thisUser = users[user_id]

    if thisUser.getStatus():
        thisUser.offline()
        duration = get_time(time, users[user_id].getStartTime())
        thisUser.allTimeAdd(duration)
        if(duration % 60 > 10):
            duration = duration // 60 + 1
        else:
            duration = duration // 60

        if thisUser.getType() == 1:
            needReduce = duration * COSTPERTIME[1]
            realReduce = compute_real_cost(needReduce, thisUser.getCost()[0], 36)
            thisUser.balanceReduce(realReduce)
            thisUser.costAdd(0,realReduce)
        else:
            needReduce = duration * COSTPERTIME[2]
            realReduce = compute_real_cost(needReduce, thisUser.getCost()[0], 24)
            thisUser.balanceReduce(realReduce)
            thisUser.costAdd(0,realReduce)
        for machine in machines:
            if user_id in machine.getCards():
                machine.popCard(user_id)
        await stop_shukkin.finish(
            f"请带好随身物品，当心自动拾取\n{thisUser.getNickname()}[{user_id}] 今日消费 {thisUser.getCost()[0]} 元，余额 {thisUser.getBalance()} 元")
    else:
        await stop_shukkin.finish(f"{thisUser.getNickname()}[{user_id}] 还没入场呢")

@open_door.handle()
async def _(bot: Bot, event: Event):
    logger.info("【拼Bot核心插件】触发 [open_door]")
    user_id = int(event.get_user_id())
    time = datetime.now()
    if user_id not in users:
        await open_door.finish(f"您尚未注册，请先创建账号")

    thisUser = users[user_id]
    if (thisUser.getStatus()):
        #ser.write(b"open\n")
        await open_door.finish(f"门已打开，记得随手关门哦")
    else:
        await open_door.finish(f"您还没出勤呢，先发送 出勤 来出勤吧")

@check_place.handle()
async def _(bot: Bot, event: Event):
    logger.info("【拼Bot核心插件】指令器 | 触发->查询场况[check_place]")
    num = 0
    num_shukkin = 0
    num_waiting = 0
    message = "————玩家列表————\n"
    waiting = "[在场等待]\n"
    shukkin = "[正在出勤]\n"
    for user in users.values():
        if user.getStatus():
            if user.getType() == 1:
                shukkin += f"{num_shukkin+1}. {user.getNickname()}[{user.getUserid()}]\n"
                num_shukkin += 1
            else:
                waiting += f"{num_waiting+1}. {user.getNickname()}[{user.getUserid()}]\n"
                num_waiting += 1
    if num_waiting == 0:
        waiting += "无\n"
    if num_shukkin == 0:
        shukkin += "无\n"
    message += waiting + shukkin
    num = num_shukkin + num_waiting
    message += f"当前拼好窝内人数为: {num}\n"
    message += "————拼好窝BOT————"

    if(num == 0):
        await check_place.finish("当前拼好窝内没有人")
    await check_place.finish(message)



##############################################
##################权限命令######################
##############################################

@permission_arrearage_check.handle()
async def _(bot: Bot, event: Event):
    logger.info("【拼Bot核心插件】指令器 | 触发权限级->欠费查询 [permission_arrearage_check]")
    check_id = int(event.get_user_id())
    if not Authorized(check_id, "PERMISSION"):
        logger.info("【拼Bot核心插件】指令器 | permission_arrearage_check > 权限检验失败")
        await permission_arrearage_check.finish(f"无权限")
    logger.info("【拼Bot核心插件】指令器 | permission_arrearage_check > 权限检验通过")
    num = 0
    message = "————欠费列表————\n"
    for user in users.values():
        if user.getBalance() < 0:
            num += 1
            message += f"{num}.{user.getInfo()} 欠费: {0-user.getBalance()}元\n "
    if num == 0:
        message += f"无人欠费\n"
    message += "————拼好窝Bot————"
    await permission_arrearage_check.finish(message)



##############################################
##################管理命令######################
##############################################



@admin_initialize.handle()
async def _(bot: Bot, event: Event):
    logger.info("【拼Bot核心插件】初始化 | 准备初始化数据")
    admin_id = int(event.get_user_id())
    # if admin_id not in ADMINS:
    #     admin_initialize.finish(f"{admin_id} 非管理员用户")

    if not Authorized(admin_id,"SUPER_ADMIN"):
        await admin_initialize.finish(f"无权限")

    global machines
    try:
        filepath = os.path.join(data_path, "machines.json")
        with open(filepath, "r", encoding="utf-8") as f:
            datas = json.load(f)
            machines = [deserialize_machine(data) for data in datas]

        ###加载模块###
        logger.info("【拼Bot核心插件】初始化 | 正在加载存档")
        save_files = [f for f in os.listdir(save_path) if f.startswith("maimai") and f.endswith(".sav")]
        if not save_files:
            await admin_initialize.send(f"未找到任何存档，将不加载存档初始化BOT")
            logger.error("【拼Bot核心插件】初始化 | 未找到存档")
        else:
            filename = max(save_files, key=lambda f: datetime.strptime(f[7:-4], "%Y-%m-%d"))
            filepath = os.path.join(save_path, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                serialized_users = json.load(f)
            global users
            users = {int(qq): deserialize_player(data) for qq, data in serialized_users.items()}
            logger.debug(users)
            await admin_initialize.send(f"已加载存档 {filename}")
            logger.info(f"【拼Bot核心插件】初始化 | 已加载存档 {filename}")
    except Exception as e:
        logger.error(f"【拼Bot核心插件】初始化 | 发生错误: {e} \n {e.args}")
        await admin_initialize.finish(f"初始化过程中发生错误:{e}")
    logger.info("【拼Bot核心插件】初始化 | 数据初始化完毕")
    await admin_initialize.finish("BOT已初始化完成")

@admin_addbalance.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发管理级->增加余额 [admin_addbalance]")
    check_id = int(event.get_user_id())

    if not Authorized(check_id,"SUPER_ADMIN"):
        logger.info("【拼Bot核心插件】指令器 | admin_addbalance > 权限检验失败")
        await admin_addbalance.finish("无权限")

    logger.info("【拼Bot核心插件】指令器 | admin_addbalance > 权限检验成功")
    admin_id = check_id
    args = args.extract_plain_text().strip().split()
    if(len(args) != 2):
        await admin_addbalance.finish("请按照 >> 增加余额 [QQ号] [金额] << 的格式输入")
    user_id, money = args
    user_id = int(user_id)
    if(user_id not in users):
        await admin_addbalance.finish(f"{user_id} 尚未注册")

    thisUser = users[user_id]
    thisUser.balanceRechar(int(money))
    await admin_addbalance.finish(f"已为 {thisUser.getNickname()}[{user_id}] 添加 {money} 元余额")

@admin_setbalance.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发管理级->设置余额 [admin_setbalance]")
    check_id = int(event.get_user_id())

    if not Authorized(check_id,"SUPER_ADMIN"):
        logger.info("【拼Bot核心插件】指令器 | admin_setbalance > 权限检验失败")
        await admin_setbalance.finish("无权限")

    logger.info("【拼Bot核心插件】指令器 | admin_setbalance > 权限检验成功")
    admin_id = check_id

    args = args.extract_plain_text().strip().split()
    if(len(args) != 2):
        await admin_setbalance.finish("请按照 >> 设置余额 [QQ号] [金额] << 的格式输入")
    user_id, money = args
    user_id = int(user_id)
    if(user_id not in users):
        await admin_setbalance.finish(f"{user_id} 尚未注册")

    # if(admin_id not in ADMINS):
    #     await admin_setbalance.finish(f"{admin_id} 非管理员用户")

    thisUser = users[user_id]
    thisUser.balanceSet(int(money))
    await admin_setbalance.finish(f"已将 {thisUser.getNickname()}[{user_id}] 的余额设置为 {money} 元")

@admin_stop_nocost.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发管理级->管理无花费退勤 [admin_stop_nocost]")
    check_id = int(event.get_user_id())

    if not Authorized(check_id,"SUPER_ADMIN"):
        logger.info("【拼Bot核心插件】指令器 | admin_stop_nocost > 权限检验失败")
        await admin_stop_nocost.finish("无权限")

    logger.info("【拼Bot核心插件】指令器 | admin_stop_nocost > 权限检验成功")
    admin_id = check_id

    args = args.extract_plain_text().strip()
    if len(args) != 1:
        await admin_stop_nocost.finish("请按照 >> 管理无费退勤 [QQ号] << 的格式输入")

    user_id = int(args[0])
    if user_id not in users:
        await admin_stop_nocost.finish(f"{user_id} 尚未注册")

    thisUser = users[user_id]
    if users[user_id].getStatus():
        users[user_id].offline()
        for machine in machines:
            if user_id in machine.getCards():
                machine.popCard(user_id)
        await admin_stop_nocost.finish(f"已将 {thisUser.getInfo()} 退勤")
    else:
        await admin_stop_nocost.finish(f"{thisUser.getInfo()} 尚未入场")

@admin_stop_withcost.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发管理级->管理有花费退勤 [admin_stop_withcost]")
    check_id = int(event.get_user_id())

    if not Authorized(check_id,"SUPER_ADMIN"):
        logger.info("【拼Bot核心插件】指令器 | admin_stop_withcost > 权限检验失败")
        await admin_stop_withcost.finish(f"无权限")

    logger.info("【拼Bot核心插件】指令器 | admin_stop_withcost > 权限检验成功")
    admin_id = check_id

    args = args.extract_plain_text().strip()
    if len(args) != 1:
        await admin_stop_withcost.finish(f"请按照 >> 管理有费退勤 [QQ号] << 的格式输入")

    user_id = int(args[0])
    if user_id not in users:
        await admin_stop_withcost.finish(f"{user_id} 尚未注册")

    thisUser = users[user_id]
    time = datetime.now()
    if thisUser.getStatus():
        thisUser.offline()
        duration = get_time(time, users[user_id].getStartTime())
        thisUser.allTimeAdd(duration)
        if(duration % 60 > 10):
            duration = duration // 60 + 1
        else:
            duration = duration // 60

        if thisUser.getType() == 1:
            needReduce = duration * COSTPERTIME[1]
            realReduce = compute_real_cost(needReduce, thisUser.getCost()[0], 35)
            thisUser.balanceReduce(realReduce)
            thisUser.costAdd(0,realReduce)
        else:
            needReduce = duration * COSTPERTIME[2]
            realReduce = compute_real_cost(needReduce, thisUser.getCost()[0], 24)
            thisUser.balanceReduce(realReduce)
            thisUser.costAdd(0,realReduce)
        for machine in machines:
            if user_id in machine.getCards():
                machine.popCard(user_id)
        await stop_shukkin.finish(f"已将 {thisUser.getInfo()} 退勤，该用户本次花费 {realReduce} 元，日总消费 {thisUser.getCost()[0]} 元")
    else:
        await stop_shukkin.finish(f"{thisUser.getInfo()} 尚未入场")

@admin_start.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发管理级->管理出勤 [admin_start]")
    check_id = int(event.get_user_id())

    if not Authorized(check_id,"SUPER_ADMIN"):
        logger.info("【拼Bot核心插件】指令器 | admin_start > 权限检验失败")
        await admin_start.finish("无权限")

    logger.info("【拼Bot核心插件】指令器 | admin_start > 权限检验成功")
    admin_id = check_id

    args = args.extract_plain_text().strip().split()
    if len(args) != 1:
        await admin_start.finish("请按照 >> 管理出勤 [QQ号] << 的格式输入")
    user_id = int(args[0])
    thisUser = users[user_id]
    if thisUser.getStatus():
        await admin_start.finish(f"{user_id} 已经在出勤了")
    else:
        time = datetime.now().strftime(time_format)
        time = datetime.strptime(time, time_format)
        users[user_id].setStartTime(time)
        thisUser.online()
        await admin_start.finish(f"已将 {thisUser.getNickname()}[{user_id}] 设置为出勤状态")

@admin_setCost.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发管理级->管理消费 [admin_setCost]")
    check_id = int(event.get_user_id())

    if not Authorized(check_id,"SUPER_ADMIN"):
        logger.info("【拼Bot核心插件】指令器 | admin_setCost > 权限检验失败")
        await admin_setCost.finish("无权限")

    logger.info("【拼Bot核心插件】指令器 | admin_setCost > 权限检验成功")
    admin_id = check_id

    args = args.extract_plain_text().strip().split()
    if len(args) != 2:
        await admin_setCost.finish("请按照 >> 管理消费 [QQ号] [消费额] << 的格式输入")
    user_id = int(args[0])
    money = int(args[1])
    thisUser = users[user_id]
    thisUser.costSet(0,money)
    await admin_setCost.finish(f"已将 {thisUser.getNickname()}[{user_id}] 今日总消费设置为 {money} 元")

@admin_ban.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发管理级->封禁用户 [admin_ban]")
    check_id = int(event.get_user_id())

    if not Authorized(check_id,"SUPER_ADMIN"):
        logger.info("【拼Bot核心插件】指令器 | admin_ban > 权限检验失败")
        await admin_ban.finish(f"无权限")

    logger.info("【拼Bot核心插件】指令器 | admin_ban > 权限检验成功")
    admin_id = check_id

    args = args.extract_plain_text().strip().split()
    if len(args) != 1:
        await admin_ban.finish("请按照 >> 封禁 [QQ号] << 的格式输入")
    user_id = int(args[0])
    thisUser = users[user_id]
    thisUser.ban()
    await admin_ban.finish(f"已将 {thisUser.getInfo()} 封禁")

@admin_unban.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 ｜ 触发管理级->解封用户 [admin_unban]")
    check_id = int(event.get_user_id())

    if not Authorized(check_id,"SUPER_ADMIN"):
        logger.info("【拼Bot核心插件】指令器 | admin_unban > 权限检验失败")
        await admin_unban.finish("无权限")

    logger.info("【拼Bot核心插件】指令器 | admin_unban > 权限检验成功")
    admin_id = check_id

    args = args.extract_plain_text().strip().split()
    if len(args) != 1:
        await admin_unban.finish("请按照 >> 解封 [QQ号] << 的格式输入")
    user_id = int(args[0])
    thisUser = users[user_id]
    thisUser.unban()
    await admin_unban.finish(f"已将 {thisUser.getInfo()} 解封")

#####管理命令 - 机台部分#####

@admin_machine_on.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发管理级->开启机台 [admin_machine_on]")
    check_id = int(event.get_user_id())

    if not Authorized(check_id,"SUPER_ADMIN"):
        logger.info("【拼Bot核心插件】指令器 | admin_machine_on > 权限检验失败")
        await admin_machine_on.finish(f"无权限")

    logger.info("【拼Bot核心插件】指令器 | admin_machine_on > 权限检验成功")
    admin_id = check_id

    args = args.extract_plain_text().strip().split()
    if len(args) != 1:
        await admin_machine_on.finish(f"请按照 >> 开启机台 [机台名] << 的格式输入")
    machine_name = args[0]
    index = search_machine(machines, machine_name)
    if (index == -1):
        await admin_machine_on.finish("未找到该机台")
    else:
        thisMachine = machines[index]
        thisMachine.onMachine()
        await admin_machine_on.finish(f"已开启机台 {thisMachine.getName()}")

@admin_machine_off.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发管理级->关闭机台 [admin_machine_off]")
    check_id = int(event.get_user_id())

    if not Authorized(check_id,"SUPER_ADMIN"):
        logger.info("【拼Bot核心插件】指令器 | admin_machine_off > 权限检验失败")
        await admin_machine_off.finish(f"无权限")

    logger.info("【拼Bot核心插件】指令器 | admin_machine_off > 权限检验成功")
    admin_id = check_id

    args = args.extract_plain_text().strip().split()
    if len(args) != 1:
        await admin_machine_off.finish(f"请按照 >> 关闭机台 [机台名] << 的格式输入")
    machine_name = args[0]
    index = search_machine(machines, machine_name)
    if (index == -1):
        await admin_machine_off.finish("未找到该机台")
    else:
        thisMachine = machines[index]
        thisMachine.offMachine()
        await admin_machine_off.finish(f"已关闭机台 {thisMachine.getName()}")

#####管理命令-存档部分#####

#卧槽这坨屎是我写的？
@admin_dowSave.handle()
async def _(bot: Bot, event: Event):
    logger.info("【拼Bot核心插件】指令器 | 触发管理级->保存存档 [admin_dowSave]")
    check_id = int(event.get_user_id())

    if not Authorized(check_id,"SUPER_ADMIN"):
        logger.info("【拼Bot核心插件】指令器 | admin_dowSave > 权限检验失败")
        await admin_dowSave.finish(f"无权限")

    logger.info("【拼Bot核心插件】指令器 | admin_dowSave > 权限检验成功")
    admin_id = check_id

    filename = f"maimai_{datetime.now().strftime("%Y-%m-%d")}.sav"
    try:
        serialized_users = {qq: serialize_player(player) for qq, player in users.items()}
        filepath = os.path.join(save_path, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(serialized_users, f, ensure_ascii=False, indent=4)
    except Exception as e:
        await admin_dowSave.finish(f"保存时发生错误:{e}")

    await admin_dowSave.finish(f"数据已保存至 {filename}")

#卧槽，屎
@admin_getSave.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    logger.info("【拼Bot核心插件】指令器 | 触发管理级->读取存档 [admin_getSave]")
    check_id = int(event.get_user_id())

    if not Authorized(check_id,"SUPER_ADMIN"):
        logger.info("【拼Bot核心插件】指令器 | admin_getSave > 权限检验失败")
        await admin_getSave.finish(f"无权限")

    logger.info("【拼Bot核心插件】指令器 | admin_getSave > 权限检验成功")
    admin_id = check_id

    if filename := args.extract_plain_text():
        pass
    else:
        autosave_files = [f for f in os.listdir(save_path) if f.startswith("autosave") and f.endswith(".sav")]
        save_files = [f for f in os.listdir(save_path) if f.startswith("maimai") and f.endswith(".sav")]
        if not save_files:
            await admin_getSave.finish(f"未找到存档")

        max_in_savefile = max(save_files,key=lambda f: datetime.strptime(f[7:-4],"%Y-%m-%d"))
        max_in_autosave = max(autosave_files,key=lambda f: datetime.strptime(f[9:-4],"%Y-%m-%d"))
        time_of_savefile = datetime.strptime(max_in_savefile[7:-4],"%Y-%m-%d")
        time_of_autosave = datetime.strptime(max_in_autosave[9:-4],"%Y-%m-%d")

        if time_of_savefile < time_of_autosave:
            filename = max_in_autosave
        else:
            filename = max_in_savefile

    try:
        filepath = os.path.join(save_path, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            serialized_users = json.load(f)

        global users
        users = {int(qq): deserialize_player(data) for qq, data in serialized_users.items()}
        logger.debug(users)
    except Exception as e:
        await admin_getSave.finish(f"发生错误:{e}")

    await admin_getSave.finish(f"已读取存档 {filename}")

