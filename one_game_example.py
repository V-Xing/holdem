import gym
import holdem
import numpy as np

from holdem.agent import DQNAgent
from holdem.utils import action_table


agent = DQNAgent(epsilon=1.0, alpha=0.001, gamma=0.1, time=7500)
agent_id = 0


def play_out_hand(env, n_seats):
    # reset environment, gather relevant observations
    obs, _ = env.reset()
    # Add batch size dimension
    obs = np.expand_dims(obs, axis=0)

    # display the table, cards and all
    env.render(mode='human')

    terminal = False
    while not terminal:
        current_player = env.current_player_id
        if current_player == env.agent_id:
            action_id = agent.choose_action(obs)

            if action_id == 0:
                action_id = action_table.CHECK
            elif action_id == 1:
                action_id = action_table.CALL
            elif action_id == 2:
                action_id = action_table.RAISE
            else:
                action_id = action_table.FOLD

            # If fold or call when not supposed to, set to check
            if (env.tocall == 0 and action_id not in [action_table.CHECK,
                                                      action_table.RAISE]):
                action_id = action_table.CHECK

            if action_id == action_table.RAISE:
                action = [action_id, 50]
            else:
                action = [action_id, action_table.NA]
        else:
            action = holdem.safe_action(current_player, env.tocall, n_seats)
        print(f'current player {current_player}, action {action}')
        next_obs, reward, terminal, info = env.step(action)
        next_obs = np.expand_dims(next_obs, axis=0)
        if current_player == env.agent_id:
            agent.learn(obs, action_id, reward, next_obs, terminal)
        obs = next_obs
        env.render(mode='human')


env = gym.make('TexasHoldem-v1', n_seats=2, equity_steps=10000)
env.add_player(agent_id, stack=2000, is_agent=True)
env.add_player(agent_id+1, stack=2000)
play_out_hand(env, env.n_seats)
