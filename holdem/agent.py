import random
import numpy as np
from keras.models import Sequential
from keras.layers.core import Dense
from keras.optimizers import Adam

#random.seed(0)


class DQNAgent():
    def __init__(self, epsilon=1.0, alpha=0.5, gamma=0.9, time=30000):
        self.action_size = 4    # Check, call, raise by 50, fold
        self.input_shape = 3    # Equity, stack, pot
        self.epsilon = epsilon  # Random exploration factor
        self.alpha = alpha      # Learning factor
        self.gamma = gamma      # Discount factor- closer to 1 learns well into distant future
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.99
        self.learning = True
        self.model = self._build_model()

        self.time = time
        self.time_left = time  # Epsilon Decay
        self.small_decrement = (0.4 * epsilon) / (0.3 * self.time_left)  # reduce epsilon

    def _build_model(self):
        model = Sequential()
        model.add(Dense(32, input_shape=(self.input_shape,),
                  kernel_initializer='random_uniform', activation='relu'))
        model.add(Dense(16, activation='relu'))
        model.add(Dense(self.action_size, activation='softmax'))
        model.compile(loss='binary_crossentropy',
                      optimizer=Adam(lr=self.alpha))
        return model

    def choose_action(self, state):
        """
        Choose which action to take, based on the observation.
        Uses greedy epsilon for exploration/exploitation.
        """
        if np.random.rand() <= self.epsilon:
            action = random.randrange(self.action_size)
        else:
            action_value = self.model.predict(state)
            action = np.argmax(action_value[0])
        self.update_parameters()
        return action

    def update_parameters(self):
        """
        Update epsilon and alpha after each action
        Set them to 0 if not learning
        """
        if self.time_left > 0.9 * self.time:
            self.epsilon -= self.small_decrement
        elif self.time_left > 0.7 * self.time:
            self.epsilon -= self.small_decrement
        elif self.time_left > 0.5 * self.time:
            self.epsilon -= self.small_decrement
        elif self.time_left > 0.3 * self.time:
            self.epsilon -= self.small_decrement
        elif self.time_left > 0.1 * self.time:
            self.epsilon -= self.small_decrement
        self.time_left -= 1

    def learn(self, state, action, reward, next_state, terminal):
        target = reward
        if not terminal:
            target = reward + self.gamma * np.amax(self.model.predict(next_state)[0])
        target_f = self.model.predict(state)
        target_f[0][action] = target
        self.model.fit(state, target_f, epochs=1, verbose=0)
