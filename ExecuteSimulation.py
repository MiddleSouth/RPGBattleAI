import RPGTurnBattle as RPG

print(f'ターン制RPG戦闘シミュレーションを開始します。')
env = RPG.Simulation('battle/data/', [8])
env.reset()
total_r = 0
print(f'\n {env.battle.enemy.name} が出現しました。コマンドを選択してください。')
while True:
    action = int(input(env.render_command_list() + '\n'))
    state, reward, done, message = env.step(action)
    print(message)
    #print(state) # AIに渡すステータス
    total_r += reward
    if done:
        break

    print(env.render())
print(f'獲得報酬：{total_r}')
