import time
import random
import copy
from hut_allocator.allocation import Allocation
from hut_allocator.config import NUM_ITERATIONS, TIMEOUT_SECONDS, NUM_SWAP_ATTEMPTS

class Optimizer:
    """Optimizes allocation of reservation requests to huts."""

    def __init__(self, huts_config, requests, season_start, season_end):
        self.huts_config = huts_config
        self.requests = requests
        self.season_start = season_start
        self.season_end = season_end

    def optimize(self, num_iterations=NUM_ITERATIONS, timeout=TIMEOUT_SECONDS):
        """
        Run optimization to find best allocation.

        Uses a multi-start approach with local search:
        1. Generate multiple initial solutions (greedy + random)
        2. For each, perform local search by trying swaps
        3. Return the best solution found
        """
        print(f"\nStarting optimization with {num_iterations} iterations...")
        print(f"Total requests to allocate: {len(self.requests)}")

        best_allocation = None
        best_score = -1
        all_results = []

        for iteration in range(num_iterations):
            print(f"\nIteration {iteration + 1}/{num_iterations}")

            # Create new allocation
            allocation = Allocation(self.huts_config, self.requests, self.season_start, self.season_end)

            # Initialize with greedy or random
            if iteration == 0:
                # First iteration always uses greedy
                allocation.greedy_assign()
                print("  Initial method: Greedy")
            else:
                # Mix of greedy and random for diversity
                if random.random() < 0.3:
                    allocation.greedy_assign()
                    print("  Initial method: Greedy")
                else:
                    allocation.random_assign()
                    print("  Initial method: Random")

            print(f"  Initial score: {allocation.score}")

            # Local search with swaps
            allocation = self._local_search(allocation, timeout_per_iteration=timeout/num_iterations)

            print(f"  Final score: {allocation.score}")
            print(f"  Assigned: {len(allocation.assigned_requests)}/{len(allocation.requests)}")

            all_results.append(allocation)

            if allocation.score > best_score:
                best_score = allocation.score
                best_allocation = allocation

        # Sort results by score
        all_results.sort(key=lambda a: a.score, reverse=True)

        print(f"\n{'='*60}")
        print(f"OPTIMIZATION COMPLETE")
        print(f"{'='*60}")
        print(f"Best score: {best_score}")
        print(f"Top 3 scores: {[a.score for a in all_results[:3]]}")

        return best_allocation, all_results[:3]

    def _local_search(self, allocation, timeout_per_iteration=30):
        """
        Perform local search to improve allocation.

        Strategy:
        1. Try swapping unassigned requests with assigned requests
        2. Try swapping lower-preference assigned with unassigned higher-preference
        """
        start_time = time.time()
        improvements = 0

        while time.time() - start_time < timeout_per_iteration:
            improved = False

            # Strategy 1: Try to assign unassigned requests by swapping with assigned
            for unassigned in list(allocation.unassigned_requests):
                if time.time() - start_time >= timeout_per_iteration:
                    break

                # Try swapping with random assigned requests
                assigned_list = list(allocation.assigned_requests)
                random.shuffle(assigned_list)

                for assigned in assigned_list[:NUM_SWAP_ATTEMPTS]:
                    if allocation.try_swap_requests(unassigned, assigned):
                        improved = True
                        improvements += 1
                        break

            # Strategy 2: Try to improve preference rank (swap lower pref with higher pref)
            unassigned_list = list(allocation.unassigned_requests)
            random.shuffle(unassigned_list)

            for unassigned in unassigned_list[:NUM_SWAP_ATTEMPTS]:
                if time.time() - start_time >= timeout_per_iteration:
                    break

                # Look for assigned requests from different users with worse preference
                for assigned in allocation.assigned_requests:
                    if assigned.user_name != unassigned.user_name:
                        if unassigned.preference_rank < assigned.preference_rank:
                            if allocation.try_swap_requests(unassigned, assigned):
                                improved = True
                                improvements += 1
                                break

            if not improved:
                # No more improvements found
                break

        if improvements > 0:
            print(f"  Improvements made: {improvements}")

        return allocation

    def suggest_alternatives(self, allocation):
        """
        For unassigned requests, suggest alternative dates/huts.
        """
        suggestions = {}

        for request in allocation.unassigned_requests:
            user_alternatives = []

            # Try other huts for same dates
            for hut_name, hut in allocation.huts.items():
                if hut_name != request.hut_name:
                    temp_request = copy.copy(request)
                    temp_request.hut_name = hut_name
                    if hut.can_accommodate(temp_request):
                        user_alternatives.append({
                            'hut': hut_name,
                            'dates': f"{request.start_date.strftime('%Y-%m-%d')} to {request.end_date.strftime('%Y-%m-%d')}",
                            'party_size': request.party_size,
                            'note': 'Different hut, same dates'
                        })

            suggestions[request.user_name] = user_alternatives

        return suggestions
