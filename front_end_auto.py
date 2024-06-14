import streamlit as st
import time
from bad_guy import BadGuy, Player  # 请替换为实际的文件名和导入路径

st.set_page_config(initial_sidebar_state='collapsed')

# 初始化游戏状态
if "game_obj" not in st.session_state:
    st.session_state['game_obj'] = None

if 'is_new_game' not in st.session_state:
    st.session_state.is_new_game = False

if 'is_reset_game' not in st.session_state:
    st.session_state.is_reset_game = False

if "is_game_close" not in st.session_state:
    st.session_state['is_game_close'] = False

if "undercover_word" not in st.session_state:
    st.session_state['undercover_word'] = "灌汤包"

if "common_word" not in st.session_state:
    st.session_state['common_word'] = '小笼包'

if "current_phase" not in st.session_state:
    st.session_state['current_phase'] = "statement"

# 开始新游戏
def start_new_game():
    st.session_state['game_obj'] = None  # 重置游戏对象
    msg = st.toast(f'正在开始新游戏。。。')
    undercover_word = st.session_state.undercover_word
    common_word = st.session_state.common_word
    
    msg = f'卧底词: {undercover_word}, 平民词: {common_word}'
    st.toast(msg)
    
    obj = BadGuy(
        player_num=6,  # 设置为6个玩家
        common_word=common_word,
        undercover_word=undercover_word,
    )
    st.session_state['game_obj'] = obj
    st.session_state.is_new_game = True
    st.session_state['is_game_close'] = False
    st.session_state['current_phase'] = "statement"

    # 输出调试信息
    st.write("新游戏已启动")
    st.write(f"卧底词: {undercover_word}, 平民词: {common_word}")

# 进行下一回合
def next_turn():
    game_obj: BadGuy = st.session_state['game_obj']

    if st.session_state['current_phase'] == "statement":
        st.toast(f'Players 正在做陈述。。。')
        for player_statement in game_obj.next_turn_statement():
            player: Player = player_statement['player']
            statement = player_statement['statement']
            thinking = player_statement['thinking']  # 获取思考内容
            # if thinking == "":
            #     thinking = "大脑思考不动了"
            st.markdown(f"**Player {player.player_id} 的思考:** \n{thinking}</span>", unsafe_allow_html=True)
            st.write(f"**Player {player.player_id} 的陈述:** {statement}")
            # time.sleep(2)  # 等待2秒钟以逐步显示

        st.session_state['current_phase'] = "vote"  # 切换到投票阶段

    elif st.session_state['current_phase'] == "vote":
        st.toast(f'Players 正在投票。。。')
        for player_vote in game_obj.next_turn_vote():
            player: Player = player_vote['player']
            vote = player_vote['vote']
            thinking = player_vote['thinking'] # 获取思考内容
            # if thinking == "":
            #     thinking = "大脑思考不动了"
            st.write(f"**Player {player.player_id} 的思考:** \n{thinking}")
            st.write(f"Player {player.player_id} 投票给 player_{vote}")
            # time.sleep(2)  # 等待2秒钟以逐步显示

        eliminated_player = game_obj.execute_vote_result()
        st.write(f"Player {eliminated_player.player_id} 被淘汰")

        if game_obj.is_game_close():
            st.toast(f'游戏结束')
            st.write(game_obj.game_status)
            st.balloons()
            st.session_state['is_game_close'] = True
        else:
            st.session_state['current_phase'] = "statement"  # 切换到陈述阶段

# 重置游戏
def reset_game():
    st.session_state.is_new_game = False
    game_obj = st.session_state['game_obj']
    if game_obj is not None:
        st.session_state['undercover_word'] = game_obj.undercover_word
        st.session_state['common_word'] = game_obj.common_word
    st.session_state['current_phase'] = "statement"

    # 输出调试信息
    st.write("游戏已重置")

# 显示控制按钮
buttons = st.columns(3)
with buttons[0]:
    is_new_game = st.button('New game', on_click=start_new_game, disabled=st.session_state.is_new_game)

with buttons[1]:
    is_next_turn = st.button('Next turn', disabled=not st.session_state.is_new_game or st.session_state['is_game_close'],
                             on_click=next_turn)

with buttons[2]:
    is_reset_game = st.button('Reset game', disabled=not st.session_state.is_new_game, on_click=reset_game)

# 显示玩家信息
if st.session_state.is_new_game:
    game_obj: BadGuy = st.session_state['game_obj']
    players = game_obj.players
    tab_names = []
    for player in players:
        color = "green" if player.active else "gray"
        player_name = f"{player.player_id}*" if player.is_undercover else f"{player.player_id}"
        tab_names.append(f':{color}[Player {player_name}]')

    player_tabs = st.tabs(tab_names)
    
    for idx, player in enumerate(players):
        with player_tabs[idx]:
            st.write(f"Player {player.player_id} 词语: {player.word}")

# 如果不是新游戏，显示词语输入框
if not st.session_state.is_new_game:
    undercover_word = st.text_input(label='卧底词语', key="undercover_word")
    common_word = st.text_input(label='平民词语', key="common_word")

# 提示用户开始新游戏
if not st.session_state.is_new_game:
    new_game_alert = st.info(f'请设置平民和卧底词汇, 点击 “New game” 开始游戏。')
