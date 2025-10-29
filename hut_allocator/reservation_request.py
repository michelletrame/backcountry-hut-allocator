from datetime import datetime, timedelta

class ReservationRequest:
    """Represents a single reservation request from a user."""

    def __init__(self, user_name, preference_rank, hut_name, start_date, end_date, party_size, traverse_group=None):
        self.user_name = user_name
        self.preference_rank = int(preference_rank)  # 1-5, where 1 is most preferred
        self.hut_name = hut_name
        self.start_date = start_date if isinstance(start_date, datetime) else datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = end_date if isinstance(end_date, datetime) else datetime.strptime(end_date, "%Y-%m-%d")
        self.party_size = int(party_size)
        self.traverse_group = traverse_group  # None for regular, e.g., "traverse_1" for linked traverse
        self.assigned = False

        # Make request_id unique including hut and dates for traverse legs
        if traverse_group:
            self.request_id = f"{user_name}_P{preference_rank}_{hut_name}_{start_date}"
        else:
            self.request_id = f"{user_name}_P{preference_rank}"

    @property
    def is_traverse(self):
        """Check if this request is part of a traverse."""
        return self.traverse_group is not None

    @property
    def num_nights(self):
        """Calculate number of nights for this reservation."""
        return (self.end_date - self.start_date).days

    def get_date_range(self):
        """Return list of all dates covered by this reservation."""
        dates = []
        current = self.start_date
        while current < self.end_date:
            dates.append(current)
            current += timedelta(days=1)
        return dates

    def __repr__(self):
        status = "ASSIGNED" if self.assigned else "UNASSIGNED"
        traverse_info = f" [TRAVERSE: {self.traverse_group}]" if self.is_traverse else ""
        return f"{self.user_name} (P{self.preference_rank}): {self.hut_name}, {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}, {self.party_size} people [{status}]{traverse_info}"

    def __eq__(self, other):
        if not isinstance(other, ReservationRequest):
            return False
        return self.request_id == other.request_id

    def __hash__(self):
        return hash(self.request_id)
