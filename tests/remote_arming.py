import time
import warrior
from warrior import test, expect

hilt = warrior.find_hilt()

# Connect between the 9V batteries and RA's battery inputs
bat_1, bat_2 = warrior.AnalogInput(hilt[1])
# Connect in place of the mag switches
mag_1, mag_2 = warrior.AnalogInput(hilt[2])
# Connect to altimiter power provided by RA
alt_1, alt_2 = warrior.AnalogInput(hilt[3])
# Connect to drogue pyro negative channels
drogue_1, drogue_2 = warrior.Output(hilt[4])
# Connect to main pyro negative channels
main_1, main_2 = warrior.Output(hilt[5])
# Connect between 5V and RA's 5V input from its CAN connector
can_5v, _ = warrior.AnalogInput(hilt[6])
# Connect to the stratologger UART data line
# uart, _ = warrior.Output(hilt[7])

@test.nominal
def nominal():
    expect.equal(bat_1.get_voltage(), 3, tolerance=2)
    #expect.equal(bat_2.get_voltage(), 9, tolerance=1)
    bat_1.set_connected(True)
    bat_2.set_connected(True)
    mag_1.set_connected(False)
    mag_2.set_connected(False)
    drogue_1.set(False)
    drogue_2.set(False)
    main_1.set(False)
    main_2.set(False)
    can_5v.set_connected(True)
    status = hilt.get_can_message(1, board_id="ARMING", msg_type="E_NOMINAL")
    expect.non_none(status)
    expect.equal(status["data"]["status"], "E_NOMINAL")

@test
def battery_voltage_sense():
    pass

warrior.run()
