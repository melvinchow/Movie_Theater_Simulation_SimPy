# Movie_Theater_Simulation_SimPy
simulating employee capacities and customer wait queues

This is an enhancement to the simPy sample code found here: ["Simulating Real-World Processes With SimPy."](https://realpython.com/simulation-with-simpy/)

I found the original code to be lacking in detail.  It only gave out one final result (average wait time).
I could not see what was happening in the middle of movie theater operations from the perspective of the employees or the guests.  So I added more lines to declare events taking place and how long wait times and queues grow or decrease.

The simulation (created by executing one of the .py files) saves the event log into CSV files

After simulation, the python notebooks (ipynb) creates time series graphs visualizing the queue lines and changing capacities of the movie theatre staff.

Sidenote: different revisions to the simulation script were made in order to capture detail in the CSVs necessary for what I wanted to portray in the time series graphs.



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
