import sys
import random
from typing import Tuple

import numpy as np

from battle.battle import Battle
from battle.command import PlayerCommands

class Simulation:

    def __init__(self, data_folder_path:str='battle/data/', scenario_code:str='default'):
        """コンストラクタ

        Args:
            data_folder_path (str, optional): Unitデータの格納先フォルダパス. Defaults to 'Lv3/battle/data/'.
            scenario (str, optional): ゲームのシナリオ. Defaults to 'default'.
        """
        self.data_folder_path = data_folder_path

        self.n_battle = 0
        self.message = ''
        self.total_damage = 0 # 現在の敵に与えたダメージの合計
        self.is_firat_attack = True

        # 戦闘データ読み込み
        self.battle = Battle(self.data_folder_path, scenario_code)

    def reset(self)->np.array:
        """環境を初期化する

        Args:
            lv (int, optional): プレイヤーのレベル. Defaults to 5.

        Returns:
            np.array: 最初の状態
        """

        # 戦闘回数リセット
        self.n_battle = 0

        # 戦闘準備
        self.battle.reset()

        # 最初の敵と遭遇
        self.battle.encount()

        return self.get_status()

    def step(self, action:int)->Tuple[np.array, int, bool, str]:
        """行動選択1回分、戦闘を進める

        Args:
            action (int): プレイヤーの行動

        Returns:
            Tuple[np.array, int, bool, str]: 状態、報酬、エピソード終端、戦闘結果メッセージ
        """        
        reward = 0
        done = False
        # 行動選択して1ターン戦闘を進める
        message = self.battle.act_one_turn(action)

        # 10回戦闘終了、またはプレイヤー死亡で終了
        if self.battle.player.hp == 0:
            message += f'\nあなたは死んでしまいました。'
            reward -= 20
            done = True
        elif(self.battle.enemy.hp == 0 or self.battle.escape):
            if not self.battle.escape:
                message += f'\n\n{self.battle.enemy.name} を倒した！'
                reward += 1
            self.n_battle += 1
            self.battle.player.recovery_battle_condition()
            if self.n_battle < 10:
                message += f'\n残り戦闘回数： {10 - self.n_battle} 回'
                self.battle.encount()
                message += f'\n\n新たに {self.battle.enemy.name} が出現しました。コマンドを選択してください。'
            else:
                message += f'\n\n敵を 10 体倒しました！ シミュレーションを終了します。'
                reward += 10
                done = True

        # 1ターンの結果を返す(state, reward, done, info)
        return self.get_status(), reward, done, message

    def render(self)->str:
        """現在の状態を表示する

        Returns:
            str: 現在の状態
        """        
        message = f'\nあなたのステータス'
        message += f'\nHP:{self.battle.player.hp}, MP:{self.battle.player.mp}'
        message += f'\nモンスター：{self.battle.enemy.name}'
        return message

    def get_status(self)->np.array:
        """現在の状態を取得する

        Returns:
            np.array: 状態
        """
        l = [
            self.battle.player.max_hp,
            self.battle.player.hp,
            self.battle.player.mp,
            self.battle.player.attack,
            self.battle.player.difense,
            self.battle.player.speed,
            int(self.battle.player.seal_spell),
            int(self.battle.player.sleep),
            self.battle.enemy.max_hp,
            self.battle.enemy.attack,
            self.battle.enemy.difense,
            self.battle.enemy.speed,
            int(self.battle.enemy.seal_spell),
            int(self.battle.enemy.sleep),
            self.battle.total_damage,
            self.n_battle
        ]
        
        l.extend(
            self.battle.player.command_pattern
        )

        l.extend(
            self.battle.enemy.command_pattern
        )
        return np.array(l)

    def get_n_actions(self)->int:
        """選択可能な行動数を取得する

        Returns:
            int: 選択可能な行動数
        """
        return len(PlayerCommands)

    def render_command_list(self)->str:
        """人間のプレイヤー向けにコマンドリストを表示する。

        Returns:
            str: コマンドリスト
        """
        message = ''
        commands = self.battle.player.commands
        for i, command in enumerate(commands):
            message += f'{PlayerCommands[command].name}:{i}, '
        return message

    def seed(self, seed:int)->None:
        """乱数を固定する

        Args:
            seed (int): 乱数シード
        """
        random.seed(seed)
