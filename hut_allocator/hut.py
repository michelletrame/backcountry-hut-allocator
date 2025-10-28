from datetime import datetime, timedelta
from collections import defaultdict

class Hut:
    """Represents a backcountry hut with capacity tracking."""

    def __init__(self, name, capacity, season_start, season_end):
        self.name = name
        self.capacity = capacity
        self.season_start = season_start
        self.season_end = season_end
        # Track reservations by date: {date: [(request, party_size), ...]}
        self.reservations = defaultdict(list)

    def get_available_capacity(self, date):
        """Get remaining capacity for a specific date."""
        if date < self.season_start or date >= self.season_end:
            return 0
        used = sum(party_size for _, party_size in self.reservations[date])
        return self.capacity - used

    def can_accommodate(self, request):
        """Check if this hut can accommodate the reservation request."""
        for date in request.get_date_range():
            if self.get_available_capacity(date) < request.party_size:
                return False
        return True

    def add_reservation(self, request):
        """Add a reservation to this hut."""
        if not self.can_accommodate(request):
            return False
        for date in request.get_date_range():
            self.reservations[date].append((request, request.party_size))
        request.assigned = True
        return True

    def remove_reservation(self, request):
        """Remove a reservation from this hut."""
        for date in request.get_date_range():
            self.reservations[date] = [(req, size) for req, size in self.reservations[date] if req != request]
        request.assigned = False

    def get_occupancy_summary(self):
        """Get summary of hut occupancy."""
        dates = sorted(self.reservations.keys())
        if not dates:
            return f"{self.name}: No reservations"

        summary = f"\n{self.name} (Capacity: {self.capacity}):\n"
        for date in dates:
            used = sum(size for _, size in self.reservations[date])
            requests = [req.user_name for req, _ in self.reservations[date]]
            summary += f"  {date.strftime('%Y-%m-%d')}: {used}/{self.capacity} occupied by {', '.join(requests)}\n"
        return summary

    def clear_reservations(self):
        """Clear all reservations."""
        self.reservations = defaultdict(list)

    def __repr__(self):
        return f"Hut({self.name}, capacity={self.capacity})"
