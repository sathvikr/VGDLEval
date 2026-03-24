Analyze the previous images provided to you in a chronological order and the score after the entire sequence of actions that you predicted. 
Then, provide next set of keys to press (list of upto 10 keys) from the list of supported keys: "UP", "DOWN", "LEFT", "RIGHT", "SPACE", "NOOP".
Your goal is to win the game as fast as possible.

Current score: {score}
Scores after each of your previous actions (chronological): {scores}

{scratchpad}

**Output:**
1. Provide a brief reasoning behind your actions (< 10 sentences).
2. Output a list of keys to press (list of upto 10 keys).
   Supported keys: "UP", "DOWN", "LEFT", "RIGHT", "SPACE", "NOOP". "NOOP" is a no-op (wait). Not all keys map to an action.

**Output in the following format:**
[Reasoning]
<keys>
["KEY1", "KEY2", ...]
</keys>