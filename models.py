class Sensor:
    def __init__(self, x, y, polluted):
        self.x = x
        self.y = y
        self.polluted = polluted
        self.radius = 0


class Cell:
    def __init__(self):
        self.status = None
