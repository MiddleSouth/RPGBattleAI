import matplotlib
import matplotlib.pyplot as plt
import torch

from AIPlayer.DQNPlayer import DQNPlayer
import RPGTurnBattle as RPG

training_env = RPG.Simulation(lvs=[5])

player = DQNPlayer(training_env, 200)
player.set_learning_parameters(
    eps_decay=800,
    num_episodes=1000,
    batch_size=128,
)
player.training()

plt.figure(2)
plt.clf()
rewards_t = torch.tensor(player.episode_rewards, dtype=torch.float)
plt.title('Training...')
plt.xlabel('Episode')
plt.ylabel('Reward')
plt.plot(rewards_t.numpy())
# 過去100エピソードの平均報酬の推移
if len(rewards_t) >= 100:
    means = rewards_t.unfold(0, 100, 1).mean(1).view(-1)
    means = torch.cat((torch.zeros(99), means))
    plt.plot(means.numpy())
plt.show()
