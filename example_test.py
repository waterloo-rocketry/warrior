import time
import warrior
from blade import Output, AnalogInput

out_a, out_b = Output(10)
in_a, in_b = AnalogInput(9)

@warrior.test
def digital_output_matches():
    out_a.mode(Output.DIGITAL)
    out_a.set(True)
    time.sleep(0.1)
    assert in_a.get_voltage() > 4.3
    out_a.set(False)
    time.sleep(0.1)
    assert in_a.get_voltage() < 0.5

@warrior.test
def analog_output_matches():
    out_a.mode(Output.ANALOG)
    for voltage in [0, 0.1, 0.2, 1, 2, 2.5, 3, 3.3, 3.4, 4, 4.8, 4.9, 5]:
        out_a.set(voltage)
        time.sleep(0.1)
        assert abs(in_a.get_voltage() - voltage) < 0.3

warrior.run()
