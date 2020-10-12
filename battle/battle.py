import os.path as path
import random
import json
from typing import Tuple

from battle.scenario import Scenario, load_scenarios
from battle.unit import UnitType, Unit, load_units
from battle.command import PlayerCommands, EnemyCommands, ActionResults

class Battle():
    def __init__(self, data_folder_path:str, scenario_code):
        """コンストラクタ

        Args:
            data_folder_path (str, optional): Unitデータの格納先フォルダパス.
            scenario (str, optional): ゲームのシナリオ. Defaults to 'default'.
        """
        # シナリオ読み込み
        scenarios = load_scenarios(path.join(data_folder_path, 'scenarios.json'))
        scenario = list(filter(lambda x: x.scenario_code == scenario_code, scenarios))[0]

        # プレイヤーデータ読み込み
        self.player_list = load_units(path.join(data_folder_path, 'player.json'))
        self.set_command_pattern(self.player_list, UnitType.PLAYER)
        self.player = list(filter(lambda x: x.lv == scenario.player_lv, self.player_list))[0]

        # 敵データ読み込み
        self.enemy_list = load_units(path.join(data_folder_path, 'enemies.json'))
        self.set_command_pattern(self.enemy_list, UnitType.ENEMY)
        self.enemies = list(filter(lambda x: x.id in scenario.enemies, self.enemy_list))

    def set_command_pattern(self, units:list, unit_type:UnitType):
        """ユニットが使用可能なコマンドをセットする

        Args:
            units (list): コマンド設定対象のユニットリスト
            unit_type (UnitType): コマンド設定対象のユニットのユニットタイプ
        """
        for unit in units:
            unit.command_pattern = []
            if unit_type == UnitType.PLAYER:
                commands = PlayerCommands
            else:
                commands = EnemyCommands
            for key in commands:
                unit.command_pattern.append(int(key in unit.commands))

    def reset(self):
        """最初の戦闘開始状態に初期化する
        """
        self.player.recovery_all()
        self.total_damage = 0
        self.escape = False

    def encount(self):
        """敵とランダムエンカウント"""
        self.enemy = self.enemies[random.randrange(len(self.enemies))]
        self.enemy.recovery_all()

        # 遭遇時の敵のHPはランダムで75～100％の状態。
        self.enemy.hp -= int(self.enemy.max_hp * (random.randrange(256) / 1024))

        # 各種戦闘ステータスリセット
        self.total_damage = 0
        self.escape = False

        # 先攻後攻を決める
        self.is_firat_attack = random.random() < (self.player.speed * 4) / ((self.player.speed * 4) + self.enemy.speed)

    def act_one_turn(self, action:int)->str:
        """戦闘を1ターン進める

        Args:
            action (int): プレイヤーの行動

        Returns:
            str: バトルメッセージ
        """
        message = ''

        if self.is_firat_attack :
            # 味方の行動
            self.escape, message = self.act_player(action)

            # 敵の行動 ※敵の逃走は未実装
            if(self.enemy.hp > 0):
                _, tmp_message = self.act_enemy()
                message += tmp_message
        else:
            _, message = self.act_enemy()
            if(self.player.hp > 0):
                self.escape, tmp_message = self.act_player(action)
                message += tmp_message

        return message
    
    def act_player(self, action:int)->Tuple[bool, str]:
        """プレイヤーの行動

        Args:
            action (int): プレイヤーが選択した行動

        Returns:
            Tuple[bool, str]: 逃走成功, バトルメッセージ
        """
        awake_message = ''
        if self.player.sleep:
            if self.player.judge_awake():
                awake_message = f'\n{self.player.name} は目を覚ました！'
            else:
                return False, f'\n{self.player.name} は眠っている･･･'

        # AIにプレイさせる際、まだ覚えていないコマンドを使おうとすることがあるので
        # その場合は何もしない。
        if action > len(self.player.commands) - 1:
            return False, f'\n{self.player.name} は 様子を見ている'
        results = PlayerCommands[self.player.commands[action]].action(self.player, self.enemy)
        results.message = awake_message + results.message
        self.total_damage += results.damage
        return results.escape, results.message

    def act_enemy(self)->Tuple[bool, str]:
        """敵の行動

        Returns:
            Tuple[bool, str]: 逃走成功、バトルメッセージ
        """
        awake_message = ''
        if self.enemy.sleep:
            if self.enemy.judge_awake():
                awake_message = f'\n{self.enemy.name} は目を覚ました！'
            else:
                return False, f'\n{self.enemy.name} は眠っている･･･'

        action = self.enemy.commands[random.randrange(len(self.enemy.commands))]
        results = EnemyCommands[action].action(self.enemy, self.player)
        results.message = awake_message + results.message
        self.total_damage -= results.recover
        return results.escape, results.message
