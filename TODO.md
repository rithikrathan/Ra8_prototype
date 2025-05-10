# Working on the fetch unit:

added the delay and insertNOPE signal and its now working and now have to work on the insert nope instruction that is used to 
handle the pipeline when a b-type instruction is passed ad it may result in a branch and changes the PC value 
so the fetch unit must not get the instructions and immediate values from the old PC address

Problem:
    the the b-type instructions are followed by immediate values that gives the address to branch, those address must load into 
    the pipeline register but the folowing instructions should not, this is a problem because
    as soon as the last byte of the address in loaded into the register the next instruction is loaded into the fetch register 
    in the same cycle, so i have to somehow set the insertNOPE signal in the fetch unit [I've already added the insert nope 
    signal and its working also must test it if it works when the first instruction is a b-type instruction]

^^^^^
dont worry about this. you still dont know how the instructions behave so its not right to design something that needs to be changed everytime you make changes to the instructions set

first work on increment program counter signal and the ready signal from the fetch unit then we can worry about pipeline hazards.
once you did that then test it with the programm counter, instruction memeory and some data registers to make sure it works perfectly.
we will take care of pipeline hazards later now assume the ideal pipeline behaviour and proceed to design

