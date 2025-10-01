"""
Closed Queuing Network Simulation

A discrete-event simulation of a closed queuing network for manufacturing systems analysis.
This implementation models production flows, work-in-process (WIP), cycle times, and bottlenecks.

Author: Christian De Los Santos
"""

import numpy as np
import heapq
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum


class EventType(Enum):
    """Types of events in the simulation"""
    ARRIVAL = "arrival"
    DEPARTURE = "departure"


@dataclass(order=True)
class Event:
    """Represents a discrete event in the simulation"""
    time: float
    event_type: EventType = field(compare=False)
    job_id: int = field(compare=False)
    station_id: int = field(compare=False)


@dataclass
class Job:
    """Represents a job/part moving through the network"""
    job_id: int
    arrival_time: float = 0.0
    completion_time: float = 0.0
    station_visits: List[Tuple[int, float, float]] = field(default_factory=list)
    
    @property
    def cycle_time(self) -> float:
        """Calculate total cycle time for the job"""
        return self.completion_time - self.arrival_time if self.completion_time > 0 else 0.0


class Station:
    """Represents a workstation in the queuing network"""
    
    def __init__(self, station_id: int, num_servers: int, mean_service_time: float, name: str = None):
        """
        Initialize a station.
        
        Args:
            station_id: Unique identifier for the station
            num_servers: Number of parallel servers at this station
            mean_service_time: Mean service time (exponentially distributed)
            name: Optional name for the station
        """
        self.station_id = station_id
        self.num_servers = num_servers
        self.mean_service_time = mean_service_time
        self.name = name or f"Station_{station_id}"
        
        self.queue: List[int] = []  # Queue of job IDs waiting for service
        self.servers_busy = 0  # Number of servers currently busy
        
        # Statistics
        self.total_arrivals = 0
        self.total_departures = 0
        self.total_queue_time = 0.0
        self.total_service_time = 0.0
        self.queue_length_sum = 0.0
        self.last_update_time = 0.0
        
    def is_available(self) -> bool:
        """Check if a server is available"""
        return self.servers_busy < self.num_servers
    
    def add_to_queue(self, job_id: int, current_time: float):
        """Add a job to the queue"""
        self._update_queue_stats(current_time)
        self.queue.append(job_id)
        self.total_arrivals += 1
        
    def start_service(self, current_time: float) -> Optional[int]:
        """Start service for the next job in queue if server available"""
        self._update_queue_stats(current_time)
        if self.queue and self.is_available():
            job_id = self.queue.pop(0)
            self.servers_busy += 1
            return job_id
        return None
    
    def complete_service(self, current_time: float):
        """Complete service for a job"""
        self._update_queue_stats(current_time)
        self.servers_busy -= 1
        self.total_departures += 1
        
    def generate_service_time(self) -> float:
        """Generate a service time from exponential distribution"""
        return np.random.exponential(self.mean_service_time)
    
    def _update_queue_stats(self, current_time: float):
        """Update queue length statistics"""
        if self.last_update_time > 0:
            time_delta = current_time - self.last_update_time
            self.queue_length_sum += len(self.queue) * time_delta
        self.last_update_time = current_time
    
    @property
    def utilization(self) -> float:
        """Calculate server utilization"""
        if self.total_service_time == 0:
            return 0.0
        return self.total_service_time / (self.num_servers * self.last_update_time)
    
    @property
    def avg_queue_length(self) -> float:
        """Calculate average queue length"""
        if self.last_update_time == 0:
            return 0.0
        return self.queue_length_sum / self.last_update_time


class ClosedQueueingNetwork:
    """
    Simulates a closed queuing network (fixed number of jobs circulating).
    
    In a closed network, jobs never leave - they continuously cycle through stations.
    This is common in manufacturing where a fixed number of parts circulate.
    """
    
    def __init__(self, num_jobs: int, routing_matrix: np.ndarray, seed: int = None):
        """
        Initialize the closed queuing network.
        
        Args:
            num_jobs: Fixed number of jobs in the system (WIP level)
            routing_matrix: Probability matrix for routing between stations (NxN)
            seed: Random seed for reproducibility
        """
        if seed is not None:
            np.random.seed(seed)
        
        self.num_jobs = num_jobs
        self.routing_matrix = routing_matrix
        self.num_stations = len(routing_matrix)
        
        self.stations: List[Station] = []
        self.jobs: Dict[int, Job] = {}
        self.event_queue: List[Event] = []
        self.current_time = 0.0
        self.jobs_in_transit = set()  # Track jobs between stations
        
        # Statistics
        self.total_completions = 0
        self.warmup_completions = 0
        
    def add_station(self, num_servers: int, mean_service_time: float, name: str = None) -> int:
        """Add a station to the network"""
        station_id = len(self.stations)
        station = Station(station_id, num_servers, mean_service_time, name)
        self.stations.append(station)
        return station_id
    
    def initialize_jobs(self, initial_station: int = 0):
        """Initialize all jobs at a starting station"""
        for job_id in range(self.num_jobs):
            job = Job(job_id=job_id, arrival_time=0.0)
            self.jobs[job_id] = job
            
            # Add initial arrival events for all jobs
            event = Event(
                time=0.0,
                event_type=EventType.ARRIVAL,
                job_id=job_id,
                station_id=initial_station
            )
            heapq.heappush(self.event_queue, event)
    
    def schedule_event(self, time: float, event_type: EventType, job_id: int, station_id: int):
        """Schedule a new event"""
        event = Event(time=time, event_type=event_type, job_id=job_id, station_id=station_id)
        heapq.heappush(self.event_queue, event)
    
    def get_next_station(self, current_station: int) -> int:
        """Determine next station based on routing probabilities"""
        probabilities = self.routing_matrix[current_station]
        return np.random.choice(self.num_stations, p=probabilities)
    
    def process_arrival(self, event: Event):
        """Process a job arrival at a station"""
        station = self.stations[event.station_id]
        job = self.jobs[event.job_id]
        
        # Remove from transit tracking
        self.jobs_in_transit.discard(event.job_id)
        
        # Record arrival time at this station
        arrival_time = event.time
        
        # Add to queue
        station.add_to_queue(event.job_id, self.current_time)
        
        # Try to start service immediately if server available
        if station.is_available():
            job_to_serve = station.start_service(self.current_time)
            if job_to_serve is not None:
                # Schedule departure
                service_time = station.generate_service_time()
                departure_time = self.current_time + service_time
                station.total_service_time += service_time
                
                # Record station visit
                job.station_visits.append((event.station_id, arrival_time, departure_time))
                
                self.schedule_event(
                    time=departure_time,
                    event_type=EventType.DEPARTURE,
                    job_id=job_to_serve,
                    station_id=event.station_id
                )
    
    def process_departure(self, event: Event):
        """Process a job departure from a station"""
        station = self.stations[event.station_id]
        job = self.jobs[event.job_id]
        
        # Complete service
        station.complete_service(self.current_time)
        
        # Count completion (for statistics after warmup)
        self.total_completions += 1
        
        # Try to serve next job in queue
        if station.queue:
            job_to_serve = station.start_service(self.current_time)
            if job_to_serve is not None:
                service_time = station.generate_service_time()
                departure_time = self.current_time + service_time
                station.total_service_time += service_time
                
                # Record station visit
                next_job = self.jobs[job_to_serve]
                next_job.station_visits.append((event.station_id, self.current_time, departure_time))
                
                self.schedule_event(
                    time=departure_time,
                    event_type=EventType.DEPARTURE,
                    job_id=job_to_serve,
                    station_id=event.station_id
                )
        
        # Route to next station
        next_station = self.get_next_station(event.station_id)
        self.jobs_in_transit.add(event.job_id)  # Mark as in transit
        self.schedule_event(
            time=self.current_time,
            event_type=EventType.ARRIVAL,
            job_id=event.job_id,
            station_id=next_station
        )
    
    def run(self, simulation_time: float, warmup_time: float = 0.0):
        """
        Run the simulation.
        
        Args:
            simulation_time: Total simulation time
            warmup_time: Warmup period to exclude from statistics
        """
        print(f"Starting simulation with {self.num_jobs} jobs for {simulation_time} time units...")
        print(f"Warmup period: {warmup_time} time units\n")
        
        # Reset statistics at warmup
        warmup_done = False
        
        while self.event_queue and self.current_time < simulation_time:
            # Get next event
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            
            # Check for warmup completion
            if not warmup_done and self.current_time >= warmup_time:
                self._reset_statistics()
                warmup_done = True
                print(f"Warmup period completed at time {warmup_time:.2f}\n")
            
            # Process event
            if event.event_type == EventType.ARRIVAL:
                self.process_arrival(event)
            elif event.event_type == EventType.DEPARTURE:
                self.process_departure(event)
        
        print(f"Simulation completed at time {self.current_time:.2f}")
    
    def _reset_statistics(self):
        """Reset statistics after warmup period"""
        for station in self.stations:
            station.total_arrivals = 0
            station.total_departures = 0
            station.total_queue_time = 0.0
            station.total_service_time = 0.0
            station.queue_length_sum = 0.0
            station.last_update_time = self.current_time
        
        self.total_completions = 0
        self.warmup_completions = 0
    
    def print_statistics(self):
        """Print simulation statistics"""
        print("\n" + "="*70)
        print("CLOSED QUEUING NETWORK SIMULATION RESULTS")
        print("="*70)
        
        print(f"\nNetwork Configuration:")
        print(f"  Total Jobs in System (WIP): {self.num_jobs}")
        print(f"  Number of Stations: {self.num_stations}")
        print(f"  Total Completions: {self.total_completions}")
        print(f"  Simulation Time: {self.current_time:.2f}")
        
        if self.total_completions > 0:
            throughput = self.total_completions / self.current_time
            avg_cycle_time = self.current_time / (self.total_completions / self.num_jobs)
            print(f"  Throughput: {throughput:.4f} jobs/time unit")
            print(f"  Avg Cycle Time: {avg_cycle_time:.4f} time units")
        
        print(f"\nStation Statistics:")
        print("-" * 70)
        
        bottleneck_util = 0.0
        bottleneck_station = None
        
        for station in self.stations:
            print(f"\n{station.name}:")
            print(f"  Servers: {station.num_servers}")
            print(f"  Mean Service Time: {station.mean_service_time:.2f}")
            print(f"  Arrivals: {station.total_arrivals}")
            print(f"  Departures: {station.total_departures}")
            print(f"  Utilization: {station.utilization:.2%}")
            print(f"  Avg Queue Length: {station.avg_queue_length:.2f}")
            print(f"  Current Queue: {len(station.queue)} jobs")
            
            if station.utilization > bottleneck_util:
                bottleneck_util = station.utilization
                bottleneck_station = station
        
        if bottleneck_station:
            print(f"\n{'='*70}")
            print(f"BOTTLENECK ANALYSIS:")
            print(f"  Bottleneck Station: {bottleneck_station.name}")
            print(f"  Utilization: {bottleneck_util:.2%}")
            print(f"  This station limits system throughput")
            print("="*70)


def example_two_station_network():
    """Example: Simple two-station closed queuing network"""
    print("\n" + "="*70)
    print("EXAMPLE: Two-Station Closed Queuing Network")
    print("="*70 + "\n")
    
    # Create routing matrix (2x2)
    # Jobs alternate between stations: 0 -> 1 -> 0 -> 1 -> ...
    routing_matrix = np.array([
        [0.0, 1.0],  # From station 0: always go to station 1
        [1.0, 0.0]   # From station 1: always go to station 0
    ])
    
    # Create network with 5 jobs
    network = ClosedQueueingNetwork(num_jobs=5, routing_matrix=routing_matrix, seed=42)
    
    # Add stations
    network.add_station(num_servers=1, mean_service_time=1.0, name="Machining")
    network.add_station(num_servers=1, mean_service_time=1.5, name="Assembly")
    
    # Initialize jobs at station 0
    network.initialize_jobs(initial_station=0)
    
    # Run simulation
    network.run(simulation_time=1000.0, warmup_time=100.0)
    
    # Print results
    network.print_statistics()


def example_manufacturing_line():
    """Example: Manufacturing line with multiple stations"""
    print("\n" + "="*70)
    print("EXAMPLE: Manufacturing Line with 4 Stations")
    print("="*70 + "\n")
    
    # Create routing matrix (4x4) - sequential flow with recirculation
    routing_matrix = np.array([
        [0.0, 1.0, 0.0, 0.0],  # Station 0 -> Station 1
        [0.0, 0.0, 1.0, 0.0],  # Station 1 -> Station 2
        [0.0, 0.0, 0.0, 1.0],  # Station 2 -> Station 3
        [1.0, 0.0, 0.0, 0.0]   # Station 3 -> Station 0 (recirculate)
    ])
    
    # Create network with 10 jobs (WIP = 10)
    network = ClosedQueueingNetwork(num_jobs=10, routing_matrix=routing_matrix, seed=123)
    
    # Add stations with different capacities and service times
    network.add_station(num_servers=2, mean_service_time=0.8, name="Loading")
    network.add_station(num_servers=1, mean_service_time=2.0, name="Processing")  # Bottleneck
    network.add_station(num_servers=2, mean_service_time=1.0, name="Inspection")
    network.add_station(num_servers=1, mean_service_time=0.5, name="Unloading")
    
    # Initialize jobs at station 0
    network.initialize_jobs(initial_station=0)
    
    # Run simulation
    network.run(simulation_time=2000.0, warmup_time=200.0)
    
    # Print results
    network.print_statistics()


if __name__ == "__main__":
    # Run examples
    example_two_station_network()
    print("\n" * 3)
    example_manufacturing_line()
