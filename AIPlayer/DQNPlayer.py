import random
import numpy as np
from collections import namedtuple
from typing import Tuple
 
import torch
import torch.optim as optim
import torch.nn.functional as F

from .DQN import Transition, ReplayMemory, DQN

class DQNPlayer():

    def __init__(self, env, n_hidden_channels=100):
        """コンストラクタ

        Args:
            env : 学習対象の環境
        """
        # GPUの利用設定
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # ゲーム環境取得
        self.env = env
        self.env.reset()
        self.obs_size = len(self.env.get_status())
        self.n_actions = self.env.get_n_actions()

        # DQNネットワーク設定
        # 探索用モデル
        self.policy_net = DQN(self.obs_size, self.n_actions, n_hidden_channels).to(self.device)
        # 最適化用モデル
        self.target_net = DQN(self.obs_size, self.n_actions, n_hidden_channels).to(self.device)
        self.target_net.eval()

        # 最適化手法設定
        self.optimizer = optim.Adam(self.policy_net.parameters())
        # 経験再生メモリ
        self.memory = ReplayMemory(10000)

        # 各エピソードで得られた報酬
        self.episode_rewards = []

    def set_learning_parameters(self,
        batch_size:int=128,
        gamma:float=0.99,
        eps_start:float=0.9,
        eps_end:float=0.05,
        eps_decay:int=90,
        target_update:int=10,
        num_episodes:int=100
        ):
        """学習パラメータ設定

        Args:
            batch_size (int, optional): 経験再生のバッチサイズ. Defaults to 128.
            gamma (int, optional): Q学習の割引率. Defaults to 0.99.
            eps_start (int, optional): εの開始値. Defaults to 0.9.
            eps_end (int, optional): εの最終値. Defaults to 0.05.
            eps_decay (int, optional): εが最終値に到達するまでのエピソード数. Defaults to 90.
            target_update (int, optional): DQNのアップデート頻度. Defaults to 10.
            num_episodes (int, optional): 訓練エピソード数. Defaults to 100.
        """
        self.BATCH_SIZE = batch_size
        self.GAMMA = gamma
        self.EPS_START = eps_start
        self.EPS_END = eps_end
        self.EPS_DECAY = eps_decay
        self.TARGET_UPDATE = target_update
        self.num_episodes = num_episodes

    def select_action(self, state:torch.tensor, i_episode:int):
        """行動選択

        Args:
            state(torch.tensor): 現在の状態
            i_episode(int): 現在のエピソード番号
        
        Returns:
            tensor: 選択した行動のindex
        """
        sample = random.random()

        # epsを線形に減らす
        eps_threshold = self.EPS_START - (i_episode / self.EPS_DECAY)
        if eps_threshold < self.EPS_END:
            eps_threshold = self.EPS_END

        if sample > eps_threshold:
            with torch.no_grad():
                return self.policy_net(state).max(1)[1].view(1, 1)
        else:
            return torch.tensor([[random.randrange(self.n_actions)]], device=self.device, dtype=torch.long)

    def optimize_model(self):
        """モデルを更新する"""
        if len(self.memory) < self.BATCH_SIZE:
            return

        # 経験を取得する
        transitions = self.memory.sample(self.BATCH_SIZE)
        batch = Transition(*zip(*transitions))

        # 最後の状態（最後の行動実行後の状態）は不要なのでマスクする
        non_final_mask = torch.tensor(tuple(map(lambda s: s is not None, batch.next_state)), device=self.device, dtype=torch.bool)
        non_final_next_states = torch.cat([s for s in batch.next_state if s is not None])

        # 取得した経験リストを一つのtorch.tensorに変換（リストを結合）する
        state_batch = torch.cat(batch.state)
        action_batch = torch.cat(batch.action)
        reward_batch = torch.cat(batch.reward)

        # 各状態と行動の組み合わせに対するQ値を取得する
        state_action_values = self.policy_net(state_batch).gather(1, action_batch)
    
        # 過去の経験の各状態におけるQ値の最大値（ベストな行動を行った場合のQ値）を取得する。
        # なお、最後の状態からは行動を行わない（=Q値が常に0になる）ため、経験再生の対象外とする。
        next_state_values = torch.zeros(self.BATCH_SIZE, device=self.device)
        next_state_values[non_final_mask] = self.target_net(non_final_next_states).max(1)[0].detach()

        # Q値の期待値を取得する
        expected_state_action_values = (next_state_values * self.GAMMA) + reward_batch

        # Q値の損失計算を行う
        loss = F.smooth_l1_loss(state_action_values, expected_state_action_values.unsqueeze(1))

        # モデルを更新する
        self.optimizer.zero_grad()
        loss.backward()
        for param in self.policy_net.parameters():
            param.grad.data.clamp_(-1, 1)
        self.optimizer.step()

    def conv_state(self, state):
        """numpy.ndarrayをtorch.tensorに変換してGPUに転送する

        Args:
            state(ndarray): 状態
        
        Returns:
            tensor: 状態
        """
        state = np.ascontiguousarray([state], dtype=np.float32)
        state = torch.from_numpy(state).to(self.device)
        return state

    def training(self):
        """訓練を行う"""
        for i_episode in range(self.num_episodes):
            # 環境をリセットする
            state = self.env.reset()
            total_reward = 0
            done = False

            state = self.conv_state(state)

            while done == False:
                # 行動選択する
                action = self.select_action(state, i_episode)

                # 行動の結果を取得する
                next_state, reward, done, _ = self.env.step(action.item())

                total_reward += reward
                reward = torch.tensor([reward], device=self.device)

                if done:
                    next_state = None
                else:
                    next_state = self.conv_state(next_state)

                # 経験を保存する
                self.memory.push(state, action, next_state, reward)

                state = next_state

                # 経験再生を用いてDQNモデルを更新する
                self.optimize_model()

            # plot データを追加
            self.episode_rewards.append(total_reward)

            # 探索中のDQNを経験再生用DQNにコピーする
            if i_episode % self.TARGET_UPDATE == 0:
                self.target_net.load_state_dict(self.policy_net.state_dict())

            # 学習の進捗表示    
            if (i_episode + 1) % (self.num_episodes / 10) == 0:
                print(f'end {i_episode + 1} episode')

        print('Complete')

    def test(self, test_env, n_episode:int, is_render:bool=False)->Tuple[list, int]:
        """訓練結果のテスト

        Args:
            test_env: テスト対象の環境
            n_episode (int): テストするエピソード数
            is_render (bool): テスト中のバトルメッセージを表示する. Defaults to False.

        Returns:
            Tuple[list, int]: 各エピソードの獲得報酬、全エピソードの死亡回数の合計
        """
        result_rewards = []
        dead_count = 0

        for i in range(n_episode):
            state = test_env.reset()
            state = self.conv_state(state)
            total_reward = 0
            done = False

            while not done:
                if is_render:
                    print(test_env.render())

                action = self.target_net(state).max(1)[1].view(1, 1)
                next_state, reward, done, message = test_env.step(action.item())
                total_reward += reward

                next_state = self.conv_state(next_state)
                state = next_state

                if is_render:
                    print(message)

            result_rewards.append(total_reward)
            if int(next_state[0][0].item()) == 0:
                dead_count += 1
            if is_render:
                print(f'獲得報酬は{total_reward}です。')
        
        return result_rewards, dead_count
