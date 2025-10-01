"""
Test script for the Closed Queuing Network Simulation

This script verifies that the simulation works correctly with various configurations.
"""

import sys
from closed_queuing_network import ClosedQueueingNetwork, example_two_station_network, example_manufacturing_line
import numpy as np


def test_basic_functionality():
    """Test basic simulation functionality"""
    print("\nTest 1: Basic Functionality")
    print("-" * 50)
    
    # Create a simple network
    routing_matrix = np.array([
        [0.0, 1.0],
        [1.0, 0.0]
    ])
    
    network = ClosedQueueingNetwork(num_jobs=3, routing_matrix=routing_matrix, seed=42)
    network.add_station(num_servers=1, mean_service_time=1.0, name="Station_A")
    network.add_station(num_servers=1, mean_service_time=1.0, name="Station_B")
    network.initialize_jobs(initial_station=0)
    network.run(simulation_time=100.0, warmup_time=10.0)
    
    # Basic assertions
    assert network.total_completions > 0, "No completions recorded"
    assert network.current_time > 0, "Simulation time not advancing"
    assert len(network.stations) == 2, "Wrong number of stations"
    
    print("✓ Basic functionality test passed")
    return True


def test_bottleneck_detection():
    """Test that bottleneck detection works correctly"""
    print("\nTest 2: Bottleneck Detection")
    print("-" * 50)
    
    # Create a network with an obvious bottleneck
    routing_matrix = np.array([
        [0.0, 1.0],
        [1.0, 0.0]
    ])
    
    network = ClosedQueueingNetwork(num_jobs=5, routing_matrix=routing_matrix, seed=123)
    # Station 0: fast service
    network.add_station(num_servers=2, mean_service_time=0.5, name="Fast_Station")
    # Station 1: slow service (bottleneck)
    network.add_station(num_servers=1, mean_service_time=3.0, name="Slow_Station")
    network.initialize_jobs(initial_station=0)
    network.run(simulation_time=500.0, warmup_time=50.0)
    
    # Bottleneck should be the slow station
    slow_station = network.stations[1]
    fast_station = network.stations[0]
    
    assert slow_station.utilization > fast_station.utilization, \
        "Bottleneck detection failed: slow station should have higher utilization"
    assert slow_station.avg_queue_length > fast_station.avg_queue_length, \
        "Bottleneck detection failed: slow station should have longer queue"
    
    print(f"  Fast station utilization: {fast_station.utilization:.2%}")
    print(f"  Slow station utilization: {slow_station.utilization:.2%}")
    print("✓ Bottleneck detection test passed")
    return True


def test_wip_conservation():
    """Test that the number of jobs remains constant (closed network property)"""
    print("\nTest 3: WIP Conservation (Closed Network Property)")
    print("-" * 50)
    
    routing_matrix = np.array([
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0]
    ])
    
    num_jobs = 7
    network = ClosedQueueingNetwork(num_jobs=num_jobs, routing_matrix=routing_matrix, seed=456)
    network.add_station(num_servers=1, mean_service_time=1.0, name="Station_1")
    network.add_station(num_servers=1, mean_service_time=1.2, name="Station_2")
    network.add_station(num_servers=1, mean_service_time=0.8, name="Station_3")
    network.initialize_jobs(initial_station=0)
    network.run(simulation_time=200.0, warmup_time=20.0)
    
    # Count jobs in system
    total_jobs_in_system = 0
    for station in network.stations:
        total_jobs_in_system += len(station.queue) + station.servers_busy
    
    # Add jobs in transit between stations
    total_jobs_in_system += len(network.jobs_in_transit)
    
    # In a closed network, total jobs should equal num_jobs
    assert total_jobs_in_system == num_jobs, \
        f"WIP not conserved: {total_jobs_in_system} jobs in system, expected {num_jobs}"
    
    print(f"  Expected jobs: {num_jobs}")
    print(f"  Actual jobs: {total_jobs_in_system}")
    print(f"  (In stations: {total_jobs_in_system - len(network.jobs_in_transit)}, In transit: {len(network.jobs_in_transit)})")
    print("✓ WIP conservation test passed")
    return True


def test_multiple_servers():
    """Test that multiple servers work correctly"""
    print("\nTest 4: Multiple Servers per Station")
    print("-" * 50)
    
    routing_matrix = np.array([
        [0.0, 1.0],
        [1.0, 0.0]
    ])
    
    # Test with varying server counts
    network = ClosedQueueingNetwork(num_jobs=10, routing_matrix=routing_matrix, seed=789)
    network.add_station(num_servers=1, mean_service_time=1.0, name="Single_Server")
    network.add_station(num_servers=3, mean_service_time=1.0, name="Multi_Server")
    network.initialize_jobs(initial_station=0)
    network.run(simulation_time=300.0, warmup_time=30.0)
    
    single_server = network.stations[0]
    multi_server = network.stations[1]
    
    # Multi-server should have lower utilization per server
    assert multi_server.utilization < single_server.utilization, \
        "Multi-server station should have lower utilization"
    
    print(f"  Single server utilization: {single_server.utilization:.2%}")
    print(f"  Multi-server utilization: {multi_server.utilization:.2%}")
    print("✓ Multiple servers test passed")
    return True


def run_all_tests():
    """Run all test cases"""
    print("="*70)
    print("RUNNING CLOSED QUEUING NETWORK SIMULATION TESTS")
    print("="*70)
    
    tests = [
        test_basic_functionality,
        test_bottleneck_detection,
        test_wip_conservation,
        test_multiple_servers
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    # Run tests
    success = run_all_tests()
    
    # Run examples if tests pass
    if success:
        print("\n\nAll tests passed! Running examples...\n")
        example_two_station_network()
        print("\n" * 2)
        example_manufacturing_line()
    else:
        print("\nSome tests failed. Please fix issues before running examples.")
        sys.exit(1)
