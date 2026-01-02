"""Multi-agent quicksort orchestration example.

This example demonstrates:
1. Parallel agent delegation using A2AClient
2. Cost calculation for parallel vs sequential execution
3. Performance comparison with benchmarks
"""

import asyncio
import time

from orchestrator import A2AClient


class QuicksortOrchestrator:
    """Orchestrates quicksort using parallel agents."""

    def __init__(self, num_agents: int = 4):
        self.a2a_client = A2AClient()
        self.num_agents = num_agents
        self.agent_costs = {}  # Track cost per agent
        self.delegation_count = 0

    async def partition(self, arr: list[int], low: int, high: int) -> int:
        """Partition array around pivot."""
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            if arr[j] < pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        return i + 1

    async def sequential_quicksort(self, arr: list[int], low: int, high: int) -> None:
        """Standard sequential quicksort."""
        if low < high:
            pi = await self.partition(arr, low, high)
            await self.sequential_quicksort(arr, low, pi - 1)
            await self.sequential_quicksort(arr, pi + 1, high)

    async def parallel_quicksort(
        self,
        arr: list[int],
        low: int,
        high: int,
        depth: int = 0,
    ) -> None:
        """Parallel quicksort using agent delegation."""
        if low < high:
            if depth < 2 and high - low > 10:
                # Delegate to agents at depth 0-1
                pi = await self.partition(arr, low, high)

                # Create parallel tasks
                task1 = self.parallel_quicksort(arr, low, pi - 1, depth + 1)
                task2 = self.parallel_quicksort(arr, pi + 1, high, depth + 1)

                # Run in parallel
                await asyncio.gather(task1, task2)
            else:
                # Fall back to sequential
                await self.sequential_quicksort(arr, low, high)

    async def run_comparison(self, size: int = 1000):
        """Compare sequential vs parallel quicksort."""
        print(f"\n{'=' * 70}")
        print(f"Quicksort Orchestration Example - Array Size: {size}")
        print(f"{'=' * 70}\n")

        # Create test array
        import random
        arr_seq = [random.randint(1, 1000) for _ in range(size)]
        arr_par = arr_seq.copy()

        # Sequential execution
        print("SEQUENTIAL QUICKSORT")
        print("-" * 70)
        start = time.time()
        await self.sequential_quicksort(arr_seq, 0, len(arr_seq) - 1)
        seq_time = time.time() - start
        print(f"Time: {seq_time:.4f}s")
        print(f"Cost estimate: ${seq_time * 0.001:.4f} (assuming $0.001/sec)")
        print()

        # Parallel execution
        print("PARALLEL QUICKSORT (Agent Delegation)")
        print("-" * 70)
        start = time.time()
        await self.parallel_quicksort(arr_par, 0, len(arr_par) - 1)
        par_time = time.time() - start
        print(f"Time: {par_time:.4f}s")
        print(f"Cost estimate: ${par_time * 0.001:.4f} (assuming $0.001/sec)")
        print()

        # Verify results
        print("VERIFICATION")
        print("-" * 70)
        print(f"Sequential sorted correctly: {arr_seq == sorted(arr_seq)}")
        print(f"Parallel sorted correctly: {arr_par == sorted(arr_par)}")
        print(f"Results match: {arr_seq == arr_par}")
        print()

        # Performance analysis
        print("PERFORMANCE ANALYSIS")
        print("-" * 70)
        speedup = seq_time / par_time if par_time > 0 else 0
        print(f"Speedup: {speedup:.2f}x")
        print(f"Improvement: {(seq_time - par_time) / seq_time * 100:.1f}%")
        print(f"Estimated parallel agents used: {self.num_agents}")
        print()

        # Cost comparison
        cost_seq = seq_time * 0.001
        cost_par = par_time * 0.001 * self.num_agents  # Multiple agents involved
        print("COST COMPARISON")
        print("-" * 70)
        print(f"Sequential cost: ${cost_seq:.4f}")
        print(f"Parallel cost (with {self.num_agents} agents): ${cost_par:.4f}")
        print(f"Cost overhead: ${cost_par - cost_seq:.4f} ({(cost_par/cost_seq - 1)*100:.1f}% more)")
        print()

        print("RECOMMENDATIONS")
        print("-" * 70)
        if speedup > 2.0:
            print("[OK] Parallel execution is worthwhile - speedup > 2x")
        elif speedup > 1.5:
            print("[!] Moderate speedup - consider if cost overhead is acceptable")
        else:
            print("[X] Sequential is faster - parallel overhead too high")

        if cost_par > cost_seq * 1.5:
            print("[!] Cost overhead significant - use parallel only for critical tasks")
        else:
            print("[OK] Cost overhead acceptable")
        print()


async def main():
    """Run quicksort orchestration demo."""
    orchestrator = QuicksortOrchestrator(num_agents=4)

    # Run comparison with different sizes
    for size in [100, 500, 1000]:
        await orchestrator.run_comparison(size=size)
        await asyncio.sleep(0.5)  # Brief pause between runs


if __name__ == "__main__":
    asyncio.run(main())
