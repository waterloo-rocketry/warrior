from hilt import Pin
from warrior import hilt

class Blade:
    def __call__(self, slot):
        raise NotImplementedError

class OutputBlade(Blade):
    DIGITAL = False
    ANALOG = True
    def __call__(self, slot):
        return [
            OutputChannel(slot, Pin.PPS1, Pin.AN1, Pin.D1),
            OutputChannel(slot, Pin.PPS1, Pin.AN1, Pin.D1)
        ]
Output = OutputBlade()

class AnalogInputBlade(Blade):
    def __call__(self, slot):
        return [
            AnalogInputChannel(slot, Pin.PPS1, Pin.AN1, Pin.D1),
            AnalogInputChannel(slot, Pin.PPS1, Pin.AN1, Pin.D1)
        ]
AnalogInput = AnalogInputBlade()

class Channel:
    def __init__(self, slot):
        self.slot = slot

class OutputChannel(Channel):
    def __init__(self, slot, pps, an, d):
        super().__init__(slot)
        self.pps = pps
        self.an = an
        self.d = d
        self._mode = Output.DIGITAL
        hilt.digital_read(self.slot, self.pps) # clear pin type
        hilt.analog_read(self.slot, self.an) # set correct pin type
        hilt.digital_write(self.slot, self.d, self._mode)

    def mode(self, mode):
        self._mode = mode
        hilt.digital_write(self.slot, self.d, self._mode)

    def set(self, value):
        if self._mode is Output.DIGITAL:
            if not isinstance(value, bool):
                raise TypeError(f"Cannot set digital output to non-boolean {value}.")
            hilt.digital_write(self.slot, self.pps, value)
        elif self._mode is Output.ANALOG:
            if not isinstance(value, (int, float)):
                raise TypeError(f"Cannot set digital output to non-numeric {value}.")
            hilt.analog_write(self.slot, self.pps, value)

class AnalogInputChannel(Channel):
    def __init__(self, slot, pps, an, d):
        super().__init__(slot)
        self.pps = pps
        self.an = an
        self.d = d
        hilt.analog_read(self.slot, self.pps) # set correct pin type
        hilt.analog_read(self.slot, self.an)

    def get_voltage(self):
        return hilt.analog_read(self.slot, self.pps) / 15 * 115
