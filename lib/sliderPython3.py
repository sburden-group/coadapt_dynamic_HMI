#!/usr/bin/python
# -*- coding: utf-8 -*-

import serial
from time import sleep
import numpy as np
import struct
import serial.tools.list_ports

COM_PORT = 'COM4'
#COM_PORT = '/dev/tty.usbmodem141121'

encoding = 'ascii'

class sliderUSB():

    def __init__(self, port=COM_PORT, debugMode = False):

        self.arduinoSerial = serial.Serial(port = port, baudrate = 9600,#115200,
        timeout=0.1,
        bytesize=serial.EIGHTBITS)
        self.data = np.array([])
        self.debugMode = debugMode

    def __del__(self):
        self.clearUSBRecBuffer()

    def clearUSBRecBuffer(self):
        while (self.arduinoSerial.inWaiting()):
            self.arduinoSerial.read()
        if self.debugMode:
            print ('USB received buffer cleared\n')

    def startArduino(self):
        self.stopArduino()
        self.clearUSBRecBuffer()
        self.arduinoSerial.write(bytearray('a',encoding))
        if self.debugMode:
            print ('Arduino started.\n')

    def stopArduino(self):
        self.arduinoSerial.write(bytearray('A',encoding))
        if self.debugMode:
            print ('Arduino stopped.\n')

    def grabData(self):
        self.arduinoSerial.write(bytearray('g',encoding))
        while(self.arduinoSerial.inWaiting()<8):
            pass
        self.data = struct.unpack('<fI', self.arduinoSerial.read(8))
        return self.data

if __name__ == '__main__':
    #arduinoPorts = [p.device
    #for p in serial.tools.list_ports.comports()
    #if 'Arduino' in p.description
    #]

    sliderJoystick = sliderUSB(port=COM_PORT)

    sliderJoystick.startArduino()
    print ('phase 1')
    for n in range(0,200):
        print (sliderJoystick.grabData())     #or append it to your other data or whatever
        sleep(1./50.)

    #sleep(3)
    #print('Slept Some')

    #for n in range(0,20):
    #    print sliderJoystick.grabData()
    sliderJoystick.stopArduino()

    # sleep(5)
    # # sleep(2.5)
    # # print sliderJoystick.grabData()
    # # sleep(2.5)
    # print 'phase2'
    # sliderJoystick.startArduino()
    # for n in range(0,1000):
    #     print sliderJoystick.grabData()     #or append it to your other data or whatever
    # sliderJoystick.stopArduino()
