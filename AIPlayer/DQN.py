import random
from collections import namedtuple
 
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torchvision.transforms as T


Transition = namedtuple('Transition',
                        ('state', 'action', 'next_state', 'reward'))
 
class ReplayMemory(object):
    """
    経験再生を行うクラス
    """
 
    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
        self.position = 0
 
    def push(self, *args):
        """経験を記録する"""
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = Transition(*args)
        self.position = (self.position + 1) % self.capacity
 
    def sample(self, batch_size):
        """バッチサイズ分の経験をランダムに取得する"""
        return random.sample(self.memory, batch_size)
 
    def __len__(self):
        return len(self.memory)

class DQN(nn.Module): 
    def __init__(self, obs_size, n_actions, n_hidden_channels=100):
        super(DQN, self).__init__()
        self.l0 = nn.Linear(obs_size, n_hidden_channels)
        self.l1 = nn.Linear(n_hidden_channels, n_hidden_channels)
        self.l2 = nn.Linear(n_hidden_channels, n_actions)
 
    def forward(self, x):
        x = torch.relu(self.l0(x))
        x = torch.relu(self.l1(x))
        return self.l2(x)
