import random
from typing import Tuple
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field

from battle.unit import UnitType, Unit

@dataclass
class ActionResults():
    """1ユニットの行動結結果を格納する"""
    message: str
    damage: int = field(default=0)
    recover: int = field(default=0)
    escape: bool = field(default=False)

class Command(metaclass=ABCMeta):
    """戦闘コマンド"""
    def __init__(self, name):
        self.name = name

    def damage_message(self, damaged_unit:Unit, damage:int)->str:
        """ダメージを与えたときのメッセージ

        Args:
            damaged_unit (Unit): ダメージを受けたユニット
            damage (int): ダメージの数値

        Returns:
            str: バトルメッセージ
        """
        message = ''
        if damaged_unit.unit_type == UnitType.PLAYER:
            message = f'{damaged_unit.name} は {damage} のダメージを受けた！'
        else:
            message = f'{damaged_unit.name} に {damage} のダメージを与えた！'
        
        return message

    @abstractmethod
    def action(self, action_unit:Unit, target_unit:Unit)->ActionResults:
        pass

class Attack(Command):
    """通常攻撃"""
    def __init__(self):
        super().__init__('こうげき')

    def action(self, action_unit:Unit, target_unit:Unit)->ActionResults:
        """通常攻撃

        Args:
            action_unit (Unit): 攻撃側ユニット
            target_unit (Unit): 攻撃対象ユニット

        Returns:
            ActionResults: ダメージ, バトルメッセージ
        """
        damage = int((action_unit.attack - (target_unit.difense // 2)) // (2 + random.randrange(256) / 128))
        if damage <= 0:
            damage = random.randint(0, 1)
        target_unit.hp -= damage
        message = f'\n{action_unit.name} の攻撃！ ' + self.damage_message(target_unit, damage)
        if target_unit.hp < 0:
            target_unit.hp = 0
            message += f'\n{target_unit.name} は 倒れた！'
        return ActionResults(damage=damage, message=message)

class Spell(Command):
    """呪文"""
    def __init__(self, name:str, used_mp:int):
        super().__init__(name)
        self.used_mp = used_mp

    def valid_spell(self, unit:Unit, mp_use:int)->Tuple[bool, str]:
        """呪文の成否判定

        Args:
            unit (Unit): 呪文を唱えたユニット
            mp_use (int): 呪文の消費MP

        Returns:
            Tuple[bool, str]: 呪文の成否, 失敗時のメッセージ
        """
        # 封印状態の場合
        if unit.seal_spell:
            return False, 'しかし呪文は封じられている！'

        # MP不足チェック
        if unit.mp < mp_use:
            return False, 'しかしMPが足りなかった！'

        return True, ''

class AttackSpell(Spell):
    """攻撃呪文"""
    def __init__(self, name:str, used_mp:int, min_damage:int, max_damage:int):
        super().__init__(name, used_mp)
        self.min_damage = min_damage
        self.max_damage = max_damage

    def action(self, action_unit:Unit, target_unit:Unit)->ActionResults:
        """攻撃呪文を唱える

        Args:
            action_unit (Unit): 攻撃側ユニット
            target_unit (Unit): 攻撃対象ユニット

        Returns:
            ActionResults: ダメージ, バトルメッセージ
        """
        message = f'\n{action_unit.name} は {self.name} の呪文を唱えた！ '

        valid, tmp_message = super().valid_spell(action_unit, self.used_mp)
        if not valid:
            message += tmp_message
            return ActionResults(damage=0, message=message)

        damage = random.randint(self.min_damage, self.max_damage)
        action_unit.mp -= self.used_mp
        target_unit.hp -= damage
        message += super().damage_message(target_unit, damage)
        if target_unit.hp < 0:
            target_unit.hp = 0
            message += f'\n{target_unit.name} は 倒れた！'
        return ActionResults(damage=damage, message=message)

class RecoverSpell(Spell):
    """回復呪文"""
    def __init__(self, name:str, used_mp:int, min_recover:int, max_recover:int):
        super().__init__(name, used_mp)
        self.min_recover = min_recover
        self.max_recover = max_recover

    def action(self, action_unit:Unit, target_unit:Unit)->ActionResults:
        """回復呪文を唱える

        Args:
            action_unit (Unit): 呪文を唱えたユニット
            target_unit (Unit): 回復対象ユニット

        Returns:
            ActionResults: 回復量、バトルメッセージ
        """

        # Todo:DQ1の戦闘は1対1なので、単純化のため呪文を唱えたユニット=回復対象ユニットとする。
        message = f'\n{action_unit.name} は {self.name} の呪文を唱えた！ '
        valid, tmp_message = self.valid_spell(action_unit, self.used_mp)
        if not valid:
            message += tmp_message
            return ActionResults(recover=0, message=message)

        recover = action_unit.recovery_hp(random.randint(self.min_recover, self.max_recover))
        action_unit.mp -= self.used_mp
        message += f'{action_unit.name} の HP が {recover} 回復した！'
        return ActionResults(recover=recover, message=message)

class SealSpell(Spell):
    """呪文を封印する呪文"""
    def __init__(self, name:str, used_mp:int):
        super().__init__(name, used_mp)

    def action(self, action_unit:Unit, target_unit:Unit)->ActionResults:
        """封印呪文を唱える

        Args:
            action_unit (Unit): 呪文を唱えたユニット
            target_unit (Unit): 封印対象ユニット

        Returns:
            ActionResults: バトルメッセージ
        """

        message = f'\n{action_unit.name} は {self.name} の呪文を唱えた！ '
        valid, tmp_message = self.valid_spell(action_unit, self.used_mp)
        if not valid:
            message += tmp_message
            return ActionResults(message=message)

        target_unit.seal_spell = True
        action_unit.mp -= self.used_mp
        message += f'{target_unit.name} は呪文が使えなくなった！'
        return ActionResults(message=message)

class SleepSpell(Spell):
    """相手を睡眠状態にする呪文"""
    def __init__(self, name:str, used_mp:int):
        super().__init__(name, used_mp)

    def action(self, action_unit:Unit, target_unit:Unit)->ActionResults:
        """睡眠呪文を唱える

        Args:
            action_unit (Unit): 呪文を唱えたユニット
            target_unit (Unit): 睡眠対象ユニット

        Returns:
            ActionResults: バトルメッセージ
        """

        message = f'\n{action_unit.name} は {self.name} の呪文を唱えた！ '
        valid, tmp_message = self.valid_spell(action_unit, self.used_mp)
        if not valid:
            message += tmp_message
            return ActionResults(message=message)

        target_unit.sleep = True
        target_unit.n_sleep_tern = 0
        action_unit.mp -= self.used_mp
        message += f'{target_unit.name} は眠ってしまった！'
        return ActionResults(message=message)

class Escape(Command):
    """逃走"""
    def __init__(self):
        super().__init__('にげる')

    def action(self, action_unit:Unit, target_unit:Unit)->ActionResults:
        """逃げる

        Args:
            action_unit (Unit): 逃げるユニット
            target_unit (Unit): 相手ユニット

        Returns:
            ActionResults: 逃走成否, バトルメッセージ
        """
        message = f'\n{action_unit.name} は逃げ出した！'

        # モンスターは必ず逃走成功
        if action_unit.unit_type == UnitType.ENEMY:
            action_unit.hp = 0
            return ActionResults(escape=True, message=message)

        escape = False
        # プレイヤーはモンスターとのSpeed差により確率で成功
        if random.random() < (action_unit.speed * 4) / ((action_unit.speed * 4) + target_unit.speed):
            message += f'\nうまく逃げ切った！'
            target_unit.hp = 0
            escape = True
        else:
            message += f'\nしかし回り込まれてしまった！'
            escape = False

        return ActionResults(escape=escape, message=message)

PlayerCommands = {
    'attack': Attack(),
    'escape': Escape(),
    'cure': RecoverSpell('治療', 4, 18, 25),
    'fire': AttackSpell('火の玉', 3, 7, 12),
    'magic_seal': SealSpell('封印', 2),
    'sleep': SleepSpell('睡眠', 2),
}

EnemyCommands = {
    'attack': Attack(),
    'escape': Escape(),
    'cure': RecoverSpell('治療', 4, 10, 16),
    'fire': AttackSpell('火の玉', 2, 3, 10),
    'magic_seal': SealSpell('封印', 2),
    'sleep': SleepSpell('睡眠', 2),
}

