# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Aleksander Beloi (beloi.alex@gmail.com)
# Copyright (c) 2018 Sam Wenke (samwenke@gmail.com)
# Copyright (c) 2019 Ingvar Lond (ingvar.lond@gmail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.



# To run the tests install pytest with "pip install pytest" and run a command "py.test" in the tests folder

import pytest

from holdem.env import TexasHoldemEnv

from holdem.utils import player_table, community_table, action_table

def test_fold():
    for n_players in range(2, 11):
        env = _create_env(n_players)
        _reset_env(env)
        done = False
        iters = 0
        while not done:
            iters += 1
            _, r, done, _ = _step(env, [action_table.FOLD, 0])
            expected_reward = [0] * n_players
            if done:
                bb_pos = 1 if n_players == 2 else 2
                expected_reward[bb_pos] = (env._smallblind + env._bigblind) / env._bigblind
            assert r == expected_reward
        assert iters == n_players - 1 # Last to act wins when everyone else folds

def test_heads_up_positions_and_blind_posting():
    env = _create_env(2)
    player_infos, _, community_infos, _ = _reset_env(env)
    assert player_infos[0][player_table.CURRENT_BET] == env._smallblind # Button is small blind in heads-up
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 0
    
    env = _create_env(3)
    player_infos, _, community_infos, _ = _reset_env(env)
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[2][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 0

def test_bet_sizes_2_player():
    # 2 Players
    env = _create_env(2)
    player_infos, _, community_infos, _ = _reset_env(env)
    assert player_infos[0][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._smallblind + env._bigblind
    assert community_infos[community_table.TO_ACT_POS] == 0
    
    # SB/BTN minraises
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 2])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == env._bigblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind * 2
    assert community_infos[community_table.POT] == env._bigblind * 3
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 1
    
    # BB calls
    s, r, d, i = _step(env, [action_table.CALL, 0])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == 0
    assert community_infos[community_table.POT] == env._bigblind * 4
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 1

    # FLOP
    # BB minbets
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._bigblind * 5
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 0

    # SB/BTN folds
    s, r, d, i = _step(env, [action_table.FOLD, 0])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [-(env._bigblind * 2 - env._smallblind) / env._bigblind, (env._bigblind * 3) / env._bigblind] # Stack change in big blinds
    assert d == True
    assert i['money_won'] == -50
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == 0
    assert community_infos[community_table.POT] == env._bigblind * 5
    assert community_infos[community_table.BUTTON_POS] == 0

    # Reset environment to play next hand
    player_infos, _, community_infos, _ = _reset_env(env)
    assert player_infos[0][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._smallblind + env._bigblind
    assert community_infos[community_table.BUTTON_POS] == 1 # Previous BB is now BTN/SB
    assert community_infos[community_table.TO_ACT_POS] == 1 # SB/BTN acts first heads-up

def test_bet_sizes_3_player():
    # 3 Players
    env = _create_env(3)
    player_infos, _, community_infos, _ = _reset_env(env)
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[2][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._smallblind + env._bigblind
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 0
    
    # BTN minraises, SB to act
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 2])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert player_infos[2][player_table.CURRENT_BET] == env._bigblind * 2
    assert community_infos[community_table.POT] == env._bigblind * 3 + env._smallblind
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 1
    
    # SB calls, BB to act
    s, r, d, i = _step(env, [action_table.CALL, 0])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == env._bigblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind * 2
    assert player_infos[2][player_table.CURRENT_BET] == env._bigblind * 2
    assert community_infos[community_table.POT] == env._bigblind * 5
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 2

    # BB calls, SB to act
    s, r, d, i = _step(env, [action_table.CALL, 1337])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == 0
    assert player_infos[2][player_table.CURRENT_BET] == 0
    assert community_infos[community_table.POT] == env._bigblind * 6
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 1

    # FLOP
    # SB minbets
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == 0
    assert player_infos[2][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._bigblind * 7
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 2

    # BB flats, BTN to act
    s, r, d, i = _step(env, [action_table.CALL, -99999999])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert player_infos[2][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._bigblind * 8
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 0

    # BTN raises to 10, SB to act
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 10])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == env._bigblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert player_infos[2][player_table.CURRENT_BET] == env._bigblind * 10
    assert community_infos[community_table.POT] == env._bigblind * 18
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 1

    # SB calls, BB to act
    s, r, d, i = _step(env, [action_table.CALL, 0])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == env._bigblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind * 10
    assert player_infos[2][player_table.CURRENT_BET] == env._bigblind * 10
    assert community_infos[community_table.POT] == env._bigblind * 27
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 2

    # BB folds, SB to act
    s, r, d, i = _step(env, [action_table.FOLD, 0])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == 0
    assert player_infos[2][player_table.CURRENT_BET] == 0
    assert community_infos[community_table.POT] == env._bigblind * 27
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 1

    # TURN
    # SB shoves all in, BTN to act
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 88])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind * 88
    assert player_infos[2][player_table.CURRENT_BET] == 0
    assert community_infos[community_table.POT] == env._bigblind * 115
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 0

    # BTN folds
    s, r, d, i = _step(env, [action_table.FOLD, 0])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [-12 , (15 * env._bigblind + env._smallblind) / env._bigblind, -2]
    assert d == True
    assert i['money_won'] == -12 * env._bigblind
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == 0
    assert player_infos[2][player_table.CURRENT_BET] == 0
    assert community_infos[community_table.POT] == env._bigblind * 115
    assert community_infos[community_table.BUTTON_POS] == 0

    # Reset environment to play next hand
    player_infos, _, community_infos, _ = _reset_env(env)
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[2][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._smallblind + env._bigblind
    assert community_infos[community_table.BUTTON_POS] == 1 # Previous SB is now BTN
    assert community_infos[community_table.TO_ACT_POS] == 1 # BTN acts first 3-way

def test_min_max_bet():
    # 2 Players
    env = _create_env(2)
    player_infos, _, community_infos, _ = _reset_env(env)
    assert player_infos[0][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._smallblind + env._bigblind
    assert community_infos[community_table.TO_ACT_POS] == 0

    # BTN minraises
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 2])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == env._bigblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind * 2
    assert community_infos[community_table.POT] == env._bigblind * 3
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 1

    # BB minraises
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 3])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == env._bigblind * 2
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind * 3
    assert community_infos[community_table.POT] == env._bigblind * 5
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 0

    # BTN raises from 3 to 10 bb
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 10])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == env._bigblind * 3
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind * 10
    assert community_infos[community_table.POT] == env._bigblind * 13
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 1

    # BB raises from 10 to 50
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 50])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == env._bigblind * 10
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind * 50
    assert community_infos[community_table.POT] == env._bigblind * 60
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 0

    # BTN raises from 50 to 90 bb
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 90])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == env._bigblind * 50
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind * 90
    assert community_infos[community_table.POT] == env._bigblind * 140
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 1

    # BB shoves 100 bb
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 100])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == env._bigblind * 90
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind * 100
    assert community_infos[community_table.POT] == env._bigblind * 190
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 0

    # BTN folds
    s, r, d, i = _step(env, [action_table.FOLD, 0])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [-(90 * env._bigblind - env._smallblind) / env._bigblind, 91]
    assert d == True
    assert i['money_won'] == -90 * env._bigblind
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == 0
    assert community_infos[community_table.POT] == env._bigblind * 190
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 1

    # Reset environment to play next hand
    player_infos, _, community_infos, _ = _reset_env(env)
    assert player_infos[0][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._smallblind + env._bigblind
    assert community_infos[community_table.BUTTON_POS] == 1 # Previous BB is now BTN/SB
    assert community_infos[community_table.TO_ACT_POS] == 1 # SB/BTN acts first heads-up

# Private methods

def _unpack_state(state):
    (player_states, (community_infos, community_cards)) = state
    player_infos, player_hands = zip(*player_states)
    return player_infos, player_hands, community_infos, community_cards

def _create_env(n_players):
    env = TexasHoldemEnv(n_players)
    for i in range(n_players):
        env.add_player(i, stack=2500)
    assert not env is None
    return env

def _reset_env(env):
    n_players = env.n_seats
    player_infos, player_hands, community_infos, community_cards = _unpack_state(env.reset())
    assert not community_infos is None
    assert not community_cards is None
    assert not player_infos is None
    assert not player_hands is None
    assert len(player_hands) == n_players
    assert len(player_infos) == n_players
    return player_infos, player_hands, community_infos, community_cards

def _step(env, move):
    actions = [move] * env.n_seats
    return env.step(actions)