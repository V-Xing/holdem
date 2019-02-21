# holdem

## Installation

```sh
git clone https://github.com/VinQbator/holdem.git
```

```sh
cd holdem
pip install .
```

It is also highly recommended to install https://github.com/mitpokerbots/pbots_calc to get a fast C backend for Monte Carlo simulations ( Make sure to add the library to LD_LIBRARY_PATH, which is not said in the instructions)

## Description

This is the first [OpenAI Gym](https://github.com/openai/gym) _No-Limit Texas Hold'em_* (NLH)
environment written in Python. It's an experiment to build a Gym environment that is synchronous and
can support any number of players but also appeal to the general public that wants to learn how to
"solve" NLH.

*Python 3 supports arbitrary length integers :money_with_wings:

Right now, this is a work in progress, but I believe the API is mature enough for some preliminary
experiments. Join us in making some interesting progress on multi-agent Gym environments.

## Usage

There is limited documentation at the moment. I'll try to make this less painful to understand.

### `env = holdem.TexasHoldemEnv(n_seats, max_limit=100000, all_in_equity_reward=False, equity_steps=100, autoreset_stacks=True, debug=False)`

Creates a gym environment representation a NLH Table from the parameters:

+ `n_seats` - number of seats in table. No players are initially allocated to the table. You must call `env.add_player(seat_id, ...)` to populate the table.
+ `max_limit` - max_limit is used to define the `gym.spaces` API for the class. It does not actually determine any NLH limits; in support of `gym.spaces.Discrete`.
+ `all_in_equity_reward` - use Monte Carlo simulation to pay out winnings and rewards from environment based on equity in all in situations.
+ `equity_steps` - number of MC simulations to run to determine equity.
+ `autoreset_stacks` - reset stacks after every hand automatically.
+ `debug` - add debug statements to play, will probably be removed in the future.

### `env.add_player(seat_id, stack=2500)`

Adds a player to the table according to the specified seat (`seat_id`) and the initial amount of
chips allocated to the player's `stack`. If the table does not have enough seats according to the
`n_seats` used by the constructor, a `gym.error.Error` will be raised.

### `(player_states, community_states) = env.reset()`

Calling `env.reset` resets the NLH table to a new hand state. New behavior is reserved for a special, future portion of the API that is yet another feature that is not standard in Gym environments and is a work in progress.

The observation returned is a `tuple` of the following by index:

0. `player_states` - a `tuple` where each entry is `tuple(player_info, player_hand)`, this feature can be used to gather all states and hands by `(player_infos, player_hands) = zip(*player_states)`.
    + `player_infos` - is a `list` of `int` features describing the individual player. It can be conveniently accessed with `utils.player_table` like so `player_states[0][player_table.STACK]`. First index is always the player that needs to act now. It contains the following entries:

      + `CURRENT_BET` - `0` - seat is empty, `1` - seat is not empty.
      + `STACK` - player's current stack.
      + `IS_IN_POT` - player has cards.
      + `HAS_ACTED` - `0` - player has not played this round, `1` - player has played this round.
      + `IS_ALL_IN` - `0` - player is currently not all-in, `1` - player is all-in.
      + `LAST_SIDEPOT` - player's last sidepot.
  
  + `player_hands` - is a `list` of `int` features describing the cards in the player's pocket. The values are encoded based on the `treys.Card` integer representation.

1. `community_states` - a `tuple(community_infos, community_cards)` where:
   + `community_infos` - a `list` of public information common to everyone on the table. Positions here are absolute not indexes in players list (you can subtract TO_ACT_POS from BUTTON_POS to get button dealer player's index):
     
     + `BUTTON_POS` - location of the dealer button, where big blind is posted.
     + `SMALL_BLIND` - the current small blind amount.
     + `POT` - the current total amount in the community pot.
     + `LAST_RAISE` - the last posted raise amount.
     + `MINRAISE` - minimum required raise amount, if above 0.
     + `TO_CALL` - the amount required to call.
     + `TO_ACT_POS` - the current player required to take an action.

   + `community_cards` - is a `list` of `int` features describing the cards on board.
     The values are encoded based on the `treys.Card` integer representation. There are 5 `int` in
     the list, where `-1` represents that there is no card present.

# Example

Might be out of date.

```python
import gym
import holdem

def play_out_hand(env, n_seats):
  # reset environment, gather relevant observations
  (player_states, (community_infos, community_cards)) = env.reset()
  (player_infos, player_hands) = zip(*player_states)

  # display the table, cards and all
  env.render(mode='human')

  terminal = False
  while not terminal:
    # play safe actions, check when noone else has raised, call when raised.
    actions = holdem.safe_actions(community_infos, n_seats=n_seats)
    (player_states, (community_infos, community_cards)), rews, terminal, info = env.step(actions)
    env.render(mode='human')

env = gym.make('TexasHoldem-v1') # holdem.TexasHoldemEnv(2)

# start with 2 players
env.add_player(0, stack=2000) # add a player to seat 0 with 2000 "chips"
env.add_player(1, stack=2000) # add another player to seat 1 with 2000 "chips"
# play out a hand
play_out_hand(env, env.n_seats)

# add one more player
env.add_player(2, stack=2000) # add another player to seat 1 with 2000 "chips"
# play out another hand
play_out_hand(env, env.n_seats)
```
