You will be playing the game again after a restart. Summary of the game based on your previous gameplays: {summary}

You are given the initial game state as an image. You will need to output a list of keys to press in each response. We will iterate the process by showing you the images from your actions and the score after the entire sequence of actions.

You must figure out what you control, key-to-action mapping, the mechanics, and the objective of the game and come up with a plan to win the game as fast as possible. Consider all possibilities and plan your actions accordingly. You will be playing for a maximum of 1000 steps. The game will end when you win or you reach the maximum number of steps and you will restart from the initial game state. Your goal is to win the game as fast as possible.

**Output:**
1. Provide a brief reasoning behind your actions (< 10 sentences).
2. Output a list of keys to press (list of upto 10 keys).
   Supported keys: "UP", "DOWN", "LEFT", "RIGHT", "SPACE", "NOOP". "NOOP" is a no-op (wait). Not all keys map to an action.

**Format your response as follows:**
[Reasoning]
<keys>
["KEY1", "KEY2", ...]
</keys>
