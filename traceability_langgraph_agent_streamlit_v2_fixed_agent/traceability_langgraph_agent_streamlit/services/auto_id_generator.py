from collections import defaultdict
class AutoIdGenerator:
    def __init__(self):
        self.counts = defaultdict(int)
    def next_id(self, category: str) -> str:
        self.counts[category] += 1
        return f"AUTO-{category}-{self.counts[category]:03d}"
