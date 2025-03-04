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

from enum import IntEnum

from gym import Env, error, spaces, utils
from gym.utils import seeding

from treys import Deck, Evaluator

from .player import Player
from .utils import hand_to_str, format_action, community_table, player_table
from .equity_evaluation import Equity


class Street(IntEnum):
    NOT_STARTED = 0
    PREFLOP = 1
    FLOP = 2
    TURN = 3
    RIVER = 4
    SHOWDOWN = 5


class TexasHoldemEnv(Env, utils.EzPickle):
    BLIND_INCREMENTS = [[10, 25], [25, 50], [50, 100], [75, 150], [100, 200],
                        [150, 300], [200, 400], [300, 600], [
                            400, 800], [500, 10000],
                        [600, 1200], [800, 1600], [1000, 2000]]

    def __init__(self, n_seats, max_limit=100000, all_in_equity_reward=False,
                 equity_steps=100, autoreset_stacks=True, debug=False):
        # n_suits = 4                     # s,h,d,c
        # n_ranks = 13                    # 2,3,4,5,6,7,8,9,T,J,Q,K,A
        # n_pocket_cards = 2
        # n_stud = 5

        self.n_seats = n_seats

        self._blind_index = 0
        [self._smallblind, self._bigblind] = TexasHoldemEnv.BLIND_INCREMENTS[0]
        self._deck = Deck()
        self._evaluator = Evaluator()

        self.community = []
        self._dead_cards = []
        self._street = Street.NOT_STARTED
        self._button = -1

        self._side_pots = [0] * n_seats
        self._current_sidepot = 0  # index of _side_pots
        self._totalpot = 0
        self._tocall = 0
        self._lastraise = 0
        self._number_of_hands = 0
        self._current_bet = 0

        # fill seats with dummy players
        self._seats = [Player(i, stack=0, emptyplayer=True)
                       for i in range(n_seats)]
        self.emptyseats = n_seats
        self._player_dict = {}
        self._current_player = None
        self._debug = debug
        self._last_player = None
        self._last_action = None

        self.agent_exists = False

        self.equity_reward = all_in_equity_reward
        self.equity = Equity(n_evaluations=equity_steps)

        self._autoreset_stacks = autoreset_stacks

        # self.observation_space = spaces.Tuple([  # <--- This thing is totally broken!!!
        #     spaces.Tuple([                # players
        #         spaces.MultiDiscrete([
        #             1,                   # emptyplayer
        #             n_seats - 1,         # seat
        #             max_limit,           # stack
        #             1,                   # is_playing_hand
        #             max_limit,           # handrank
        #             1,                   # playedthisround
        #             1,                   # is_betting
        #             1,                   # isallin
        #             max_limit,           # last side pot
        #         ]),
        #         spaces.Tuple([
        #             spaces.MultiDiscrete([    # hand
        #                 # suit, can be negative one if it's not avaiable.
        #                 n_suits,
        #                 # rank, can be negative one if it's not avaiable.
        #                 n_ranks,
        #             ])
        #         ] * n_pocket_cards)
        #     ] * n_seats),
        #     spaces.Tuple([
        #         spaces.Discrete(n_seats - 1),  # big blind location
        #         spaces.Discrete(max_limit),   # small blind
        #         spaces.Discrete(max_limit),   # big blind
        #         spaces.Discrete(max_limit),   # pot amount
        #         spaces.Discrete(max_limit),   # last raise
        #         spaces.Discrete(max_limit),   # minimum amount to raise
        #         # how much needed to call by current player.
        #         spaces.Discrete(max_limit),
        #         spaces.Discrete(n_seats - 1),  # current player seat location.
        #         spaces.MultiDiscrete([        # community cards
        #             n_suits - 1,          # suit
        #             n_ranks - 1,          # rank
        #             1,                     # is_flopped
        #         ]),
        #     ] * n_stud),
        # ])
        # self.action_space = spaces.Tuple([
        #     spaces.MultiDiscrete([
        #         3,                     # action_id
        #         max_limit,             # raise_amount
        #     ]),
        # ] * n_seats)
        self.observation_space = spaces.Tuple([
                            spaces.Box(low=0.0, high=1.0, shape=(1,)),  # equity
                            spaces.Discrete(max_limit),  # stack
                            spaces.Discrete(max_limit),  # pot amount
                            ])

        self.action_space = spaces.MultiDiscrete([3, max_limit])

    @property
    def current_player_id(self):
        return self._current_player.player_id

    @property
    def tocall(self):
        return self._tocall

    def seed(self, seed=None):
        _, seed = seeding.np_random(seed)
        return [seed]

    def add_player(self, seat_id, stack=2500, is_agent=False):
        """Add a player to the environment seat with the given stack (chipcount)"""
        player_id = seat_id
        if player_id not in self._player_dict:
            if is_agent:
                if self.agent_exists:
                    raise error.Error('Agent already exists')
                self.agent_exists = True
                self.agent_id = player_id
            new_player = Player(player_id, stack=stack, emptyplayer=False)
            if self._seats[player_id].emptyplayer:
                self._seats[player_id] = new_player
                new_player.set_seat(player_id)
            else:
                raise error.Error('Seat already taken.')
            self._player_dict[player_id] = new_player
            self.emptyseats -= 1

    def remove_player(self, seat_id):
        """Remove a player from the environment seat."""
        player_id = seat_id
        try:
            idx = self._seats.index(self._player_dict[player_id])
            self._seats[idx] = Player(-1, stack=0, emptyplayer=True)
            del self._player_dict[player_id]
            self.emptyseats += 1
        except ValueError:
            pass

    def reset(self):
        self._reset_game()
        self._number_of_hands += 1
        [self._smallblind, self._bigblind] = TexasHoldemEnv.BLIND_INCREMENTS[0]
        if len(self._player_dict) >= 2:
            players = self._playing_players
            self._reset_street_state()
            self._current_player = self._first_to_act(players)
            self._last_player = self._current_player
            self._post_smallblind(self._current_player)
            self._pass_move_to_next_player()
            self._post_bigblind(self._current_player)
            self._pass_move_to_next_player()
            self._tocall = self._bigblind
            self._folded_players = []
            self._deal_next_street()
        return self._get_current_reset_returns()

    def step(self, action):
        """
        CHECK = 0
        CALL = 1
        RAISE = 2
        FOLD = 3

        RAISE_AMT = [0, minraise]
        """
        if self._current_player is None:
            raise error.Error(
                'Round cannot be played without 2 or more players.')

        if self._street == Street.SHOWDOWN:
            raise error.Error('Rounds already finished, needs to be reset.')

        players = self._playing_players
        if len(players) <= 1:
            raise error.Error(
                'Round cannot be played with one or less players.')

        if not any([p.isallin is False for p in players]):
            raise error.Error('Eveyone all in, round should be finished')

        if self._current_player.isallin:
            raise error.Error(
                'This should never happen, position to act should pass players'
                'that can\'t take any actions')

        self._current_player.equity = self._compute_my_equity(self._current_player)
        self._last_action = action

        move = self._current_player.validate_action(
            self._tocall, self._minraise, action)
        if self._debug:
            print('Player', self._current_player.player_id, move)
        self._player_action(self._current_player, move[1])
        if move[0] == 'raise':
            for p in players:
                if p != self._current_player and not p.isallin:
                    p.playedthisround = False
        self._pass_move_to_next_player()
        if move[0] == 'fold':
            self._dead_cards += self._last_player.hand
            self._last_player.playing_hand = False
            players.remove(self._last_player)
            self._folded_players.append(self._last_player)

        not_acted_players = [
            player for player in players if not player.playedthisround]
        all_but_one_all_in = sum(
            [player.isallin for player in players]) >= len(players) - 1
        street_done = all([player.playedthisround for player in players]) \
            or (len(not_acted_players) == 1
                and not_acted_players[0].currentbet >= self._tocall
                and all_but_one_all_in)

        ready_for_showdown = (len(players) > 1
                              and all_but_one_all_in
                              and street_done)

        if ready_for_showdown:
            if self.equity_reward:
                self._street = Street.SHOWDOWN
            else:
                while self._street < Street.SHOWDOWN:
                    self._deal_next_street()

        if street_done:
            self._resolve_street(players)

        terminal = False
        if self._street == Street.SHOWDOWN or len(players) == 1:
            terminal = True
            self._resolve_hand(players)

        return self._get_current_step_returns(terminal)

    def _compute_equities(self, players):
        return self.equity.get_equities([p.hand for p in players],
                                        self.community, self._deck.cards,
                                        self._dead_cards)

    def _compute_my_equity(self, player):
        return self.equity.get_my_equity([player.hand], len(self._seats),
                                         self.community, self._deck.cards)

    def render(self, mode='human', close=False):
        for p in self._playing_players:
            p.equity = self._compute_my_equity(p)

        print('\ntotal pot: {}'.format(self._totalpot))
        if self._last_action is not None:
            pid = self._last_player.player_id
            print('last action by player {}:'.format(pid))
            print(format_action(self._last_player, self._last_action))

        (player_states, community_states) = self._get_current_state()
        (player_infos, player_hands) = zip(*player_states)
        (community_infos, community_cards) = community_states
        blinds_idxs = self._get_blind_indexes(community_infos)

        print('community:')
        print('-' + hand_to_str(community_cards))
        print('players:')
        for idx, hand in enumerate(player_hands):
            idx_relative = (
                idx + self._current_player.player_id) % len(self._seats)
            position_string = self._get_blind_str(blinds_idxs, idx_relative)
            folded = "F" if not player_infos[idx][player_table.IS_IN_POT] else " "
            print('{} {} {}{}stack: {}, equity: {}'.format(idx_relative,
                  position_string, folded, hand_to_str(hand),
                  self._seats[idx_relative].stack,
                  self._seats[idx_relative].equity))

    def _get_blind_str(self, blinds_idxs, idx):
        if idx == blinds_idxs[0]:
            return "SB"
        elif idx == blinds_idxs[1]:
            return "BB"
        else:
            return "  "

    def _get_blind_indexes(self, community_infos):
        idx = community_infos[community_table.BUTTON_POS]
        # If more than 2 players playing, SB is next from BTN, else BTN is SB
        if len([s for s in self._seats if not s.sitting_out and not s.emptyplayer]) > 2:
            idx = (idx + 1) % len(self._seats)
        sb_idx = -1
        while True:
            while self._seats[idx].sitting_out or self._seats[idx].emptyplayer:
                idx = (idx + 1) % len(self._seats)
            if sb_idx == -1:
                sb_idx = idx
            else:
                return (sb_idx, idx)
            idx = (idx + 1) % len(self._seats)

    def _resolve_street(self, players):
        self._current_player = self._first_to_act(players)
        self._resolve_sidepots(players + self._folded_players)
        if self._street < Street.SHOWDOWN and len(players) > 1:
            self._reset_street_state()
            self._deal_next_street()

    def _deal_next_street(self):
        if self._street == Street.NOT_STARTED:
            self._deal()
        elif self._street == Street.PREFLOP:
            self._flop()
        elif self._street == Street.FLOP:
            self._turn()
        elif self._street == Street.TURN:
            self._river()
        self._street += 1

    def _increment_blinds(self):
        self._blind_index = min(self._blind_index + 1,
                                len(TexasHoldemEnv.BLIND_INCREMENTS) - 1)
        [self._smallblind, self._bigblind] = TexasHoldemEnv.BLIND_INCREMENTS[self._blind_index]

    def _post_smallblind(self, player):
        if self._debug:
            print('player ', player.player_id, 'small blind', self._smallblind)
        self._player_action(player, min(player.stack, self._smallblind))
        player.post_blind(self._smallblind)

    def _post_bigblind(self, player):
        if self._debug:
            print('player ', player.player_id, 'big blind', self._bigblind)
        self._player_action(player, min(player.stack, self._bigblind))
        player.post_blind(self._bigblind)
        self._lastraise = self._bigblind
        if self._debug:
            print('total pot: {}'.format(self._totalpot))

    def _player_action(self, player, total_bet):
        self._current_bet = max(total_bet, self._current_bet)
        extra_from_player_bet = total_bet - player.currentbet
        relative_bet = total_bet - self._last_player.currentbet
        player.declare_action(total_bet)

        self._totalpot += extra_from_player_bet
        self._tocall = max(self._tocall, total_bet)
        if self._tocall > 0:
            self._tocall = max(self._tocall, self._bigblind)

        self._lastraise = max(self._lastraise, relative_bet)

    def _reset_street_state(self):
        for player in self._player_dict.values():
            player.currentbet = 0
            if not player.isallin:
                player.playedthisround = False
        self._tocall = 0
        self._lastraise = 0
        self._current_bet = 0
        if self._debug:
            print('totalpot', self._totalpot)

    @property
    def _playing_players(self):
        return [p for p in self._seats if p.playing_hand]

    def _pass_move_to_next_player(self):
        self._last_player = self._current_player
        self._current_player = self._next(
            self._playing_players, self._current_player)

    def _first_to_act(self, players):
        players = sorted(
            set(players + [self._seats[self._button]]), key=lambda x: x.get_seat())
        if self._street == Street.NOT_STARTED and len(players) == 2:
            return self._seats[self._button]
        else:
            return self._next(players, self._seats[self._button])

    def _next(self, players, current_player):
        players = [p for p in players if not p.isallin or p is current_player]
        idx = players.index(current_player)
        return players[(idx+1) % len(players)]

    def _deal(self):
        for player in self._seats:
            if player.playing_hand:
                player.hand = self._deck.draw(2)

    def _flop(self):
        self.community = self._deck.draw(3)

    def _turn(self):
        self.community.append(self._deck.draw(1))

    def _river(self):
        self.community.append(self._deck.draw(1))

    def _resolve_sidepots(self, players_playing):
        players = [p for p in players_playing if p.currentbet]
        if self._debug:
            print('current bets: ', [p.currentbet for p in players])
            print('playing hand: ', [p.playing_hand for p in players])
        if not players:
            return
        try:
            smallest_bet = min(
                [p.currentbet for p in players if p.playing_hand])
        except ValueError:
            for p in players:
                self._side_pots[self._current_sidepot] += p.currentbet
                p.currentbet = 0
            return

        smallest_players_allin = [p for p, bet in
                                  zip(players, [p.currentbet for p in players])
                                  if bet == smallest_bet and p.isallin]

        for p in players:
            self._side_pots[self._current_sidepot] += min(
                smallest_bet, p.currentbet)
            p.currentbet -= min(smallest_bet, p.currentbet)
            p.lastsidepot = self._current_sidepot

        if smallest_players_allin:
            self._current_sidepot += 1
            self._resolve_sidepots(players)
        assert sum(self._side_pots) == self._totalpot
        if self._debug:
            print('sidepots: ', self._side_pots)

    def _resolve_hand(self, players):
        if len(players) == 1:
            # Everyone else folded
            if self._debug:
                print('Refunding, sum(sidepots) %s, totalpot %s' %
                      (str(sum(self._side_pots)), str(self._totalpot)))
            players[0].refund(self._totalpot)
        else:
            # trim side_pots to only include the non-empty side pots
            temp_pots = [pot for pot in self._side_pots if pot > 0]

            if self.equity_reward and len(self.community) < 5:
                for pot_idx, _ in enumerate(temp_pots):
                    # find players involved in given side_pot, compute the equities and pot split
                    pot_contributors = [
                        p for p in players if p.lastsidepot >= pot_idx]
                    if len(pot_contributors) > 1:
                        equities = self.equity.get_equities(
                            [p.hand for p in pot_contributors], self.community,
                            self._deck.cards, self._dead_cards)
                        amount_distributed = 0
                        for p_idx, player in enumerate(pot_contributors):
                            split_amount = int(
                                round(self._side_pots[pot_idx] * equities[p_idx]))
                            if self._debug:
                                print('Player', player.player_id,
                                      'wins side pot (', split_amount, ')')
                            player.refund(split_amount)
                            amount_distributed += split_amount
                    else:
                        amount_distributed = int(self._side_pots[pot_idx])
                        pot_contributors[0].refund(amount_distributed)
                    self._side_pots[pot_idx] -= amount_distributed

                    # any remaining chips after splitting go to the winner in the earliest position
                    if self._side_pots[pot_idx]:
                        earliest = self._first_to_act(
                            [player for player in pot_contributors])
                        earliest.refund(self._side_pots[pot_idx])
            else:
                # compute hand ranks
                for player in players:
                    player.handrank = self._evaluator.evaluate(
                        player.hand, self.community)

                # compute who wins each side pot and pay winners
                for pot_idx, _ in enumerate(temp_pots):
                    # find players involved in given side_pot, compute the winner(s)
                    pot_contributors = [
                        p for p in players if p.lastsidepot >= pot_idx]
                    winning_rank = min([p.handrank for p in pot_contributors])
                    winning_players = [
                        p for p in pot_contributors if p.handrank == winning_rank]

                    for player in winning_players:
                        split_amount = int(
                            self._side_pots[pot_idx]/len(winning_players))
                        if self._debug:
                            print('Player', player.player_id, 'wins side pot (', int(
                                self._side_pots[pot_idx]/len(winning_players)), ')')
                        player.refund(split_amount)
                        self._side_pots[pot_idx] -= split_amount

                    # any remaining chips after splitting go to the winner in the earliest position
                    if self._side_pots[pot_idx]:
                        earliest = self._first_to_act(
                            [player for player in winning_players])
                        earliest.refund(self._side_pots[pot_idx])

    def _reset_game(self):
        self._street = Street.NOT_STARTED
        playing = 0
        for player in self._seats:
            if not player.emptyplayer and not player.sitting_out:
                if self._autoreset_stacks:
                    player.reset_stack()
                player.reset_hand()
                playing += 1
        self.community = []
        self._dead_cards = []
        self._current_sidepot = 0
        self._totalpot = 0
        self._last_action = None
        self._side_pots = [0] * len(self._seats)
        self._deck.shuffle()

        if playing:
            self._button = (self._button + 1) % len(self._seats)
            while not self._seats[self._button].playing_hand:
                self._button = (self._button + 1) % len(self._seats)

    @property
    def _minraise(self):
        minraise = min(self._current_bet + self._lastraise,
                       self._current_player.max_bet)
        return max(minraise, self._current_bet + 1)

    def _pad(self, l, n, v):
        if (not l) or (l is None):
            l = []
        return l + [v] * (n - len(l))

    def _get_current_player_state(self, player):
        return (self._compute_my_equity(player), player.stack, self._totalpot)

    def _get_current_state(self):
        player_states = []
        n_players = len(self._seats)
        for i in range(self._current_player.player_id,
                       self._current_player.player_id + n_players):
            player = self._seats[i % n_players]
            player_features = [
                int(player.currentbet),
                int(player.stack),
                int(player.equity),
                int(player.playing_hand),
                int(player.playedthisround),
                int(player.isallin),
                int(player.lastsidepot),
                int(player.player_id),
            ]
            player_states.append(
                (player_features, self._pad(player.hand, 2, -1)))
        community_states = ([
            int(self._button),
            int(self._smallblind),
            int(self._bigblind),
            int(self._totalpot),
            int(self._lastraise),
            int(self._minraise),
            int(self._tocall),
            int(self._current_player.player_id),
        ], self._pad(self.community, 5, -1))
        return (tuple(player_states), community_states)

    def _get_current_reset_returns(self):
        observation, _, _, _ = self._get_current_step_returns(terminal=False)
        return observation, self._get_current_state()

    def _get_current_step_returns(self, terminal):
        agent = self._seats[self.agent_id]
        observation = self._get_current_player_state(agent)
        reward = ((agent.stack - agent.hand_starting_stack) / self._bigblind
                  if terminal else 0)
        info = {}
        info['money_won'] = agent.stack - \
            (agent.hand_starting_stack + agent.blind) if terminal else 0
        return observation, reward, terminal, info
