"""
Advanced Example: WIP Analysis for Closed Queuing Network

This example demonstrates how to analyze the impact of Work-In-Process (WIP) 
levels on system throughput and cycle time - a key concept in manufacturing 
systems analysis.
"""

from closed_queuing_network import ClosedQueueingNetwork
import numpy as np


def analyze_wip_impact():
    """
    Analyze how different WIP levels affect throughput and cycle time.
    This demonstrates Little's Law: WIP = Throughput × Cycle Time
    """
    print("="*70)
    print("WIP IMPACT ANALYSIS: Closed Queuing Network")
    print("="*70)
    print("\nAnalyzing system performance across different WIP levels...")
    print("(This simulates increasing the number of parts in circulation)\n")
    
    # Define routing matrix for a 3-station production line
    routing_matrix = np.array([
        [0.0, 1.0, 0.0],  # Station 0 -> Station 1
        [0.0, 0.0, 1.0],  # Station 1 -> Station 2
        [1.0, 0.0, 0.0]   # Station 2 -> Station 0 (recirculate)
    ])
    
    # Test different WIP levels
    wip_levels = [2, 5, 10, 15, 20, 25]
    results = []
    
    for wip in wip_levels:
        # Create network
        network = ClosedQueueingNetwork(
            num_jobs=wip, 
            routing_matrix=routing_matrix, 
            seed=42
        )
        
        # Add stations
        network.add_station(num_servers=1, mean_service_time=1.0, name="Prep")
        network.add_station(num_servers=1, mean_service_time=2.5, name="Process")  # Bottleneck
        network.add_station(num_servers=1, mean_service_time=0.8, name="Finish")
        
        # Run simulation
        network.initialize_jobs(initial_station=0)
        network.run(simulation_time=2000.0, warmup_time=200.0)
        
        # Calculate metrics
        throughput = network.total_completions / network.current_time
        avg_cycle_time = network.current_time / (network.total_completions / wip) if network.total_completions > 0 else 0
        
        # Find bottleneck
        bottleneck = max(network.stations, key=lambda s: s.utilization)
        
        results.append({
            'wip': wip,
            'throughput': throughput,
            'cycle_time': avg_cycle_time,
            'bottleneck_util': bottleneck.utilization,
            'bottleneck_queue': bottleneck.avg_queue_length
        })
    
    # Display results
    print("\n" + "-"*70)
    print(f"{'WIP':<6} {'Throughput':<12} {'Cycle Time':<12} {'Bottleneck':<12} {'Queue Len':<10}")
    print(f"{'':6} {'(jobs/time)':<12} {'(time)':<12} {'Utilization':<12} {'(avg)':<10}")
    print("-"*70)
    
    for r in results:
        print(f"{r['wip']:<6} {r['throughput']:<12.4f} {r['cycle_time']:<12.2f} "
              f"{r['bottleneck_util']:<12.2%} {r['bottleneck_queue']:<10.2f}")
    
    print("-"*70)
    
    # Analysis insights
    print("\n" + "="*70)
    print("KEY INSIGHTS:")
    print("="*70)
    
    # Find saturation point
    throughput_improvement = []
    for i in range(1, len(results)):
        improvement = (results[i]['throughput'] - results[i-1]['throughput']) / results[i-1]['throughput']
        throughput_improvement.append(improvement)
    
    print("\n1. THROUGHPUT ANALYSIS:")
    print(f"   - Initial throughput (WIP={results[0]['wip']}): {results[0]['throughput']:.4f}")
    print(f"   - Maximum throughput (WIP={results[-1]['wip']}): {results[-1]['throughput']:.4f}")
    print(f"   - Improvement: {((results[-1]['throughput']/results[0]['throughput'])-1)*100:.1f}%")
    
    # Find where improvements start diminishing
    diminishing_idx = next((i for i, imp in enumerate(throughput_improvement) if imp < 0.05), len(throughput_improvement))
    if diminishing_idx < len(results) - 1:
        optimal_wip = results[diminishing_idx + 1]['wip']
        print(f"   - Diminishing returns start at WIP ≈ {optimal_wip}")
    
    print("\n2. CYCLE TIME ANALYSIS:")
    print(f"   - Minimum cycle time (WIP={results[0]['wip']}): {results[0]['cycle_time']:.2f}")
    print(f"   - Cycle time at high WIP (WIP={results[-1]['wip']}): {results[-1]['cycle_time']:.2f}")
    print(f"   - Increase: {((results[-1]['cycle_time']/results[0]['cycle_time'])-1)*100:.1f}%")
    print(f"   - Higher WIP increases cycle time due to queueing")
    
    print("\n3. BOTTLENECK BEHAVIOR:")
    print(f"   - Bottleneck utilization ranges from {results[0]['bottleneck_util']:.1%} to {results[-1]['bottleneck_util']:.1%}")
    print(f"   - Queue length grows from {results[0]['bottleneck_queue']:.1f} to {results[-1]['bottleneck_queue']:.1f}")
    print(f"   - Maximum theoretical throughput ≈ {1/2.5:.4f} jobs/time (1/service_time)")
    
    print("\n4. RECOMMENDATIONS:")
    if diminishing_idx < len(results) - 1:
        optimal_wip = results[diminishing_idx + 1]['wip']
        optimal_result = results[diminishing_idx + 1]
        print(f"   - Operate near WIP = {optimal_wip} for best throughput/cycle time balance")
        print(f"   - Expected throughput: {optimal_result['throughput']:.4f} jobs/time")
        print(f"   - Expected cycle time: {optimal_result['cycle_time']:.2f} time units")
    else:
        print(f"   - Consider testing higher WIP levels for maximum throughput")
    print(f"   - To improve further, reduce bottleneck service time or add capacity")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    analyze_wip_impact()
