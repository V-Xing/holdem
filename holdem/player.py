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

from gym import error


class Player(object):

    CHECK = 0
    CALL = 1
    RAISE = 2
    FOLD = 3

    def __init__(self, player_id, stack=2500, emptyplayer=False):
        self.player_id = player_id

        self.hand = []
        self.stack = stack
        self.starting_stack = stack
        self.hand_starting_stack = stack
        self.currentbet = 0
        self.lastsidepot = 0
        self._seat = -1
        self.handrank = -1
        self.blind = 0

        self.equity = 0

        # flags for table management
        self.emptyplayer = emptyplayer
        self.isallin = False
        self.playing_hand = False
        self.playedthisround = False
        # not used at the moment, but might become useful in the future
        self.sitting_out = False

    @property
    def max_bet(self):
        return self.currentbet + self.stack

    def get_seat(self):
        return self._seat

    def set_seat(self, value):
        self._seat = value

    def reset_hand(self):
        self._hand = []
        self.playedthisround = False
        self.isallin = False
        self.currentbet = 0
        self.lastsidepot = 0
        self.blind = 0
        self.hand_starting_stack = self.stack
        self.playing_hand = (self.stack != 0)

    def declare_action(self, bet_size):
        self.playedthisround = True
        if not bet_size:
            return
        self.stack -= (bet_size - self.currentbet)
        self.currentbet = bet_size
        if self.stack == 0:
            self.isallin = True

    def post_blind(self, amount):
        self.hand_starting_stack -= amount
        self.blind = amount
        self.playedthisround = False

    def refund(self, amount):
        self.stack += amount

    def player_state(self):
        return (self.get_seat(), self.stack, self.playing_hand, self.player_id)

    def reset_stack(self, amount=None):
        if amount is None:
            self.stack = self.starting_stack
        else:
            self.stack = amount

    def validate_action(self, tocall, minraise, action):
        tocall = min(tocall, self.max_bet)

        [action_idx, raise_amount] = action
        raise_amount = int(raise_amount)
        action_idx = int(action_idx)

        if tocall == 0:
            assert action_idx in [Player.CHECK, Player.RAISE]
            if action_idx == Player.RAISE:
                if raise_amount < minraise:
                    raise error.Error(
                        'raise must be at least minraise {}'.format(minraise))
                if raise_amount > self.max_bet:
                    raise error.Error(
                        'raise must be at most maxraise {}'.format(self.max_bet))
                move_tuple = ('raise', raise_amount)
            elif action_idx == Player.CHECK:
                move_tuple = ('check', self.currentbet)
            else:
                raise error.Error(
                    'invalid action ({}) must be check (0) or raise (2)'.format(action_idx))
        else:
            if action_idx not in [Player.RAISE, Player.CALL, Player.FOLD]:
                raise error.Error(
                    'invalid action ({}) must be raise (2), call (1), or fold (3)'.format(action_idx))
            if action_idx == Player.RAISE:
                if raise_amount < minraise:
                    raise error.Error(
                        'raise must be at least minraise {}'.format(minraise))
                if raise_amount > self.max_bet:
                    raise error.Error(
                        'raise must be at most maxraise {}'.format(self.max_bet))
                move_tuple = ('raise', raise_amount)
            elif action_idx == Player.CALL:
                move_tuple = ('call', min(tocall, self.max_bet))
            elif action_idx == Player.FOLD:
                move_tuple = ('fold', self.currentbet)
        return move_tuple
