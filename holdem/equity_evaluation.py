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

from treys import Card, Deck, Evaluator

class Equity():
    def __init__(self, n_evaluations=100):
        self.n_evaluations = n_evaluations
        self.evaluator = Evaluator()

    def get_equities(self, hands, community, deck):
        victories = np.zeros(len(hands))
        for i in range(self.n_evaluations):
            cur_community = community.copy()
            cur_deck = deck.copy()
            added_cards = np.random.choice(cur_deck, size=(5 - len(cur_community)), replace=False).tolist()
            cur_community += added_cards
            ranks = [self.evaluator.evaluate(hand, cur_community) for hand in hands]
            winners = ranks == np.min(ranks)
            victories[winners] += 1 / winners.sum()
        equities = victories / self.n_evaluations
        assert abs(equities.sum() - 1) < 1e-6
        return equities

if __name__ == '__main__':
    deck = Deck()
    equity = Equity()
    card1, card2, card3, card4 = deck.draw(4)
    cards = [[card1, card2], [card3, card4]]
    board = []
    equities = equity.get_equities(cards, board, deck.cards)
    Card.print_pretty_card
    print(Card.print_pretty_card(card1), Card.print_pretty_card(card2), 'VS', Card.print_pretty_card(card3), Card.print_pretty_card(card4))
    print(equities)