class TimelineManager:
    def __init__(self, timelines):
        self.timelines = timelines
        self.current_timeline = 0

    def switch_timeline(self):
        self.current_timeline = (self.current_timeline + 1) % len(self.timelines)

    def get_current_color(self):
        return self.timelines[self.current_timeline]
