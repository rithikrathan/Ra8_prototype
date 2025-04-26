# Working on the fetch unit:


1) A mealy finite state machine is used to push the instruction into the pipeline 
    and the immediate values into the pipeline registers.
    <br> 
    >The transition between states is given by:

        | currentState | condition | nextState |
        | --- | --- | --- |
        | 1 | X | 0 |
        | 0 | 0 | 1 |
        | 0 | 1 | 0 |

    >This design has a problem, when designing I considered 1 as the initial state and it pushed the the instructions and immediate values from the fetch register into their corresponding path but practically the initial state will always be 0 for this circuit so this takes one additional circuit to transition from 0 - 1 based on the above table with the condition c (Value of c is set to 0 initially).

    >So any instructins without any immediate values will still go into the pipeline normally but the next instruction is pushed into the pipeline registers instead of going into the pipeling and its next instruction is pushed into the pipeline, this oscillates back and forth if all the instructions have no immediate values.

    >I'm too lazy to identify the problem(i know the problem but too lazy to explain it)

## In short, if the input instruction does not followed by any immediate values is 2 MSBs are 00 then the state machine oscillates between 0 and 1 instead of being at constant 1, which is the only problem and it seems to handle other conditions perfectly as I expected

Also I dont know how the .md files work  
