class Blade:
    def __init__(self, slot):
        self.slot = slot

class DualChannel(Blade):
    def __new__(cls, slot):
        a = super().__new__(cls)
        a.__init__(slot, 0)
        b = super().__new__(cls)
        b.__init__(slot, 1)
        return [a, b]

    def __init__(self, slot, index):
        super().__init__(slot)
        self.pps = slot.pps[index]
        self.an = slot.an[index]
        self.d = slot.d[index]

class Output(DualChannel):
    DIGITAL = False
    ANALOG = True
    def __init__(self, slot, index):
        super().__init__(slot, index)

        self._mode = Output.DIGITAL
        #self.pps.digital_read() # clear pin type
        #self.an.analog_read() # set correct pin type
        self.d.digital_write(self._mode)

    def mode(self, mode):
        self._mode = mode
        self.d.digital_write(self._mode)

    def set(self, value):
        if self._mode is Output.DIGITAL:
            if not isinstance(value, bool):
                raise TypeError(f"Cannot set digital output to non-boolean {value}.")
            self.pps.digital_write(value)
        elif self._mode is Output.ANALOG:
            if not isinstance(value, (int, float)):
                raise TypeError(f"Cannot set analog output to non-numeric {value}.")
            self.pps.analog_write(value)

    def get_current(self):
        return (self.an.analog_read() - 1.65) * 0.2/3 # 66.6 mA/V

class AnalogInput(DualChannel):
    def __init__(self, slot, index):
        super().__init__(slot, index)

        #self.pps.analog_read() # set correct pin type
        #self.an.analog_read()
        #self.d.digital_write(False) # disconnect channel

    def set_connected(self, value):
        self.d.digital_write(value)

    def get_voltage(self):
        return self.pps.analog_read() / 15 * 115

    def get_current(self):
        return (self.an.analog_read() - 1.65) * 1.25 # 1.25 A/V
