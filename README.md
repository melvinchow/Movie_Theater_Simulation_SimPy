# Movie_Theater_Simulation_SimPy
simulating employee capacities and customer wait queues

This is an enhancement to the simPy sample code found here: ["Simulating Real-World Processes With SimPy."](https://realpython.com/simulation-with-simpy/)

I found the original results hard to interpret and follow, since it only outputs a few end result summary metrics.

I modified the script to generate a CSV file that outputs what happens during the movie theater's operations every 15 seconds.

Using this CSV, visualizations are made (shown in the ipynb) to show how busy each team in the movie theater gets while the theater is open.

The visualizations would show when the cashier and food teams are operating at capacity, if lines get too long, or if it takes too long for customers to be processed from the time they arrive at the theater, to when they get into their seats.

Some additional behavioral scenarios can be added in the future to make this simulation more realistic:
1) Small % chance a customer leaves and goes home after becoming impatient in the long line
2) Small % chance of an outlier food team disaster that holds back everyone's food
3) Cashier needs the bathroom but there are no replacement cashiers to cover for him/her

Use the HTMLs as alternatives for viewing the time series graphs if the ipynb doesnt work for you.

## Running the Script

The file `simulate.py` contains the script that mimics the tutorial code. You can execute the code by running `python3 simulate.py` from the directory that contains the file.

Here is some sample output:

```console
$ python3 simulate.py
Input # of cashiers working: 1
Input # of servers working: 1
Input # of ushers working: 1
Running simulation...
The average wait time is 42 minutes and 26 seconds.
```
