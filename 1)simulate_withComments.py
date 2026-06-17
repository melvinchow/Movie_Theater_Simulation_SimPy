"""Companion code to https://realpython.com/simulation-with-simpy/

'Simulating Real-World Processes With SimPy'

Python version: 3.7.3
SimPy version: 3.0.11

Version notes: same as original from realpython.com, but with comments added
"""

# Import random to introduce variability in service times, mimicking real-world unpredictability
import random
# Import statistics to compute the mean of collected wait times at the end
import statistics
# Import simpy, the discrete-event simulation library that drives the entire simulation
import simpy

# Global list that accumulates each moviegoer's total wait time so we can analyze results later
wait_times = []


# The Theater class models the physical theater and its limited staff (shared resources)
class Theater(object):
    # Constructor: receives the simpy environment and the number of each type of employee
    def __init__(self, env, num_cashiers, num_servers, num_ushers):
        # Store a reference to the simulation environment so processes can schedule events
        self.env = env
        # Create a simpy Resource for cashiers — only num_cashiers moviegoers can buy tickets at once;
        # others must queue. This is how SimPy models limited-capacity resources.
        self.cashier = simpy.Resource(env, num_cashiers)
        # Create a simpy Resource for food servers — limits how many can be served food simultaneously
        self.server = simpy.Resource(env, num_servers)
        # Create a simpy Resource for ushers — limits how many tickets can be checked at once
        self.usher = simpy.Resource(env, num_ushers)

    # A process that simulates the time it takes one cashier to sell a ticket to one moviegoer
    def purchase_ticket(self, moviegoer):
        # Pause this process for a random duration between 1 and 3 minutes,
        # representing the variability in how long a ticket purchase takes.
        # yield is what makes this a SimPy process — it hands control back to the simulation clock.
        yield self.env.timeout(random.randint(1, 3))

    # A process that simulates the time it takes one usher to check a moviegoer's ticket
    def check_ticket(self, moviegoer):
        # Pause for 3 seconds (3/60 of a minute) — ticket checking is fast and consistent,
        # so there's no randomness here
        yield self.env.timeout(3 / 60)

    # A process that simulates the time it takes one server to sell food to a moviegoer
    def sell_food(self, moviegoer):
        # Pause for a random duration between 1 and 5 minutes,
        # representing the variability in food orders (a drink vs. a full combo, etc.)
        yield self.env.timeout(random.randint(1, 5))


# This generator function defines the full journey of a single moviegoer through the theater.
# It's the core "process" that each moviegoer follows in the simulation.
def go_to_movies(env, moviegoer, theater):
    # Record the simulation clock time when this moviegoer arrives — used later to calculate total wait
    arrival_time = env.now

    # Request access to a cashier. The "with" block ensures the resource is released when done.
    # If all cashiers are busy, this moviegoer waits in a FIFO queue automatically.
    with theater.cashier.request() as request:
        # yield request pauses this process until a cashier becomes available
        yield request
        # Once a cashier is free, run the purchase_ticket process and wait for it to finish
        yield env.process(theater.purchase_ticket(moviegoer))

    # After buying a ticket, request access to an usher for ticket checking
    with theater.usher.request() as request:
        # Wait in queue until an usher is free
        yield request
        # Run the ticket-checking process and wait for it to complete
        yield env.process(theater.check_ticket(moviegoer))

    # Simulate that roughly 50% of moviegoers decide to buy food (coin flip)
    if random.choice([True, False]):
        # If they want food, request access to a food server
        with theater.server.request() as request:
            # Wait in queue until a server is free
            yield request
            # Run the food-selling process and wait for it to complete
            yield env.process(theater.sell_food(moviegoer))

    # The moviegoer has completed all steps and heads into the theater.
    # Calculate total time from arrival to now (includes all queuing + service time)
    # and append it to the global list for later analysis.
    wait_times.append(env.now - arrival_time)


# This generator function orchestrates the entire theater simulation —
# it creates the theater, seeds it with initial moviegoers, and continuously generates new arrivals.
def run_theater(env, num_cashiers, num_servers, num_ushers):
    # Instantiate the Theater with the given staff numbers, creating the shared resources
    theater = Theater(env, num_cashiers, num_servers, num_ushers)

    # Start with 3 moviegoers already present when the simulation begins (the initial "seed" crowd)
    for moviegoer in range(3):
        # Register each moviegoer's journey as a separate process in the simulation engine.
        # All 3 start at time 0, so they compete for resources right away.
        env.process(go_to_movies(env, moviegoer, theater))

    # After the initial batch, continuously generate new moviegoers for the rest of the simulation
    while True:
        # Wait 0.20 minutes (12 seconds) of simulation time before the next person arrives.
        # This controls the arrival rate — a key parameter in queuing theory.
        yield env.timeout(0.20)  # Wait a bit before generating a new person

        # Increment the moviegoer counter to give each person a unique ID
        moviegoer += 1
        # Launch this new moviegoer's journey as its own concurrent process
        env.process(go_to_movies(env, moviegoer, theater))


# Utility function: takes the list of recorded wait times and returns a human-readable average
def get_average_wait_time(wait_times):
    # Compute the arithmetic mean of all wait times (in minutes, as floats)
    average_wait = statistics.mean(wait_times)
    # Split the average into whole minutes and the fractional remainder
    # e.g., 4.75 becomes minutes=4, frac_minutes=0.75
    minutes, frac_minutes = divmod(average_wait, 1)
    # Convert the fractional minutes into seconds (0.75 * 60 = 45 seconds)
    seconds = frac_minutes * 60
    # Return rounded whole numbers for clean display
    return round(minutes), round(seconds)


# Collects user input from the terminal to configure how many staff members the theater has
def get_user_input():
    # Prompt the user for the number of cashiers and store as a string
    num_cashiers = input("Input # of cashiers working: ")
    # Prompt for number of food servers
    num_servers = input("Input # of servers working: ")
    # Prompt for number of ushers
    num_ushers = input("Input # of ushers working: ")
    # Bundle all inputs into a list for validation
    params = [num_cashiers, num_servers, num_ushers]
    # Validate that every input is a positive integer (digits only)
    if all(str(i).isdigit() for i in params):  # Check input is valid
        # Convert the validated string inputs to integers
        params = [int(x) for x in params]
    else:
        # If any input is invalid, warn the user and fall back to safe defaults
        print(
            "Could not parse input. Simulation will use default values:",
            "\n1 cashier, 1 server, 1 usher.",
        )
        # Default configuration: 1 of each staff type (will likely cause long queues)
        params = [1, 1, 1]
    # Return the list of 3 integers [cashiers, servers, ushers]
    return params


# The main entry point that ties everything together: setup → run → report
def main():
    # Seed the random number generator so results are reproducible across runs.
    # With the same seed (42), every "random" service time and food decision will be identical.
    random.seed(42)
    # Get staff configuration from the user via terminal input
    num_cashiers, num_servers, num_ushers = get_user_input()

    # Create a new SimPy simulation environment — this is the clock and event scheduler
    env = simpy.Environment()
    # Register the run_theater generator as a process, which kicks off the simulation logic
    env.process(run_theater(env, num_cashiers, num_servers, num_ushers))
    # Run the simulation until the clock reaches 90 minutes, then stop.
    # All processes that haven't completed by minute 90 are simply abandoned.
    env.run(until=90)

    # After the simulation ends, compute and display the average wait time
    mins, secs = get_average_wait_time(wait_times)
    print(
        "Running simulation...",
        f"\nThe average wait time is {mins} minutes and {secs} seconds.",
    )


# Standard Python idiom: only run main() if this file is executed directly (not imported as a module)
if __name__ == "__main__":
    main()