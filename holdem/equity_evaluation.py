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

import numpy as np
from multiprocessing.pool import ThreadPool
from multiprocessing import cpu_count
from threading import Thread

from treys import Card, Deck, Evaluator

import os
import ctypes
import ctypes.util
import sys

if sys.platform.startswith('win'):
    pbots_calc = "pbots_calc"
elif sys.platform.startswith('darwin'):
    pbots_calc = "libpbots_calc.dylib"
else:
    pbots_calc = "libpbots_calc.so"


class _Results(ctypes.Structure):
    _fields_ = [("ev", ctypes.POINTER(ctypes.c_double)),
                ("hands", ctypes.POINTER(ctypes.c_char_p)),
                ("iters", ctypes.c_int),
                ("size", ctypes.c_int),
                ("MC", ctypes.c_int)]


use_c_backend = True

try:
    pcalc = ctypes.CDLL(pbots_calc)
    # Set the argtype and return types from the library.
    pcalc.calc.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                           ctypes.c_int, ctypes.POINTER(_Results)]
    pcalc.calc.restype = ctypes.c_int
    pcalc.alloc_results.argtypes = []
    pcalc.alloc_results.restype = ctypes.POINTER(_Results)
    pcalc.free_results.argtypes = [ctypes.POINTER(_Results)]
    pcalc.free_results.restype = None
except OSError:
    print("ERROR: Could not locate %s. Please ensure your enviroment library load path is set properly." % pbots_calc)
    print('Using slow Python hand equity evaluation as a fallback')
    use_c_backend = False


class Results:
    def __init__(self, res):
        self.size = res.size
        self.MC_used = res.MC
        self.iters = res.iters
        self.ev = []
        self.hands = []
        for i in range(self.size):
            self.ev.append(res.ev[i])
            self.hands.append(res.hands[i])

    def __str__(self):
        return str(zip(self.hands, self.ev))


def calc(hands, board, dead, iters):
    res = pcalc.alloc_results()
    err = pcalc.calc(hands, board, dead, iters, res)
    if err > 0:
        results = Results(res[0])
    else:
        print("error: could not parse input or something...")
        results = None
    pcalc.free_results(res)
    return results


class Equity():
    def __init__(self, n_evaluations=500):
        self.evaluator = Evaluator()
        self.n_evaluations = n_evaluations

    def get_equities(self, hands, community, deck, dead):
        if use_c_backend:
            return self._get_equities_c(hands, community, dead)
        else:
            return self._get_equities_python(hands, community, deck)

    def _get_equities_c(self, hands, community, dead):
        for i in range(len(hands)):
            hands[i] = ''.join([Card.int_to_str(hands[i][0]),
                                Card.int_to_str(hands[i][1])])
        community = [Card.int_to_str(h) for h in community]
        dead = [Card.int_to_str(h) for h in dead]
        hands = bytes(':'.join(hands), encoding='utf-8')
        community = bytes(''.join(community), encoding='utf-8')
        dead = bytes(''.join(dead), encoding='utf-8')
        results = calc(hands, b'', b'', self.n_evaluations)
        return results.ev

    def _get_equities_python(self, hands, community, deck):
        victories = np.zeros(len(hands))
        for _ in range(self.n_evaluations):
            cur_community = community.copy()
            cur_deck = deck.copy()
            added_cards = np.random.choice(cur_deck,
                                           size=(5 - len(cur_community)),
                                           replace=False).tolist()
            cur_community += added_cards
            ranks = [self.evaluator.evaluate(hand, cur_community) for hand in hands]
            winners = ranks == np.min(ranks)
            victories[winners] += 1 / winners.sum()
        equities = victories / self.n_evaluations
        assert abs(equities.sum() - 1) < 1e-6
        return equities

    def get_my_equity(self, my_hand, n_players, community, deck):
        victories = 0
        for _ in range(self.n_evaluations):
            cur_community = community.copy()
            cur_deck = deck.copy()
            hands = my_hand.copy()
            nb_add_comm = 5 - len(cur_community)
            # Pick cards for the community and for other players
            added_cards = np.random.choice(cur_deck,
                                           size=(nb_add_comm + 2*n_players),
                                           replace=False).tolist()
            # Add community cards
            cur_community += added_cards[:nb_add_comm]
            # Add cards for other players
            for i in range(n_players-1):
                hands.append(added_cards[nb_add_comm + 2*i:nb_add_comm + 2*(i+1)])
            # Compute ranks of each hand
            ranks = [self.evaluator.evaluate(hand, cur_community) for hand in hands]
            # Compute best hands (winners[i] == 1, ties can exist)
            winners = ranks == np.min(ranks)
            # If I won, increment number of victories
            if winners[0]:
                victories += 1 / winners.sum()
        return victories / self.n_evaluations

if __name__ == '__main__':
    deck = Deck()
    equity = Equity(1000)
    card1, card2, card3, card4 = deck.draw(4)
    dead = [card1, card2, card3, card4]
    cards = [[card1, card2], [card3, card4]]
    board = []

    import time

    start = time.time()
    equities = equity._get_equities_python(cards, board, deck.cards)
    print(Card.print_pretty_card(card1), Card.print_pretty_card(card2), 'VS', Card.print_pretty_card(card3), Card.print_pretty_card(card4))
    print(equities)
    print('Python takes %ss' % (time.time() - start,))

    start = time.time()
    equities = equity._get_equities_c(cards, board, dead)
    print(Card.print_pretty_card(card1), Card.print_pretty_card(card2), 'VS', Card.print_pretty_card(card3), Card.print_pretty_card(card4))
    print(equities)
    print('C takes %ss' % (time.time() - start,))
