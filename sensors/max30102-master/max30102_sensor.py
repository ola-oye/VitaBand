import json
import max30102
import hrcalc
import time

m = max30102.MAX30102()

def read_sensor():
    while True:
        red, ir = m.read_sequential()
        hr, hr_valid, spo2, spo2_valid = hrcalc.calc_hr_and_spo2(ir, red)

        if hr_valid and spo2_valid:
            print(json.dumps({
                "heart_rate": round(hr, 2),
                "spo2": round(spo2, 2)
            }), flush=True)
        else:
            print(json.dumps({
                "heart_rate": None,
                "spo2": None
            }), flush=True)

        time.sleep(1)

if __name__ == "__main__":
    read_sensor()


