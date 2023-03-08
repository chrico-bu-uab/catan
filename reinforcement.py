import matplotlib.pyplot as plot
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

import catan


device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Using {device}.")

torch.random.manual_seed(0)


class Network(nn.Module):
    """
    A neural network that takes in the current state's aggregate statistics
    and outputs a label representing the action the agent should take.
    """

    def __init__(self, input_size, output_size):
        """
        Initializes the neural network.

        :param input_size: The number of aggregate statistics.
        :param output_size: The number of actions.
        """
        super().__init__()

        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, output_size)

    def forward(self, x):
        """
        Performs a forward pass through the neural network.

        :param x: The input to the neural network.
        :return: The output of the neural network.
        """
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = nn.Softmax(dim=0)(self.fc3(x))

        return x


class ReinforcementAgent:
    """
    A reinforcement learning agent that uses a neural network to learn the best moves to make given aggregate statistics
    about the game's current state.

    The agent is initialized with a neural network that takes in the current state's aggregate statistics and outputs an
    action. The agent then uses the neural network to play the game and learns the best actions to take.

    The agent is trained using the Q-learning algorithm. The agent is given a reward for reaching the goal and a penalty
    for dying. The agent then uses the reward and penalty to update the weights of the neural network.
    """

    def __init__(self):
        """
        Initializes the agent with a neural network.
        """
        self.network = Network(46, 6).to(device)
        self.optimizer = optim.NAdam(self.network.parameters(), lr=1e-4)
        self.loss_function = nn.CrossEntropyLoss(label_smoothing=0.1)
        self.losses = []

        self.states = []
        self.actions = []
        self.rewards = []

        self.final_turns = []

    def get_action(self, state):
        """
        Gets the action the agent should take given the current state.

        :param state: The current state of the game.
        :return: The action the agent should take.
        """
        return self.network(torch.flatten(torch.tensor(state).to(torch.float32).to(device))).detach().cpu().numpy()

    def train(self, states, actions, rewards, final_turn):
        """
        Trains the agent using the Q-learning algorithm.

        :param states: The states the agent was in when it took the actions.
        :param actions: The actions the agent took.
        :param rewards: The rewards the agent received for taking the actions.
        :param final_turn: The turn the game ended on.
        """
        states = torch.stack([torch.tensor(state).to(torch.float32).to(device) for state in states])
        actions = torch.stack([torch.tensor(action).to(torch.long).to(device) for action in actions])
        rewards = torch.stack([torch.tensor(reward).to(torch.float32).to(device) for reward in rewards])
        self.optimizer.zero_grad()
        loss = 0
        for state, action, reward in zip(states, actions, rewards):
            output = self.network(state)
            target = output.clone()
            target[action] = reward
            loss += self.loss_function(output, target)
        loss.backward()
        self.optimizer.step()
        self.losses.append(loss.item())
        self.rewards.append(rewards.mean().item())
        self.final_turns.append(final_turn)

    def plot(self):
        """
        Plots the agent's losses and rewards.
        """
        plot.figure()
        plot.subplot(3, 1, 1)
        plot.plot(self.losses)
        plot.ylabel('Loss')
        plot.subplot(3, 1, 2)
        plot.plot(self.rewards)
        plot.ylabel('Reward')
        plot.subplot(3, 1, 3)
        plot.plot(self.final_turns)
        plot.xlabel('Epoch')
        plot.ylabel('turns')
        plot.show()


def main():
    """
    Trains the agent to play the game.
    """
    agent = ReinforcementAgent()

    # Train the agent.
    for epoch in range(1000):
        ARGS = [[], [], []]
        final_turns = []
        for _ in range(5):
            game = catan.Board()
            game.setup(agent)
            states, actions, rewards = game.play()
            ARGS[0].extend(states)
            ARGS[1].extend(actions)
            ARGS[2].extend(rewards)
            final_turns.append(game.final_turn)
        agent.train(*ARGS, sum(final_turns) / 5)
        agent.plot()
        print(f"Epoch: {epoch}")

    # Save the agent's neural network.
    torch.save(agent.network.state_dict(), 'reinforcement.pth')


if __name__ == '__main__':
    main()
