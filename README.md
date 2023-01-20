I used an arduino uno, attach a relay switch to pin 4.

run run.bat

have fun :^D

If it stops working sometimes you need to replug and restart.

If it connects but stops working mid usage you need to go inside 
Arduino/Relay/relay.ino change the x values to new ones. Then go inside
runOneMachine.py and mirror the values in the arduino function's run_machine(). line 32.

Since the requirements of each machine differs I did't create easily changeable values.