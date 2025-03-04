# -*- coding: utf-8 -*-
#
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
from enum import IntEnum

from treys import Card


class action_table(IntEnum):
    CHECK = 0
    CALL = 1
    RAISE = 2
    FOLD = 3
    NA = 0


class community_table(IntEnum):
    BUTTON_POS = 0
    SMALL_BLIND = 1
    BIG_BLIND = 2
    POT = 3
    LAST_RAISE = 4
    MINRAISE = 5
    TO_CALL = 6
    TO_ACT_POS = 7


class player_table(IntEnum):
    CURRENT_BET = 0
    STACK = 1
    IS_IN_POT = 2
    HAS_ACTED = 3
    IS_ALL_IN = 4
    LAST_SIDEPOT = 5
    ID = 6


def format_action(player, action):
    color = False
    try:
        from termcolor import colored
        # for mac, linux: http://pypi.python.org/pypi/termcolor
        # can use for windows: http://pypi.python.org/pypi/colorama
        color = True
    except ImportError:
        pass
    [aid, raise_amt] = action
    if aid == action_table.CHECK:
        text = '_ check'
        if color:
            text = colored(text, 'white')
        return text
    if aid == action_table.CALL:
        text = '- call, current bet: {}'.format(player.currentbet)
        if color:
            text = colored(text, 'yellow')
        return text
    if aid == action_table.RAISE:
        text = '^ raise, current bet: {}'.format(raise_amt)
        if color:
            text = colored(text, 'green')
        return text
    if aid == action_table.FOLD:
        text = 'x fold'
        if color:
            text = colored(text, 'red')
        return text


def card_to_str(card):
    if card == -1:
        return ''
    return Card.int_to_pretty_str(card)


def hand_to_str(hand):
    output = " "
    for i in range(len(hand)):
        c = hand[i]
        if c == -1:
            if i != len(hand) - 1:
                output += '[  ],'
            else:
                output += '[  ] '
            continue
        if i != len(hand) - 1:
            output += str(Card.int_to_pretty_str(c)) + ','
        else:
            output += str(Card.int_to_pretty_str(c)) + ' '
    return output


def safe_action(current_player, to_call, n_seats):
    return ([action_table.CALL, action_table.NA] if to_call > 0
            else [action_table.CHECK, action_table.NA])
