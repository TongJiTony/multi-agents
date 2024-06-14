import random

def simulate_game():
    players = ['平民'] * 5 + ['卧底']
    random.shuffle(players)
    player_indices = list(range(len(players)))

    while len(players) > 3:
        votes = []

        # 每个玩家投票淘汰其他玩家
        for i in range(len(players)):
            other_indices = [index for index in player_indices if index != i]
            eliminated_index = random.choice(other_indices)
            votes.append(eliminated_index)

        # 统计投票结果
        vote_counts = {index: votes.count(index) for index in player_indices}
        eliminated_index = max(vote_counts, key=vote_counts.get)
        eliminated_player = players[eliminated_index]
        
        players.pop(eliminated_index)
        player_indices.remove(eliminated_index)
        
        # 更新剩余玩家的索引
        player_indices = list(range(len(players)))
        
        if eliminated_player == '卧底':
            return '平民胜'
    
    if '卧底' in players:
        return '卧底胜'
    else:
        return '平民胜'

def estimate_win_probability(num_simulations=100000):
    results = {'平民胜': 0, '卧底胜': 0}
    
    for _ in range(num_simulations):
        result = simulate_game()
        results[result] += 1
    
    win_probability = results['卧底胜'] / num_simulations
    return win_probability

# 进行模拟
probability = estimate_win_probability()
print(probability)
