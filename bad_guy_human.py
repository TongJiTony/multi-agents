import random
import uuid
import re
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from functools import partial
from typing import List, Iterable
from collections import defaultdict

from dotenv import load_dotenv
import os

openai_api_key = os.getenv("OPENAI_API_KEY")


# 加载提示文件
open_utf8 = partial(open, encoding='utf-8')
policy_prompt = open_utf8("prompt/policy.txt").read()
prompt_general_statement = open_utf8("prompt/describe_general.txt").read()
prompt_general_vote = open_utf8("prompt/vote_general.txt").read()

def format_history(history: List[dict]):
    cur_history = ''
    for his_idx, his_turn in enumerate(history):
        cur_turn = ''
        for his_user_idx, his_user_turn in his_turn.items():
            cur_turn += f'<agent_{his_user_idx}>\n{his_user_turn}\n</agent_{his_user_idx}>\n'
        if len(cur_turn):
            cur_turn_history = f'<turn_{his_idx+1}>\n' + cur_turn + f'</turn_{his_idx+1}>'
            cur_history += '\n' + cur_turn_history
    return cur_history

def build_statement_prompt(word: str, user_id, turn_id, history: List[dict]):
    return prompt_general_statement.format(
        policy=policy_prompt,
        word=word,
        uid=user_id,
        history=format_history(history).strip(),
        turn_id=turn_id
    )

def build_vote_prompt(word: str, user_id, turn_id, history: List[dict], active_players: List[str], user_outed: str):
    return prompt_general_vote.format(
        policy=policy_prompt,
        word=word,
        uid=user_id,
        history=format_history(history).strip(),
        turn_id=turn_id,
        active_players="\n".join(active_players),
        user_outed=user_outed
    )

class Player(BaseModel):
    index: int
    player_id: str
    word: str
    active: bool = True
    history: List[dict] = Field(default_factory=lambda: [])
    is_undercover: bool
    vote_history: List[dict] = Field(default_factory=lambda: [])

class WhoIsUndercover:
    def __init__(self, player_num=4, common_word="苹果", undercover_word="香蕉", human_player_id=None):
        assert player_num > 2, player_num
        self.player_num = player_num
        self.common_word = common_word
        self.undercover_word = undercover_word
        self.human_player_id = human_player_id
        words = [common_word] * (player_num - 1) + [undercover_word]
        random.shuffle(words)

        self.players: List[Player] = []
        for index, word in enumerate(words):
            self.players.append(
                Player(
                    index=index,
                    player_id=str(index + 1),
                    word=word,
                    is_undercover=word == undercover_word,
                    active=True,
                    history=[]
                )
            )

        self.game_id = uuid.uuid4()
        self.current_turn = 1
        self.llm = ChatOpenAI(
            temperature=0.95,
            model="glm-4",
            openai_api_key=openai_api_key,
            openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
        )
        self.game_status = "running"

        # 通知人类玩家他们的词语
        self.notify_human_player()

    def notify_human_player(self):
        human_player = next(player for player in self.players if player.player_id == self.human_player_id)
        print(f"Your word is: {human_player.word}")

    def call_llm(self, prompt: str, prefill="", stream=True):
        messages = [HumanMessage(content=prompt)]
        if prefill:
            messages.append(AIMessage(content=prefill))

        if stream:
            return self.llm.stream(messages)
        else:
            r = self.llm.invoke(messages)
            return r.content

    def collect_history(self, filter_out=True):
        history = [{} for _ in range(self.current_turn)]
        for player in self.players:
            if filter_out and not player.active:
                continue
            for his in player.history:
                history[his['turn'] - 1][player.player_id] = str(his['statement'])
        return history

    def player_statement(self, player: Player, statement=None):
        if player.player_id == self.human_player_id and statement is not None:
            thinking = "User provided input."
        else:
            word = player.word
            prompt = build_statement_prompt(
                word,
                user_id=player.player_id,
                turn_id=self.current_turn,
                history=self.collect_history()
            )
            content = self.call_llm(prompt, prefill="<thinking>", stream=False)
            result = '<thinking>' + content

            # Debug print to inspect the result
            print(f"DEBUG: result = {result}")

            thinking_match = re.findall("<thinking>(.*?)</thinking>", result, re.S)
            statement_match = re.findall("<output>(.*?)</output>", result, re.S)

            if not thinking_match or not statement_match:
                raise ValueError(f"Expected tags not found in result: {result}")

            thinking = thinking_match[0].strip()
            statement = statement_match[0].strip()

        player.history.append({
            "turn": self.current_turn,
            "statement": statement,
            "thinking": thinking
        })
        return statement

    def player_vote(self, player: Player, vote=None):
        if player.player_id == self.human_player_id and vote is not None:
            thinking = "User provided input."
        else:
            active_players = [f"agent_{p.player_id}" for p in self.players if p.active and p.player_id != player.player_id]
            user_outed = ", ".join([f"agent_{p.player_id}" for p in self.players if not p.active])
            prompt = build_vote_prompt(
                word=player.word,
                user_id=player.player_id,
                turn_id=self.current_turn,
                history=self.collect_history(),
                active_players=active_players,
                user_outed=user_outed
            )
            content = self.call_llm(prompt, prefill="<thinking>", stream=False)
            result = '<thinking>' + content

            # Debug print to inspect the result
            print(f"DEBUG: result = {result}")

            thinking_match = re.findall("<thinking>(.*?)</thinking>", result, re.S)
            vote_match = re.findall("<output>(.*?)</output>", result, re.S)

            if not thinking_match or not vote_match:
                raise ValueError(f"Expected tags not found in result: {result}")

            thinking = thinking_match[0].strip()
            vote = vote_match[0].strip()

            # Extract player ID from the vote result
            vote_id_match = re.findall(r"agent_(\d+)", vote)
            if not vote_id_match:
                raise ValueError(f"Invalid vote result: {vote}")

            vote = vote_id_match[0]

        player.vote_history.append({
            "turn": self.current_turn,
            "vote": vote,
            "thinking": thinking
        })
        return vote

    def next_turn_statement(self, human_statement=None):
        for player in self.players:
            if not player.active:
                continue
            if player.player_id == self.human_player_id:
                statement = self.player_statement(player, human_statement)
            else:
                statement = self.player_statement(player)
            yield {
                'player': player,
                'current_turn': self.current_turn,
                'statement': statement
            }

    def next_turn_vote(self, human_vote=None):
        for player in self.players:
            if not player.active:
                continue
            if player.player_id == self.human_player_id:
                vote = self.player_vote(player, human_vote)
            else:
                vote = self.player_vote(player)
            yield {
                'player': player,
                'current_turn': self.current_turn,
                'vote': vote
            }

    def find_vote_result(self):
        votes = defaultdict(int)
        for player in self.players:
            if player.vote_history[-1]['turn'] == self.current_turn:
                votes[str(player.vote_history[-1]['vote']).replace("agent_", "")] += 1
        
        votes_sorted = sorted(list(votes.items()), key=lambda x: x[1], reverse=True)
        vote_res = votes_sorted[0][0]

        active_player_ids = [player.player_id for player in self.players if player.active]
        assert vote_res in active_player_ids, (vote_res, active_player_ids)
        return vote_res

    def execute_vote_result(self):
        vote_res = self.find_vote_result()
        for player in self.players:
            if player.player_id == vote_res:
                player.active = False  
                return player

    def is_game_close(self):
        active_players = [player for player in self.players if player.active]
        active_player_count = len(active_players)
        undercover_player = next((player for player in self.players if player.is_undercover), None)
        
        if active_player_count <= 3 and undercover_player and undercover_player.active:
            self.game_status = f"游戏结束，卧底玩家 {undercover_player.player_id} 胜利！"
            return True
        elif undercover_player and not undercover_player.active:
            self.game_status = f"游戏结束，平民玩家胜利！卧底玩家 {undercover_player.player_id} 被淘汰。"
            return True
        return False        

# 创建游戏对象，包含一个人类玩家
# game = WhoIsUndercover(human_player_id="1")

# # 进行两回合
# for turn in range(1, 3):
#     game.current_turn = turn
#     for result in game.next_turn_statement():
#         player = result['player']
#         statement = result['statement']
#         print(f"Turn {turn}, Player {player.player_id}: {statement}")

#     for result in game.next_turn_vote():
#         player = result['player']
#         vote = result['vote']
#         print(f"Turn {turn}, Player {player.player_id} voted for agent_{vote}")

#     eliminated_player = game.execute_vote_result()
#     print(f"Turn {turn}, Player {eliminated_player.player_id} was eliminated")
    
#     if game.is_game_close():
#         print(game.game_status)
#         break
    
#     time.sleep(6)
