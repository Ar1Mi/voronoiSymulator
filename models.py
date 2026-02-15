class Sensor:
    def __init__(self, x, y, pollution_value=1.0):
        self.x = x
        self.y = y
        self.polluted = True
        self.radius = 0
        self.pollution_value = pollution_value


class Cell:
    def __init__(self):
        self.status = None
        self.polluted_by = None
