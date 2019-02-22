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
            _, r, done, i = _step(env, [action_table.FOLD, 0])
            expected_reward = [0] * n_players
            if done:
                bb_pos = 1 if n_players == 2 else 2
                expected_reward[bb_pos] = (env._smallblind + env._bigblind) / env._bigblind
                assert i['money_won'] == (-env._smallblind if n_players == 2 else 0)
            else:
                assert i['money_won'] == 0
            assert r == expected_reward
        assert iters == n_players - 1 # Last to act wins when everyone else folds
        _reset_env(env)
        done = False
        iters = 0
        while not done:
            iters += 1
            _, r, done, i = _step(env, [action_table.FOLD, 0])
            expected_reward = [0] * n_players
            if done:
                bb_pos = 0 if n_players == 2 else 3 % n_players
                expected_reward[bb_pos] = (env._smallblind + env._bigblind) / env._bigblind
                assert i['money_won'] == (env._smallblind if (n_players == 2 or n_players == 3) else 0)
            else:
                assert i['money_won'] == 0
            assert r == expected_reward
        assert iters == n_players - 1 # Last to act wins when everyone else folds

def test_positions_and_blind_posting():
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

    # Reset environment to play next hand
    player_infos, _, community_infos, _ = _reset_env(env)
    assert player_infos[0][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._smallblind + env._bigblind
    assert community_infos[community_table.BUTTON_POS] == 1 # Previous BB is now BTN/SB
    assert community_infos[community_table.TO_ACT_POS] == 1 # SB/BTN acts first heads-up

def test_preflop_allin_call():
    # 2 Players
    env = _create_env(2)
    player_infos, _, community_infos, _ = _reset_env(env)
    assert player_infos[0][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._smallblind + env._bigblind
    assert community_infos[community_table.TO_ACT_POS] == 0

    # BTN shoves
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 100])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == env._bigblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind * 100
    assert community_infos[community_table.POT] == env._bigblind * 101
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 1

    # BB calls
    s, r, d, i = _step(env, [action_table.CALL, 0])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert d == True
    assert player_infos[0][player_table.STACK] + player_infos[1][player_table.STACK] == env._bigblind * 200
    assert round(sum(r), 2) == (env._bigblind + env._smallblind) / env._bigblind
    assert abs(i['money_won']) == 100 * env._bigblind or abs(i['money_won']) == 50 * env._bigblind # in case of split-pot
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == 0
    assert community_infos[community_table.POT] == env._bigblind * 200
    assert community_infos[community_table.BUTTON_POS] == 0

    # Reset environment to play next hand
    player_infos, _, community_infos, _ = _reset_env(env)
    assert community_infos[community_table.BUTTON_POS] == 1 # Previous BB is now BTN/SB
    assert community_infos[community_table.TO_ACT_POS] == 1 # SB/BTN acts first heads-up
    assert player_infos[0][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._smallblind + env._bigblind

def test_custom_stacks():
    # 4 different stacks
    env = TexasHoldemEnv(4)
    env.add_player(0, stack=env._bigblind * 500)
    env.add_player(1, stack=env._bigblind * 40)
    env.add_player(2, stack=env._bigblind * 100)
    env.add_player(3, stack=env._bigblind * 10)
    player_infos, _, _, _ = _reset_env(env)
    assert player_infos[1][player_table.STACK] == env._bigblind * 500 # BTN
    assert player_infos[2][player_table.STACK] == env._bigblind * 40 - env._smallblind
    assert player_infos[3][player_table.STACK] == env._bigblind * 99
    assert player_infos[0][player_table.STACK] == env._bigblind * 10

    # 3 players, last one has bigger stack
    env = TexasHoldemEnv(3, all_in_equity_reward=True)
    env.add_player(0, stack=env._bigblind * 50)
    env.add_player(1, stack=env._bigblind * 50)
    env.add_player(2, stack=env._bigblind * 80)
    player_infos, _, _, community_cards = _reset_env(env)
    assert community_cards == [-1, -1, -1, -1, -1]
    assert player_infos[0][player_table.STACK] == env._bigblind * 50 # BTN
    assert player_infos[1][player_table.STACK] == env._bigblind * 50 - env._smallblind
    assert player_infos[2][player_table.STACK] == env._bigblind * 79

    # BTN shoves
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 50])
    player_infos, _, community_infos, community_cards = _unpack_state(s)
    assert r == [0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert community_cards == [-1, -1, -1, -1, -1]
    assert player_infos[0][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert player_infos[2][player_table.CURRENT_BET] == env._bigblind * 50
    assert community_infos[community_table.POT] == env._bigblind * 51 + env._smallblind
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 1

    # SB calls
    s, r, d, i = _step(env, [action_table.CALL, env._bigblind * 50])
    player_infos, _, community_infos, community_cards = _unpack_state(s)
    assert r == [0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert community_cards == [-1, -1, -1, -1, -1]
    assert player_infos[0][player_table.CURRENT_BET] == env._bigblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind * 50
    assert player_infos[2][player_table.CURRENT_BET] == env._bigblind * 50
    assert community_infos[community_table.POT] == env._bigblind * 101
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 2

    # BB calls all in and has stack left
    s, r, d, i = _step(env, [action_table.CALL, env._bigblind * 50])
    player_infos, _, community_infos, community_cards = _unpack_state(s)
    assert d == True # Hand ends since only one player has stack left
    assert round(sum(r), 2) == 1.4
    assert community_cards == [-1, -1, -1, -1, -1]
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == 0
    assert player_infos[2][player_table.CURRENT_BET] == 0
    assert community_infos[community_table.POT] == env._bigblind * 150
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 2



def test_turn_passes_fold_and_all_in():
    # 4 Players
    env = TexasHoldemEnv(4, all_in_equity_reward=True)
    env.add_player(0, stack=env._bigblind * 100)
    env.add_player(1, stack=env._bigblind * 100)
    env.add_player(2, stack=env._bigblind * 40)
    env.add_player(3, stack=env._bigblind * 100)
    player_infos, _, community_infos, _ = _reset_env(env)
    assert player_infos[0][player_table.STACK] == env._bigblind * 100
    assert player_infos[1][player_table.STACK] == env._bigblind * 100
    assert player_infos[2][player_table.STACK] == env._bigblind * 100 - env._smallblind
    assert player_infos[3][player_table.STACK] == env._bigblind * 39
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == 0
    assert player_infos[2][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[3][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._smallblind + env._bigblind
    assert community_infos[community_table.TO_ACT_POS] == 3

    # CO bets 50 bb (leaves 50 bb behind), BTN to act
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 50])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[2][player_table.CURRENT_BET] == env._bigblind
    assert player_infos[3][player_table.CURRENT_BET] == env._bigblind * 50
    assert community_infos[community_table.POT] == env._bigblind * 51 + env._smallblind
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 0

    # BTN flats (leaves 50 bb behind), SB to act
    s, r, d, i = _step(env, [action_table.CALL, 0])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert player_infos[2][player_table.CURRENT_BET] == env._bigblind * 50
    assert player_infos[3][player_table.CURRENT_BET] == env._bigblind * 50
    assert community_infos[community_table.POT] == env._bigblind * 101 + env._smallblind
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 1

    # SB folds, BB to act
    s, r, d, i = _step(env, [action_table.FOLD, 0])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert community_infos[community_table.TO_ACT_POS] == 2
    assert player_infos[3][player_table.IS_IN_POT] == 0 # SB folded
    assert player_infos[0][player_table.CURRENT_BET] == env._bigblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind * 50
    assert player_infos[2][player_table.CURRENT_BET] == env._bigblind * 50
    assert player_infos[3][player_table.CURRENT_BET] == env._smallblind
    assert community_infos[community_table.POT] == env._bigblind * 101 + env._smallblind
    assert community_infos[community_table.BUTTON_POS] == 0

    # BB calls 40 bb and is all in in sidepot, CO to act first on flop (others all in or folded)
    s, r, d, i = _step(env, [action_table.CALL, 0])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert sum(env._side_pots) == community_infos[community_table.POT]
    assert community_infos[community_table.TO_ACT_POS] == 3
    assert player_infos[2][player_table.IS_IN_POT] == 0 # SB folded
    assert player_infos[3][player_table.IS_IN_POT] == 1 # BB allin
    assert player_infos[3][player_table.HAS_ACTED] == 1 # BB allin - should have acted automatically
    assert player_infos[0][player_table.STACK] == env._bigblind * 50 # CO
    assert player_infos[1][player_table.STACK] == env._bigblind * 50
    assert player_infos[2][player_table.STACK] == env._bigblind * 100 - env._smallblind
    assert player_infos[3][player_table.STACK] == 0
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == 0
    assert player_infos[2][player_table.CURRENT_BET] == 0
    assert player_infos[3][player_table.CURRENT_BET] == 0
    assert community_infos[community_table.POT] == env._bigblind * 140 + env._smallblind
    assert community_infos[community_table.BUTTON_POS] == 0

    # CO shoves 50 bb, BTN to act
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 50])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert sum(env._side_pots) == community_infos[community_table.POT] - env._bigblind * 50 # Should it be this way?
    assert r == [0, 0, 0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == 0
    assert player_infos[2][player_table.CURRENT_BET] == 0
    assert player_infos[3][player_table.CURRENT_BET] == env._bigblind * 50
    assert community_infos[community_table.POT] == env._bigblind * 190 + env._smallblind
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 0

    # BTN folds
    s, r, d, i = _step(env, [action_table.FOLD, 0])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert community_infos[community_table.TO_ACT_POS] == 0 # BTN to act
    assert community_infos[community_table.POT] == env._bigblind * 190 + env._smallblind
    assert sum(env._side_pots) == 0
    assert player_infos[0][player_table.STACK] == env._bigblind * 50
    assert player_infos[1][player_table.STACK] == env._bigblind * 100 - env._smallblind
    assert player_infos[2][player_table.STACK] + player_infos[3][player_table.STACK] == env._bigblind * 190 + env._smallblind
    assert sum([player[player_table.STACK] for player in player_infos]) == env._bigblind * 340
    assert r[0] == -50
    assert r[1] == 0
    assert round(r[2] + r[3]) == 51
    assert round(sum(r), 2) == (env._bigblind + env._smallblind) / env._bigblind
    assert d == True
    assert i['money_won'] == -50 * env._bigblind
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == 0
    assert player_infos[2][player_table.CURRENT_BET] == 0
    assert player_infos[3][player_table.CURRENT_BET] == 0
    assert community_infos[community_table.BUTTON_POS] == 0

def test_check_on_big_blind():
    # 2 Players
    env = _create_env(2)
    player_infos, _, community_infos, _ = _reset_env(env)
    assert player_infos[0][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._smallblind + env._bigblind
    assert community_infos[community_table.TO_ACT_POS] == 0
    
    # SB/BTN calls
    s, r, d, i = _step(env, [action_table.CALL, 0])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert sum(env._side_pots) == 0
    assert player_infos[0][player_table.CURRENT_BET] == env._bigblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._bigblind * 2
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 1
    
    # BB checks
    s, r, d, i = _step(env, [action_table.CHECK, 0])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [0, 0]
    assert d == False
    assert i['money_won'] == 0
    assert sum(env._side_pots) == community_infos[community_table.POT]
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == 0
    assert community_infos[community_table.POT] == env._bigblind * 2
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
    assert community_infos[community_table.POT] == env._bigblind * 3
    assert community_infos[community_table.BUTTON_POS] == 0
    assert community_infos[community_table.TO_ACT_POS] == 0

    # SB/BTN folds
    s, r, d, i = _step(env, [action_table.FOLD, 0])
    player_infos, _, community_infos, _ = _unpack_state(s)
    assert r == [-(env._bigblind - env._smallblind) / env._bigblind, (env._bigblind * 2) / env._bigblind] # Stack change in big blinds
    assert d == True
    assert i['money_won'] == -env._bigblind
    assert player_infos[0][player_table.CURRENT_BET] == 0
    assert player_infos[1][player_table.CURRENT_BET] == 0
    assert community_infos[community_table.POT] == env._bigblind * 3
    assert community_infos[community_table.BUTTON_POS] == 0

    # Reset environment to play next hand
    player_infos, _, community_infos, _ = _reset_env(env)
    assert player_infos[0][player_table.CURRENT_BET] == env._smallblind
    assert player_infos[1][player_table.CURRENT_BET] == env._bigblind
    assert community_infos[community_table.POT] == env._smallblind + env._bigblind
    assert community_infos[community_table.BUTTON_POS] == 1 # Previous BB is now BTN/SB
    assert community_infos[community_table.TO_ACT_POS] == 1 # SB/BTN acts first heads-up

def test_blind_stealing():
    for n_players in range(2, 11):
        env = _create_env(n_players)

        # BTN steals, others fold
        player_infos, _, community_infos, _ = _reset_env(env)
        done = False
        iters = 0
        while not done:
            iters += 1
            our_turn = community_infos[community_table.TO_ACT_POS] == 0
            if our_turn:
                move = [action_table.RAISE, 2 * env._bigblind]
            else:
                move = [action_table.FOLD, 0]
            s, r, done, i = _step(env, move)
            player_infos, _, community_infos, _ = _unpack_state(s)
            expected_reward = [0] * n_players
            if done:
                btn_pos = 0
                expected_reward[btn_pos] = (env._smallblind + env._bigblind) / env._bigblind
                assert i['money_won'] == (env._bigblind if n_players == 2 else env._bigblind + env._smallblind)
                # BTN==SB has won bb unless > 2 players, then BTN==BTN and won sb+bb
                assert player_infos[0][player_table.STACK] == 101 * env._bigblind + (0 if n_players == 2 else  env._smallblind)
                # BTN+1==SB has lost sb unless 2 players, then BTN+1==BB lost bb
                assert player_infos[1][player_table.STACK] == (99 * env._bigblind if n_players == 2 else 100 * env._bigblind - env._smallblind)
                # BTN+2==BB has lost bb unless 2 players, then BTN+2==BTN won sb
                assert player_infos[2%n_players][player_table.STACK] == (99 * env._bigblind if n_players > 2 else 101 * env._bigblind)
            else:
                assert i['money_won'] == 0
            assert r == expected_reward
        assert iters == n_players

        # CO steals, others fold
        player_infos, _, community_infos, _ = _reset_env(env)
        done = False
        iters = 0
        while not done:
            iters += 1
            our_turn = community_infos[community_table.TO_ACT_POS] == 0
            if our_turn:
                move = [action_table.RAISE, 2 * env._bigblind]
            else:
                move = [action_table.FOLD, 0]
            s, r, done, i = _step(env, move)
            player_infos, _, community_infos, _ = _unpack_state(s)
            expected_reward = [0] * n_players
            if done:
                expected_reward[0] = (env._smallblind + env._bigblind) / env._bigblind
                assert i['money_won'] == \
                    (env._smallblind if n_players <= 3 else env._bigblind + env._smallblind)
                # CO==BB has won sb unless >3 players, then CO==CO and won sb+bb
                assert player_infos[0][player_table.STACK] == \
                    100 * env._bigblind + (env._smallblind if n_players <= 3 else env._bigblind + env._smallblind)
                # CO+1==SB lost sb if 2 players, else CO+1==BTN and folds
                assert player_infos[1][player_table.STACK] == \
                    (100 * env._bigblind - env._smallblind if n_players == 2 else 100 * env._bigblind)
            else:
                assert i['money_won'] == 0
            assert r == expected_reward
        assert iters == n_players - (1 if n_players <= 3 else 0)

        # HJ steals, others fold
        player_infos, _, community_infos, _ = _reset_env(env)
        done = False
        iters = 0
        while not done:
            iters += 1
            our_turn = community_infos[community_table.TO_ACT_POS] == 0
            if our_turn:
                move = [action_table.RAISE, 2 * env._bigblind]
            else:
                move = [action_table.FOLD, 0]
            s, r, done, i = _step(env, move)
            player_infos, _, community_infos, _ = _unpack_state(s)
            expected_reward = [0] * n_players
            if done:
                expected_reward[0] = (env._smallblind + env._bigblind) / env._bigblind
                assert n_players == n_players and i['money_won'] == \
                    (env._bigblind if n_players <= 3 else (env._smallblind if n_players == 4 else env._bigblind + env._smallblind))
                # HJ==SB has won bb if <4 players, if 4 players HJ==BB and wins sb, else HJ==HJ and won sb+bb
                assert n_players == n_players and player_infos[0][player_table.STACK] == \
                    100 * env._bigblind + \
                        (env._bigblind if n_players <= 3 else (env._smallblind if n_players == 4 else env._bigblind + env._smallblind))
                # HJ+1==BB lost bb if <4 players, else HJ+1==CO and folds
                assert n_players == n_players and player_infos[1][player_table.STACK] == \
                    (100 * env._bigblind - (env._bigblind if n_players <= 3 else 0))
            else:
                assert i['money_won'] == 0
            assert r == expected_reward
        assert iters == n_players - (1 if n_players == 4 else 0)

        # MP steals, others fold
        player_infos, _, community_infos, _ = _reset_env(env)
        done = False
        iters = 0
        while not done:
            iters += 1
            our_turn = community_infos[community_table.TO_ACT_POS] == 0
            if our_turn:
                move = [action_table.RAISE, 2 * env._bigblind]
            else:
                move = [action_table.FOLD, 0]
            s, r, done, i = _step(env, move)
            player_infos, _, community_infos, _ = _unpack_state(s)
            expected_reward = [0] * n_players
            if done:
                assert n_players == n_players and \
                    community_infos[community_table.POT] == \
                        (env._smallblind if n_players != 4 else 0) + env._bigblind * (1 if (n_players == 2 or n_players == 5) else 3)
                expected_reward[0] = (env._smallblind + env._bigblind) / env._bigblind
                # MP==BB has won sb if 2 or 5 players, if 3 players MP==BTN and wins sb+bb, if 4 players MP==BB and wins bb, else MP==MP and won sb+bb
                assert n_players == n_players and player_infos[0][player_table.STACK] == \
                    100 * env._bigblind + \
                        (env._smallblind if (n_players == 2 or n_players == 5) else (env._bigblind if n_players == 4 else env._bigblind + env._smallblind))
                # MP+1==SB lost bb if <3 players, else HJ+1==CO and folds
                assert n_players == n_players and player_infos[1][player_table.STACK] == \
                    (100 * env._bigblind - (env._smallblind if n_players <= 3 else (env._bigblind if n_players == 4 else 0)))
                assert n_players == n_players and i['money_won'] == \
                    (env._smallblind if (n_players == 2 or n_players == 5) else (env._bigblind if n_players == 4 else env._bigblind + env._smallblind))
            else:
                assert i['money_won'] == 0
            assert r == expected_reward
        assert iters == n_players - (1 if (n_players == 2 or n_players == 5) else 0)

def test_card_dealing():
    # 2 Players
    env = _create_env(2)
    _, player_hands, _, community_cards = _reset_env(env)
    assert player_hands[0][0] != -1 and player_hands[0][1] != -1
    assert player_hands[1][0] != -1 and player_hands[1][1] != -1
    assert community_cards == [-1, -1, -1, -1, -1]
    
    # SB/BTN minraises
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 2])
    _, player_hands, _, community_cards = _unpack_state(s)
    assert player_hands[0][0] != -1 and player_hands[0][1] != -1
    assert player_hands[1][0] != -1 and player_hands[1][1] != -1
    assert community_cards == [-1, -1, -1, -1, -1]
    
    # BB calls
    s, r, d, i = _step(env, [action_table.CALL, 0])
    _, player_hands, _, community_cards = _unpack_state(s)
    assert player_hands[0][0] != -1 and player_hands[0][1] != -1
    assert player_hands[1][0] != -1 and player_hands[1][1] != -1
    assert community_cards[3:] == [-1, -1]
    assert community_cards[0] != -1 and community_cards[1] != -1 and community_cards[2] != -1

    # FLOP
    # BB minbets
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind])
    _, player_hands, _, community_cards = _unpack_state(s)
    assert player_hands[0][0] != -1 and player_hands[0][1] != -1
    assert player_hands[1][0] != -1 and player_hands[1][1] != -1
    assert community_cards[3:] == [-1, -1]
    assert community_cards[0] != -1 and community_cards[1] != -1 and community_cards[2] != -1

    # SB/BTN folds
    s, r, d, i = _step(env, [action_table.FOLD, 0])
    _, player_hands, _, community_cards = _unpack_state(s)
    assert player_hands[0][0] != -1 and player_hands[0][1] != -1
    assert player_hands[1][0] != -1 and player_hands[1][1] != -1
    assert community_cards[3:] == [-1, -1]
    assert community_cards[0] != -1 and community_cards[1] != -1 and community_cards[2] != -1

    # Reset environment to play next hand
    _, player_hands, _, community_cards = _reset_env(env)
    assert player_hands[0][0] != -1 and player_hands[0][1] != -1
    assert player_hands[1][0] != -1 and player_hands[1][1] != -1
    assert community_cards == [-1, -1, -1, -1, -1]

    # SB folds
    s, r, d, i = _step(env, [action_table.FOLD, 0])
    _, player_hands, _, community_cards = _unpack_state(s)
    assert player_hands[0][0] != -1 and player_hands[0][1] != -1
    assert player_hands[1][0] != -1 and player_hands[1][1] != -1
    assert community_cards == [-1, -1, -1, -1, -1]

    # Reset environment to play next hand
    _, player_hands, _, community_cards = _reset_env(env)
    assert player_hands[0][0] != -1 and player_hands[0][1] != -1
    assert player_hands[1][0] != -1 and player_hands[1][1] != -1
    assert community_cards == [-1, -1, -1, -1, -1]
    
    # SB/BTN minraises
    s, r, d, i = _step(env, [action_table.RAISE, env._bigblind * 2])
    _, player_hands, _, community_cards = _unpack_state(s)
    assert player_hands[0][0] != -1 and player_hands[0][1] != -1
    assert player_hands[1][0] != -1 and player_hands[1][1] != -1
    assert community_cards == [-1, -1, -1, -1, -1]
    
    # BB folds
    s, r, d, i = _step(env, [action_table.FOLD, 0])
    _, player_hands, _, community_cards = _unpack_state(s)
    assert player_hands[0][0] != -1 and player_hands[0][1] != -1
    assert player_hands[1][0] != -1 and player_hands[1][1] != -1
    assert community_cards == [-1, -1, -1, -1, -1]


### test calling with less than 1bb left

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
    s, r, d, i = env.step(actions)
    assert round(sum(r), 2) == (((env._bigblind + env._smallblind) / env._bigblind) if d else 0) # Sum of rewards need to be sum of blinds in big blinds
    return s, r, d, i