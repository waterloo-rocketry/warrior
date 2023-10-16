import time
import warrior
from warrior import test, expect

hilt = warrior.find_hilt()

out_a, out_b = warrior.Output(hilt[10])
in_a, in_b = warrior.AnalogInput(hilt[9])


@test
def gets_can_message():
    status = hilt.get_can_message(1, board_id="ANY", msg_type="GENERAL_BOARD_STATUS")
    expect.non_none(status)
"""
@test
def digital_output_matches():
    out_a.mode(out_a.DIGITAL)
    out_a.set(True)
    time.sleep(0.1)
    expect.equal(in_a.get_voltage(), 5, tolerance=0.7)
    out_a.set(False)
    time.sleep(0.1)
    expect.equal(in_a.get_voltage(), 0, tolerance=0.5)

@test
def analog_output_matches():
    out_a.mode(out_a.ANALOG)
    for voltage in [0, 0.1, 0.2, 1, 2, 2.5, 3, 3.3, 3.4, 4, 4.8, 4.9, 5]:
        out_a.set(voltage)
        time.sleep(0.1)
        expect.equal(in_a.get_voltage(), voltage, tolerance=0.3)
"""

warrior.run()
