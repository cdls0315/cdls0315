# Closed Queuing Network Simulation - Documentation

## Overview

This simulation implements a **discrete-event simulation** of a closed queuing network, specifically designed for manufacturing systems analysis. In a closed queuing network, a fixed number of jobs (parts, products) continuously circulate through a series of workstations, never leaving the system.

## Key Concepts

### Closed vs. Open Queuing Networks

- **Closed Network**: Fixed number of jobs in the system (constant WIP - Work-In-Process)
  - Common in manufacturing with limited pallets, fixtures, or carriers
  - Jobs recirculate through the network indefinitely
  - System throughput is limited by WIP and bottlenecks

- **Open Network**: Jobs arrive from outside, get processed, and leave
  - Common in service systems (call centers, hospitals)
  - Arrival and departure rates determine system behavior

### Manufacturing Relevance

Closed queuing networks are particularly relevant for:
1. **Pull production systems** (Kanban, CONWIP)
2. **Automated manufacturing lines** with fixed carriers
3. **Testing and burn-in systems** with limited test fixtures
4. **Semiconductor fabrication** with limited wafer carriers

## Key Performance Metrics

### 1. Throughput (λ)
- Number of jobs completed per unit time
- **Unit**: jobs/time
- **Goal**: Maximize (subject to constraints)

### 2. Cycle Time (CT)
- Average time for a job to complete one circulation through the network
- **Unit**: time units
- **Goal**: Minimize (while maintaining throughput)

### 3. Work-In-Process (WIP)
- Number of jobs in the system
- **Unit**: jobs
- **Relationship**: Little's Law states WIP = λ × CT

### 4. Utilization (ρ)
- Fraction of time servers are busy
- **Unit**: percentage (0-100%)
- **Bottleneck**: Station with highest utilization

### 5. Queue Length
- Average number of jobs waiting for service
- **Unit**: jobs
- **Impact**: Increases cycle time and variability

## Implementation Details

### Event-Driven Simulation

The simulation uses a **discrete-event** approach:
1. Events are scheduled in a priority queue (ordered by time)
2. Time advances by jumping from event to event
3. System state updates only when events occur

### Event Types

1. **ARRIVAL**: Job arrives at a station
   - Job joins the queue
   - Service starts immediately if server available
   
2. **DEPARTURE**: Job completes service at a station
   - Server becomes available
   - Next job in queue (if any) starts service
   - Job routes to next station based on routing matrix

### Station Model

Each station has:
- **Number of servers** (parallel capacity)
- **Service time distribution** (exponential with mean μ)
- **Queue** (FIFO - First In, First Out)

### Routing Matrix

An N×N matrix where element (i,j) represents the probability of routing from station i to station j.

Example for a 3-station line:
```
     Station 0  Station 1  Station 2
0    [  0.0       1.0        0.0    ]  # 0 → 1 always
1    [  0.0       0.0        1.0    ]  # 1 → 2 always
2    [  1.0       0.0        0.0    ]  # 2 → 0 always (recirculate)
```

## Usage Examples

### Basic Two-Station Network

```python
from closed_queuing_network import ClosedQueueingNetwork
import numpy as np

# Define routing (jobs alternate between stations)
routing_matrix = np.array([
    [0.0, 1.0],  # Station 0 → Station 1
    [1.0, 0.0]   # Station 1 → Station 0
])

# Create network with 5 jobs
network = ClosedQueueingNetwork(num_jobs=5, routing_matrix=routing_matrix)

# Add stations
network.add_station(num_servers=1, mean_service_time=1.0, name="Machining")
network.add_station(num_servers=1, mean_service_time=1.5, name="Assembly")

# Initialize and run
network.initialize_jobs(initial_station=0)
network.run(simulation_time=1000.0, warmup_time=100.0)

# View results
network.print_statistics()
```

### WIP Analysis

See `wip_analysis_example.py` for a complete example analyzing how different WIP levels affect:
- System throughput
- Cycle time
- Queue lengths
- Bottleneck behavior

## Interpreting Results

### Bottleneck Identification

The bottleneck is the station that limits system throughput:
- **Highest utilization** (typically >85-95%)
- **Longest queues**
- **Highest impact** on cycle time

**Actions to address bottlenecks:**
1. Add parallel servers (increase capacity)
2. Reduce service time (process improvement)
3. Offload work to other stations (rebalancing)

### Utilization Patterns

- **Low utilization (<50%)**: Excess capacity, potential for consolidation
- **Moderate utilization (50-80%)**: Good balance, room for variability
- **High utilization (80-95%)**: Near capacity, vulnerable to disruptions
- **Very high utilization (>95%)**: Bottleneck, queue buildup, long cycle times

### Optimal WIP Level

Use WIP analysis to find the optimal level that:
- **Maximizes throughput** without excessive queueing
- **Minimizes cycle time** while keeping bottleneck busy
- **Balances** lead time and capacity utilization

**Rule of thumb**: Optimal WIP is often 1.5-3× the number of stations

## Validation and Verification

The simulation includes comprehensive tests:
- **Basic functionality**: Event processing, time advancement
- **Bottleneck detection**: Identifying limiting resources
- **WIP conservation**: Verifying constant job count (closed network property)
- **Multiple servers**: Correct parallel processing behavior

Run tests with:
```bash
python test_queuing_network.py
```

## Extensions and Modifications

### Adding Complexity

1. **Different service time distributions**:
   - Modify `generate_service_time()` in Station class
   - Consider: Normal, Lognormal, Uniform, Deterministic

2. **Priority rules**:
   - Modify queue to use priority instead of FIFO
   - Consider: Shortest Processing Time (SPT), Earliest Due Date (EDD)

3. **Breakdowns and maintenance**:
   - Add server failure and repair events
   - Model availability and reliability

4. **Batch processing**:
   - Accumulate jobs before processing
   - Model batch sizes and setup times

5. **Setup times**:
   - Add setup events when switching between job types
   - Model sequence-dependent setups

## References and Further Reading

### Queuing Theory
- "Factory Physics" by Hopp & Spearman (Chapter 8: Variability Basics)
- "Introduction to Queueing Theory" by Cooper

### Simulation
- "Discrete-Event System Simulation" by Banks et al.
- "Simulation Modeling and Analysis" by Law & Kelton

### Manufacturing Systems
- "Manufacturing Systems Engineering" by Stanley B. Gershwin
- "Fundamentals of Queueing Networks" by Hong Chen & David Yao

## License

This implementation is provided as educational material for understanding closed queuing networks in manufacturing systems analysis.

---

**Author**: Christian De Los Santos  
**Context**: Manufacturing systems modeling, WIP analysis, bottleneck detection
