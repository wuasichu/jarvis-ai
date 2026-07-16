import wmi


def set_brightness_windows(percentage: int):
    w = wmi.WMI(namespace='wmi')
    brightness_methods = w.WmiMonitorBrightnessMethods()[0]
    brightness_methods.WmiSetBrightness(int(percentage), 0)
