import copy
import random
from hut_allocator.hut import Hut
from hut_allocator.config import PREFERENCE_SCORES, USER_ASSIGNMENT_BONUS

class Allocation:
    """Represents a complete allocation of reservation requests to huts."""

    def __init__(self, huts_config, requests, season_start, season_end):
        """
        Initialize allocation.

        Args:
            huts_config: dict of {hut_name: capacity}
            requests: list of ReservationRequest objects
            season_start: datetime
            season_end: datetime
        """
        self.huts = {}
        for name, capacity in huts_config.items():
            self.huts[name] = Hut(name, capacity, season_start, season_end)

        self.requests = requests
        self.assigned_requests = set()
        self.unassigned_requests = set(requests)
        self.score = 0

    def assign_request(self, request):
        """Try to assign a request to its specified hut."""
        hut = self.huts.get(request.hut_name)
        if not hut:
            return False

        if hut.can_accommodate(request):
            hut.add_reservation(request)
            self.assigned_requests.add(request)
            self.unassigned_requests.discard(request)
            return True
        return False

    def unassign_request(self, request):
        """Remove a request from its assigned hut."""
        if not request.assigned:
            return

        hut = self.huts.get(request.hut_name)
        if hut:
            hut.remove_reservation(request)
            self.assigned_requests.discard(request)
            self.unassigned_requests.add(request)

    def calculate_score(self):
        """
        Calculate total score prioritizing user coverage over preference rank.

        Score = (users_assigned * USER_ASSIGNMENT_BONUS) + preference_points

        This ensures the optimizer prioritizes getting everyone at least one
        assignment before optimizing for specific preference ranks.
        """
        # Count unique users who have at least one assignment
        assigned_users = set(req.user_name for req in self.assigned_requests)
        users_assigned_bonus = len(assigned_users) * USER_ASSIGNMENT_BONUS

        # Add preference scores
        preference_score = 0
        for request in self.assigned_requests:
            preference_score += PREFERENCE_SCORES.get(request.preference_rank, 0)

        self.score = users_assigned_bonus + preference_score
        return self.score

    def get_user_requests(self, user_name):
        """Get all requests for a specific user."""
        return [req for req in self.requests if req.user_name == user_name]

    def get_assigned_preference_for_user(self, user_name):
        """Get the preference rank that was assigned to a user (or None)."""
        user_requests = self.get_user_requests(user_name)
        assigned = [req for req in user_requests if req.assigned]
        if assigned:
            return min(req.preference_rank for req in assigned)
        return None

    def greedy_assign(self):
        """Greedy assignment: assign in order of preference rank."""
        # Sort requests by preference rank (1 first, then 2, etc.)
        sorted_requests = sorted(self.requests, key=lambda r: (r.preference_rank, random.random()))

        for request in sorted_requests:
            user = request.user_name
            # Only assign if user doesn't already have an assignment
            if self.get_assigned_preference_for_user(user) is None:
                self.assign_request(request)

        self.calculate_score()

    def random_assign(self):
        """Randomly assign requests."""
        shuffled = list(self.requests)
        random.shuffle(shuffled)

        for request in shuffled:
            user = request.user_name
            if self.get_assigned_preference_for_user(user) is None:
                self.assign_request(request)

        self.calculate_score()

    def try_swap_requests(self, req1, req2):
        """
        Try swapping two requests. This means unassigning both and trying to assign
        the other user's request in each slot.
        """
        if req1.user_name == req2.user_name:
            return False

        # Only makes sense if at least one is assigned
        if not req1.assigned and not req2.assigned:
            return False

        old_score = self.score

        # Save states
        req1_was_assigned = req1.assigned
        req2_was_assigned = req2.assigned

        # Unassign both
        if req1_was_assigned:
            self.unassign_request(req1)
        if req2_was_assigned:
            self.unassign_request(req2)

        # Try to assign in opposite order
        success1 = False
        success2 = False

        if not req1_was_assigned:
            success1 = self.assign_request(req1)
        if not req2_was_assigned:
            success2 = self.assign_request(req2)

        new_score = self.calculate_score()

        # If score didn't improve, revert
        if new_score <= old_score:
            # Revert
            if success1:
                self.unassign_request(req1)
            if success2:
                self.unassign_request(req2)
            if req1_was_assigned:
                self.assign_request(req1)
            if req2_was_assigned:
                self.assign_request(req2)
            self.calculate_score()
            return False

        return True

    def get_summary(self):
        """Get a summary of the allocation."""
        summary = f"\n{'='*60}\n"
        summary += f"ALLOCATION SCORE: {self.score}\n"
        summary += f"Assigned: {len(self.assigned_requests)}/{len(self.requests)} requests\n"
        summary += f"{'='*60}\n"

        # Group by user
        users = set(req.user_name for req in self.requests)
        for user in sorted(users):
            user_requests = self.get_user_requests(user)
            assigned = [req for req in user_requests if req.assigned]
            if assigned:
                summary += f"\n{user}: ASSIGNED (Preference {assigned[0].preference_rank})\n"
                summary += f"  {assigned[0]}\n"
            else:
                summary += f"\n{user}: UNASSIGNED\n"
                for req in sorted(user_requests, key=lambda r: r.preference_rank):
                    summary += f"  P{req.preference_rank}: {req.hut_name}, {req.start_date.strftime('%Y-%m-%d')} to {req.end_date.strftime('%Y-%m-%d')}, {req.party_size} people\n"

        # Hut summaries
        summary += f"\n{'='*60}\n"
        summary += "HUT OCCUPANCY:\n"
        summary += f"{'='*60}\n"
        for hut in self.huts.values():
            summary += hut.get_occupancy_summary()

        return summary

    def copy(self):
        """Create a deep copy of this allocation."""
        new_alloc = Allocation(
            {name: hut.capacity for name, hut in self.huts.items()},
            self.requests,
            list(self.huts.values())[0].season_start,
            list(self.huts.values())[0].season_end
        )

        # Copy assignments
        for request in self.assigned_requests:
            new_alloc.assign_request(request)

        new_alloc.calculate_score()
        return new_alloc

    def __repr__(self):
        return f"Allocation(score={self.score}, assigned={len(self.assigned_requests)}/{len(self.requests)})"
