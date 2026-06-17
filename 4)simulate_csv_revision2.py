"""
Theater Simulation with CSV Export for Time Series Analysis
Based on: https://realpython.com/simpy-simulating-with-python/

Exports a CSV with a row for every simulation event, capturing:
- Queue depths at each resource (cashier, usher, food server)
- Number of busy staff at each resource
- Cumulative moviegoers served
- Individual wait times as moviegoers finish

Use the companion Jupyter notebook to visualize the results.


REVISION 2: changes the CSV generation to export 2 files - one for per-event recording, one for time-based recording.
- Time based recording makes visualizations look smoother
"""

import csv
import random
import statistics
import simpy


# ---------------------------------------------------------------------------
# Data collector — records two types of data:
#   1. Event log:    a row every time something happens (for detailed analysis)
#   2. Time series:  a row at fixed intervals (for smooth, consistent charts)
# ---------------------------------------------------------------------------
class DataCollector:
    """Records event-level and time-sampled snapshots of theater state."""

    def __init__(self, sample_interval=0.25):
        self.event_rows = []        # irregular, driven by simulation events
        self.timeseries_rows = []   # regular, driven by a fixed clock
        self.sample_interval = sample_interval  # minutes between samples
        self.moviegoers_served = 0

    def _theater_state(self, env, theater):
        """Return a dict of the current theater state."""
        return {
            "time_min": round(env.now, 4),
            "cashier_queue": len(theater.cashier.queue),
            "usher_queue":   len(theater.usher.queue),
            "food_queue":    len(theater.server.queue),
            "cashiers_busy": theater.cashier.count,
            "ushers_busy":   theater.usher.count,
            "servers_busy":  theater.server.count,
            "total_served":  self.moviegoers_served,
        }

    def snapshot(self, env, theater, event_type, moviegoer_id,
                 wait_time=None):
        """Record an event-driven row (irregular timing)."""
        row = self._theater_state(env, theater)
        row["event"] = event_type
        row["moviegoer"] = moviegoer_id
        row["wait_time_min"] = round(wait_time, 4) if wait_time else ""
        self.event_rows.append(row)

    def sampler_process(self, env, theater):
        """A SimPy process that wakes up at fixed intervals and records
        the current theater state. This is what produces the smooth,
        evenly-spaced time series for charting."""
        while True:
            row = self._theater_state(env, theater)
            self.timeseries_rows.append(row)
            yield env.timeout(self.sample_interval)

    def write_csvs(self, events_file="theater_events.csv",
                   timeseries_file="theater_timeseries.csv"):
        """Write both CSV files."""
        if self.event_rows:
            fieldnames = list(self.event_rows[0].keys())
            with open(events_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.event_rows)
            print(f"✅ Exported {len(self.event_rows)} event rows "
                  f"→ {events_file}")

        if self.timeseries_rows:
            fieldnames = list(self.timeseries_rows[0].keys())
            with open(timeseries_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.timeseries_rows)
            print(f"✅ Exported {len(self.timeseries_rows)} time-sampled rows "
                  f"→ {timeseries_file}")


# ---------------------------------------------------------------------------
# Theater model (same logic, now reports to the DataCollector)
# ---------------------------------------------------------------------------
class Theater:
    def __init__(self, env, num_cashiers, num_servers, num_ushers):
        self.env = env
        self.cashier = simpy.Resource(env, num_cashiers)
        self.server  = simpy.Resource(env, num_servers)
        self.usher   = simpy.Resource(env, num_ushers)

    def purchase_ticket(self, moviegoer):
        yield self.env.timeout(random.randint(1, 3))

    def check_ticket(self, moviegoer):
        yield self.env.timeout(3 / 60)

    def sell_food(self, moviegoer):
        yield self.env.timeout(random.randint(1, 5))


def go_to_movies(env, moviegoer, theater, dc):
    arrival_time = env.now
    dc.snapshot(env, theater, "arrive", moviegoer)

    # --- Cashier ---
    with theater.cashier.request() as req:
        dc.snapshot(env, theater, "join_cashier_queue", moviegoer)
        yield req
        dc.snapshot(env, theater, "start_purchase", moviegoer)
        yield env.process(theater.purchase_ticket(moviegoer))
    dc.snapshot(env, theater, "ticket_purchased", moviegoer)

    # --- Usher ---
    with theater.usher.request() as req:
        dc.snapshot(env, theater, "join_usher_queue", moviegoer)
        yield req
        dc.snapshot(env, theater, "start_ticket_check", moviegoer)
        yield env.process(theater.check_ticket(moviegoer))
    dc.snapshot(env, theater, "ticket_checked", moviegoer)

    # --- Food (50% chance) ---
    if random.choice([True, False]):
        with theater.server.request() as req:
            dc.snapshot(env, theater, "join_food_queue", moviegoer)
            yield req
            dc.snapshot(env, theater, "start_food_order", moviegoer)
            yield env.process(theater.sell_food(moviegoer))
        dc.snapshot(env, theater, "food_received", moviegoer)

    # --- Done ---
    total_wait = env.now - arrival_time
    dc.moviegoers_served += 1
    dc.snapshot(env, theater, "enter_theater", moviegoer,
                wait_time=total_wait)


def run_theater(env, num_cashiers, num_servers, num_ushers, dc):
    theater = Theater(env, num_cashiers, num_servers, num_ushers)

    # Start the fixed-interval sampler — this runs alongside the theater
    # and records a row every dc.sample_interval minutes regardless of
    # whether any events are happening at that moment
    env.process(dc.sampler_process(env, theater))

    for moviegoer in range(3):
        env.process(go_to_movies(env, moviegoer, theater, dc))

    while True:
        yield env.timeout(0.20)
        moviegoer += 1
        env.process(go_to_movies(env, moviegoer, theater, dc))


def get_average_wait_time(wait_times):
    average_wait = statistics.mean(wait_times)
    minutes, frac_minutes = divmod(average_wait, 1)
    seconds = frac_minutes * 60
    return round(minutes), round(seconds)

def get_user_input():
    num_cashiers = input("Input # of cashiers working: ")
    num_servers = input("Input # of servers working: ")
    num_ushers = input("Input # of ushers working: ")
    sim_duration =input("Input length of sim duration (in minutes): ")
    params = [num_cashiers, num_servers, num_ushers, sim_duration]
    if all(str(i).isdigit() for i in params):
        params = [int(x) for x in params]
    else:
        print(
            "Could not parse input. Simulation will use default values:",
            "\n5 cashier, 3 server, 1 usher, 90 minutes.",
        )
        params = [5, 3, 1, 90]
    return params

def main():
    random.seed(42)

    # ---- Configuration ----
    # Change these values to experiment with different staffing levels.
    # The CSV output lets you compare runs side by side in the notebook.
    num_cashiers, num_servers, num_ushers, sim_duration = get_user_input()

    print(f"Running simulation: {num_cashiers} cashier(s), "
          f"{num_servers} server(s), {num_ushers} usher(s) "
          f"for {sim_duration} min...")

    dc = DataCollector(sample_interval=0.25)
    env = simpy.Environment()
    env.process(run_theater(env, num_cashiers, num_servers, num_ushers, dc))
    env.run(until=sim_duration)

    # Write results — two CSVs
    dc.write_csvs(
        events_file="theater_events.csv",       # every event (irregular)
        timeseries_file="theater_timeseries.csv" # fixed intervals (smooth)
    )

    # Summary
    served_rows = [r for r in dc.event_rows if r["wait_time_min"] != ""]
    wait_times = [r["wait_time_min"] for r in served_rows]
    mins, secs = get_average_wait_time(wait_times)
    print(f"Moviegoers served: {len(wait_times)}")
    print(f"Average wait time: {mins} min {secs} sec")


if __name__ == "__main__":
    main()