# 谁是卧底：多智能体对抗策略

## 策略评价标准
- 奖励函数：
$$
RewardFunction=\sum_{i=0}^{N}{\delta_i\cdot (N-i-1-v_i)\cdot \eta_i} \quad\quad (N-i\ge 3)
$$
\delta_i:卧底第i轮存活情况，活为1，不活为0
N:场上初始总人数
v_i:第i轮投票卧底获得的票数
\eta_i:第i轮奖励系数
\eta_i:第i轮奖励系数


- 归一化函数：
$$
f_\text{norm} = \frac{f_x - \text{min\_val}}{\text{max\_val} - \text{min\_val}}
$$

- rf_value_norm 属于[0,1],越靠近1代表卧底得分更高
without strategy: 0.1
with strategy: 0.43

## 运行脚本
- 6个agent智能对战版（电子斗蛐蛐）
```bash
streamlit run front_end_auto.py
```
- 5个agent加人类玩家
```bash
streamlit run front_end.py
```
- 计算游戏公平性（场上所有玩家随机投票，卧底胜利概率）
```bash
python winProbability.py
```
