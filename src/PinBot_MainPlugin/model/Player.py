from datetime import datetime, timedelta
from typing import List, Dict, Any
from enum import Enum

class PlayerStatus(Enum):
    """玩家状态枚举"""
    OFFLINE = 0
    PLAYING = 1
    WAITING = 2

time_format = "%Y-%m-%d %H:%M:%S"
class Player:
    """玩家类，用于实现对每个玩家的各种操作"""
    def __init__(self, nickname, userid):
        self.__userid = userid       #用户编号 => QQ号
        self.__nickname = nickname   #用户名
        self.__allTime = [0,0,0]     #用户总时长 Day Hrs Min
        self.__balance = 0           #用户剩余金钱
        self.__startTime = 0         #用户出勤开始时间
        self.__status = False        #用户是否出勤
        self.__type = 1              #用户出勤类型
        self.__playing = []          #用户当前游玩机台
        self.__cost = [0]            #用户当日消费

        self.__banned = False        #用户是否被封禁

    def balanceRechar(self, money):
        self.__balance += money
    def balanceReduce(self, money):
        self.__balance -= money
    def balanceSet(self, money):
        self.__balance = money
    def getBalance(self):
        return self.__balance

    def allTimeAdd(self, time):
        time += self.getMins()
        Day = time // 1440
        time = time % 1440
        Hour = time // 60
        Minute = time % 60
        self.__allTime[0] = Day
        self.__allTime[1] = Hour
        self.__allTime[2] = Minute

    def changeName(self, newNickname):
        self.__nickname = newNickname

    def typeShukkin(self):
        self.__type = 1
    def typeWaiting(self):
        self.__type = 2

    def costClear(self):
        self.__cost = [0]
    def costAdd(self, type, money):
        """type: 0 - 出勤"""
        self.__cost[type] += money
    def costReduce(self, type, money):
        """type: 0 - 出勤"""
        self.__cost[type] -= money
    def costSet(self, type, money):
        """type: 0 - 出勤"""
        self.__cost[type] = money
    def costAllSet(self, cost):
        self.__cost = cost

    def ban(self):
        self.__banned = True
    def unban(self):
        self.__banned = False

    def online(self):
        self.__status = True
    def offline(self):
        self.__status = False

    ###set函数###
    def setStartTime(self, time):
        self.__startTime = time

    ###get函数###
    def getDay(self):
        return self.__allTime[0]`
    def getHour(self):
        return self.__allTime[1]
    def getMin(self):
        return self.__allTime[2]
    def getMins(self):
        return self.__allTime[0]*1440+self.__allTime[1]*60+self.__allTime[2]
    def getBalance(self):
        return self.__balance
    def getStartTime(self):
        return self.__startTime

    def getType(self):
        """
        出勤 : 1
        在场 : 2
        """
        return self.__type
    def getUserid(self):
        return self.__userid
    def getNickname(self):
        return self.__nickname
    def getStatus(self):
        return self.__status
    def isBanned(self):
        return self.__banned

    def getCost(self):
        return self.__cost

    def getInfo(self):
        return f"{self.__nickname}[{self.__userid}]"

def serialize_player(player):
    """用于存储数据时规格化玩家对象"""
    return {
        "userid": player.getUserid(),
        "nickname": player.getNickname(),
        "allTime": player.getMins(),
        "balance": player.getBalance(),
        "startTime": str(player.getStartTime()),
        "status": player.getStatus(),
        "type": player.getType(),
        "banned": player.isBanned(),
        "cost": player.getCost(),
    }

def deserialize_player(data):
    """用于读取数据时反规格化玩家对象"""
    player = Player(data["nickname"], data["userid"])
    player.allTimeAdd(data["allTime"])
    player.balanceSet(data["balance"])
    player.costAllSet(data["cost"])
    player.typeShukkin() if data["type"] == 1 else player.typeWaiting()
    player.ban() if data["banned"] else player.unban()
    if(data["status"]):
        player.online()
        player.setStartTime(datetime.strptime(data["startTime"], time_format))
    else:
        player.offline()
        player.setStartTime(0)
    return player