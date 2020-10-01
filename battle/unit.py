import json
import random
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Union

from battle import items

class UnitType(IntEnum):
    PLAYER = 0
    ENEMY = 1

@dataclass
class Unit:
    """戦闘ユニット"""
    # ステータス
    unit_type : UnitType
    id: int
    name: str
    attack: int = field(default=0, init=False)
    power : int
    difense: int = field(default=0, init=False)
    guard : int
    speed: int
    max_hp: int
    hp: int = field(default=0, init=False)
    max_mp: int
    mp: int = field(default=0, init=False)
    commands: list

    lv: int = field(default=0)
    weapon : str = field(default='none')
    armor : str = field(default='none')
    shield : str = field(default='none')

    seal_spell: bool = field(default=False, init=False)
    sleep: bool = field(default=False, init=False)
    n_sleep_tern: int = field(default=0, init=False)

    # プレイヤーやモンスターが使えるコマンドのリストをAIに通知するためのリスト
    command_pattern: list = field(default=None, init=False)

    def __post_init__(self):
        item = items.Items()
        wearpon_attack = item.weapons[self.weapon].attack
        self.attack = self.power + item.weapons[self.weapon].attack
        self.difense = self.guard + item.armors[self.armor].difense + item.armors[self.shield].difense
        self.hp = self.max_hp
        self.mp = self.max_mp

    def recovery_hp(self, recover:int)->int:
        """ユニットのHPを回復する

        Args:
            recover (int): 回復させたいHP量

        Returns:
            int: 実際に回復したHP量
        """
        if self.hp + recover > self.max_hp:
            recover = self.max_hp - self.hp
        self.hp += recover

        return recover

    def recovery_battle_condition(self):
        """戦闘中限定の状態異常を回復する"""
        self.seal_spell = False

    def recovery_all(self):
        """ユニットの全ステータスを完全回復させる"""
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.seal_spell = False
        self.sleep = False
        self.n_sleep_tern == 0

    def judge_awake(self)->bool:
        """起床判定

        Returns:
            bool: True = 起床
        """
        sample = random.randrange(3)
        if self.n_sleep_tern == 0:
            self.n_sleep_tern += 1
        elif sample == 0:
            self.sleep = False
            self.n_sleep_tern = 0

        return not self.sleep

class UnitEncoder(json.JSONEncoder):
    """UnitオブジェクトをJSONにエンコードする"""
    def default(self, o):
        if isinstance(o, Unit):
            return o.__dict__
        return super(UnitEncoder, self).default(0)

def unit_decode(json_object:dict)->Unit:
    """UnitオブジェクトのみのJSONをデコードする

    Args:
        json_object (dict): JSONのオブジェクト

    Returns:
        Unit: JSONからデコードしたUnitインスタンス
    """
    return Unit(
        unit_type=json_object['unit_type'],
        id=json_object['id'],
        lv=json_object.get('lv'),
        name=json_object['name'],
        power=json_object['power'],
        weapon=json_object.get('weapon', 'none'),
        guard=json_object['guard'],
        armor=json_object.get('armor', 'none'),
        shield=json_object.get('shield', 'none'),
        speed=json_object['speed'],
        max_hp=json_object['max_hp'],
        max_mp=json_object['max_mp'],
        commands=json_object['commands'],
    )

def load_units(file_path:str)->Union[list, Unit]:
    """ユニット情報を読み込む

    Args:
        file_path (str): 読み込み対象のJSONファイルパス

    Returns:
        list: 読み込み結果(ユニットのリスト)
    """
    with open(file=file_path, mode='r', encoding='utf-8') as f:
        sf = f.read()
        decode = json.JSONDecoder(object_hook=unit_decode).decode(sf)
        return decode
