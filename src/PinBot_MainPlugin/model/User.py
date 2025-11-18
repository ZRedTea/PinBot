from datetime import datetime, timedelta
from typing import List, Dict, Any
from enum import Enum
import json

time_format = "%Y-%m-%d %H:%M:%S"

class UserStatus(Enum):
    """玩家状态枚举"""
    OFFLINE = 0
    PLAYING = 1
    WAITING = 2

class UserCostType(Enum):
    """玩家花费类型枚举"""
    NORMAL = 0
    OTHERS = 1

class User:
    """玩家类，用于实现对每个玩家的各种操作"""
    def __init__(self, nickname, userid):
        self._userid = userid                             #用户编号 => QQ号
        self._nickname = nickname                         #用户名
        self._total_play_time = timedelta()               #用户总游玩时长
        self._start_time : datetime = datetime.now()      #用户出勤开始时间
        self._balance = 0                                 #用户剩余金钱
        self._status = UserStatus.OFFLINE                 #用户目前状态
        self._current_machines = []                       #用户当前游玩的机台
        self._daily_costs: Dict[UserCostType, int] = {    #用户当日游玩花费
            UserCostType.NORMAL: 0,
            UserCostType.OTHERS: 0
        }
        self._is_banned = False                           #用户是否被封禁

    # === 属性直接访问 ===
    @property
    def user_id(self) -> str:
        return self._userid

    @property
    def nickname(self) -> str:
        return self._nickname

    @property
    def balance(self) -> int:
        return self._balance

    @property
    def status(self) -> UserStatus:
        return self._status

    @property
    def is_online(self) -> bool:
        return self._status != UserStatus.OFFLINE

    @property
    def is_banned(self) -> bool:
        return self._is_banned

    # === 信息相关方法 === #
    def change_nickname(self, nickname: str) -> bool:
        """
        修改昵称
        Args:
            nickname: str - 新昵称

        Returns:
            bool: 是否成功
        """
        self._nickname = nickname
        return True

    # === 时间相关方法 === #
    @property
    def total_play_time(self) -> timedelta:
        return self._total_play_time

    def get_total_play_time(self) -> list:
        """以列表形式返回总游玩时间"""
        total_seconds = int(self._total_play_time.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        return [days, hours, minutes]

    def get_total_play_time_str(self) -> str:
        """以字符串形式返回总游玩时间"""
        total_seconds = int(self._total_play_time.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{days}天{hours}小时{minutes}分钟"

    def add_play_time(self, minutes:int) -> None:
        """增加总游玩时间"""
        self._total_play_time += timedelta(minutes=minutes)

    # === 余额管理方法 === #
    def recharge_balance(self, amount: int) -> None:
        """充值余额"""
        self._balance += amount

    def reduce_balance(self, amount: int) -> None:
        """扣除余额"""
        self._balance -= amount

    def set_balance(self, amount: int) -> None:
        """设置余额"""
        self._balance = max(0,amount)

    # === 游玩状态管理 === #
    def start_playing(self) -> bool:
        """开始出勤"""
        if not self._is_banned and self._status == UserStatus.OFFLINE:
            self._status = UserStatus.PLAYING
            self._start_time = datetime.now()
            return True
        return False

    def start_waiting(self) -> bool:
        """开始等待"""
        if not self._is_banned and self._status == UserStatus.OFFLINE:
            self._status = UserStatus.WAITING
            self._start_time = datetime.now()
            return True
        return False

    def switch_to_playing(self, play_cost: int, play_time: int) -> bool:
        """状态转换至出勤
        Args:
            play_cost: int 本次出勤实际花费
            play_time: int 本次出勤游玩时长

        Returns:
            bool: 是否成功
        """
        if self._status == UserStatus.WAITING:
            self._status = UserStatus.PLAYING
            self._start_time = datetime.now()
            self._balance -= play_cost
            self._total_play_time += timedelta(minutes=play_time)
            return True
        return False

    def end_playing(self, play_cost: int, play_time: int) -> bool:
        """结束竖琴或等待
        Args:
            play_cost: int 本次出勤实际花费
            play_time: int 本次出勤游玩时长

        Returns:
            bool: 是否成功
        """
        if self._status == UserStatus.WAITING or self._status == UserStatus.PLAYING:
            self._status = UserStatus.OFFLINE
            self._start_time = datetime.now()
            self._balance -= play_cost
            self._total_play_time += timedelta(minutes=play_time)
            return True
        return False

    # === 当日消费管理 === #
    def add_daily_cost(self, cost_type: UserCostType, amount: int) -> bool:
        """增加某一类的当日消费
        Args:
            cost_type: str - 消费类型
            amount: int - 消费数量

        Returns:
            bool: 是否成功
        """
        if amount > 0:
            self._daily_costs[cost_type] += amount
            return True
        return False

    def get_daily_cost(self, cost_type: UserCostType = UserCostType.NORMAL) -> int:
        """获取某一类的当日消费
        Args:
            cost_type: UserCostType - 消费类型，默认普通消费

        Returns:
            int: 该类今日消费
        """
        return self._daily_costs[cost_type]

    def set_daily_cost(self, cost_type: UserCostType, amount: int) -> bool:
        """
        设置某一类的今日消费
        Args:
            cost_type: UserCostType - 消费类型
            amount: int - 消费数量

        Returns:
            bool: 是否成功
        """
        try:
            self._daily_costs[cost_type] = max(0,amount)
            return True
        except Exception as e:
            print(e)
            return False

    # === 序列化方法 ===
    def to_dict(self) -> dict:
        """将 User 对象转换为字典，便于 JSON 序列化"""
        return {
            'user_id': self._userid,
            'nickname': self._nickname,
            'total_play_time_seconds': int(self._total_play_time.total_seconds()),
            'start_time': self._start_time.strftime(time_format) if self._start_time else None,
            'balance': self._balance,
            'status': self._status.value,  # 存储枚举值
            'current_machines': self._current_machines.copy(),
            'daily_costs': {
                cost_type.value: amount for cost_type, amount in self._daily_costs.items()
            },
            'is_banned': self._is_banned
        }

    def to_json(self) -> str:
        """将 User 对象转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """从字典创建 User 对象"""
        user = cls(data['nickname'], data['user_id'])

        # 恢复基本属性
        user._total_play_time = timedelta(seconds=data['total_play_time_seconds'])
        user._balance = data['balance']
        user._is_banned = data['is_banned']
        user._current_machines = data['current_machines'].copy()

        # 恢复时间
        user._start_time = datetime.strptime(data['start_time'], time_format)

        # 恢复状态枚举
        user._status = UserStatus(data['status'])

        # 恢复消费记录
        user._daily_costs = {
            UserCostType(cost_type): amount
            for cost_type, amount in data['daily_costs'].items()
        }

        return user

    @classmethod
    def from_json(cls, json_str: str) -> 'User':
        """从 JSON 字符串创建 User 对象"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    # === 保存和加载方法 ===
    def save_to_file(self, filename: str) -> None:
        """将用户数据保存到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    @classmethod
    def load_from_file(cls, filename: str) -> 'User':
        """从文件加载用户数据"""
        with open(filename, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())

    # === 用户管理类的序列化方法 ===
    @staticmethod
    def save_users_to_file(users_dict: Dict[str, 'User'], filename: str) -> None:
        """保存所有用户数据到文件"""
        users_data = {
            user_id: user.to_dict()
            for user_id, user in users_dict.items()
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_users_from_file(filename: str) -> Dict[str, 'User']:
        """从文件加载所有用户数据"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                users_data = json.load(f)

            return {
                user_id: User.from_dict(user_data)
                for user_id, user_data in users_data.items()
            }
        except FileNotFoundError:
            return {}  # 文件不存在时返回空字典