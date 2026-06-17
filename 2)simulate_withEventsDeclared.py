"""
Enhanced Theater Simulation with Verbose Event Logging
Based on: https://realpython.com/simpy-simulating-with-python/

This version prints every event as it happens so you can follow
exactly what's going on inside the simulation at each moment.
"""

import random
import statistics
import simpy


# ANSI color codes for readable terminal output
class Color:
    ARRIVAL  = "\033[96m"   # Cyan     — new arrivals
    CASHIER  = "\033[93m"   # Yellow   — cashier events
    USHER    = "\033[95m"   # Magenta  — usher events
    FOOD     = "\033[92m"   # Green    — food server events
    DONE     = "\033[94m"   # Blue     — moviegoer enters theater
    QUEUE    = "\033[90m"   # Gray     — waiting in line
    RESET    = "\033[0m"    # Reset


wait_times = []


def fmt_time(minutes):
    """Convert simulation minutes to a readable MM:SS string."""
    m, frac = divmod(minutes, 1)
    return f"{int(m):02d}:{int(frac * 60):02d}"


def log(env, color, msg):
    """Print a timestamped, color-coded event."""
    print(f"  [{fmt_time(env.now)}] {color}{msg}{Color.RESET}")


class Theater:
    def __init__(self, env, num_cashiers, num_servers, num_ushers):
        self.env = env
        self.cashier = simpy.Resource(env, num_cashiers)
        self.server = simpy.Resource(env, num_servers)
        self.usher = simpy.Resource(env, num_ushers)

    def purchase_ticket(self, moviegoer):
        duration = random.randint(1, 3)
        log(self.env, Color.CASHIER,
            f"💳 Cashier starts selling ticket to Moviegoer #{moviegoer} "
            f"(will take {duration} min)")
        yield self.env.timeout(duration)
        log(self.env, Color.CASHIER,
            f"🎟️  Moviegoer #{moviegoer} has their ticket!")

    def check_ticket(self, moviegoer):
        log(self.env, Color.USHER,
            f"🔍 Usher checking Moviegoer #{moviegoer}'s ticket (3 sec)")
        yield self.env.timeout(3 / 60)
        log(self.env, Color.USHER,
            f"✅ Moviegoer #{moviegoer}'s ticket checked!")

    def sell_food(self, moviegoer):
        duration = random.randint(1, 5)
        log(self.env, Color.FOOD,
            f"🍿 Server starts food order for Moviegoer #{moviegoer} "
            f"(will take {duration} min)")
        yield self.env.timeout(duration)
        log(self.env, Color.FOOD,
            f"🥤 Moviegoer #{moviegoer} got their food!")


def go_to_movies(env, moviegoer, theater):
    arrival_time = env.now
    log(env, Color.ARRIVAL,
        f"🚶 Moviegoer #{moviegoer} arrives at the theater")

    # --- CASHIER STAGE ---
    queue_len = len(theater.cashier.queue)
    if queue_len > 0:
        log(env, Color.QUEUE,
            f"   ⏳ Moviegoer #{moviegoer} joins cashier line "
            f"({queue_len} already waiting)")

    with theater.cashier.request() as request:
        yield request
        yield env.process(theater.purchase_ticket(moviegoer))

    # --- USHER STAGE ---
    queue_len = len(theater.usher.queue)
    if queue_len > 0:
        log(env, Color.QUEUE,
            f"   ⏳ Moviegoer #{moviegoer} joins usher line "
            f"({queue_len} already waiting)")

    with theater.usher.request() as request:
        yield request
        yield env.process(theater.check_ticket(moviegoer))

    # --- FOOD STAGE (50% chance) ---
    wants_food = random.choice([True, False])
    if wants_food:
        queue_len = len(theater.server.queue)
        log(env, Color.FOOD,
            f"🍿 Moviegoer #{moviegoer} decides to buy food!")
        if queue_len > 0:
            log(env, Color.QUEUE,
                f"   ⏳ Moviegoer #{moviegoer} joins food line "
                f"({queue_len} already waiting)")

        with theater.server.request() as request:
            yield request
            yield env.process(theater.sell_food(moviegoer))
    else:
        log(env, Color.QUEUE,
            f"   Moviegoer #{moviegoer} skips food, heading straight in")

    # --- DONE ---
    total_wait = env.now - arrival_time
    wait_times.append(total_wait)
    log(env, Color.DONE,
        f"🎬 Moviegoer #{moviegoer} enters the theater! "
        f"(total time: {fmt_time(total_wait)})")
    print()  # blank line for readability


def run_theater(env, num_cashiers, num_servers, num_ushers):
    theater = Theater(env, num_cashiers, num_servers, num_ushers)

    # Seed with 3 initial moviegoers
    for moviegoer in range(3):
        env.process(go_to_movies(env, moviegoer, theater))

    while True:
        yield env.timeout(0.20)
        moviegoer += 1
        env.process(go_to_movies(env, moviegoer, theater))


def get_average_wait_time(wait_times):
    average_wait = statistics.mean(wait_times)
    minutes, frac_minutes = divmod(average_wait, 1)
    seconds = frac_minutes * 60
    return round(minutes), round(seconds)


def get_user_input():
    num_cashiers = input("Input # of cashiers working: ")
    num_servers = input("Input # of servers working: ")
    num_ushers = input("Input # of ushers working: ")
    params = [num_cashiers, num_servers, num_ushers]
    if all(str(i).isdigit() for i in params):
        params = [int(x) for x in params]
    else:
        print(
            "Could not parse input. Simulation will use default values:",
            "\n1 cashier, 1 server, 1 usher.",
        )
        params = [1, 1, 1]
    return params


def main():
    random.seed(42)
    num_cashiers, num_servers, num_ushers = get_user_input()

    print(f"\n{'='*60}")
    print(f"  THEATER SIMULATION")
    print(f"  Staff: {num_cashiers} cashier(s), {num_servers} server(s), "
          f"{num_ushers} usher(s)")
    print(f"  Duration: 90 minutes")
    print(f"{'='*60}\n")

    env = simpy.Environment()
    env.process(run_theater(env, num_cashiers, num_servers, num_ushers))
    env.run(until=90)

    print(f"{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    mins, secs = get_average_wait_time(wait_times)
    print(f"  Moviegoers served: {len(wait_times)}")
    print(f"  Average wait time: {mins} min {secs} sec")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()