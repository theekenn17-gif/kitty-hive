import time

class HiveTimer:
    """Tracks precision millisecond latency logs across multi-agent state boundaries using high-precision counters."""
    def __init__(self):
        self.start_time = None
        self.markers = {}

    def start(self):
        self.start_time = time.perf_counter()
        self.markers = {}

    def mark(self, event_name: str):
        self.markers[event_name] = time.perf_counter()

    def report(self) -> str:
        if not self.start_time:
            return "Timer not initialized."
        
        report_lines = ["\n⏱️ HIVE PERFORMANCE LATENCY LOG:"]
        prev_time = self.start_time
        
        for event, timestamp in self.markers.items():
            duration = (timestamp - prev_time) * 1000
            padded_event = event.ljust(30, ".")
            report_lines.append(f"  - {padded_event} {duration:.1f} ms")
            prev_time = timestamp
            
        total_delta = (time.perf_counter() - self.start_time) * 1000
        report_lines.append(f"  - Total Lifecycle Execution:. {total_delta:.1f} ms\n")
        return "\n".join(report_lines)

# Singleton export profile
hive_timer = HiveTimer()
