'''
Control of DASI FPI's etalon temperature sensor using a Adafruit ADS1015 board and raspberryPI.

Author. L Navarro
Date: 16 Sep 2021
'''
from Adafruit_ADS1x15 import ADS1015
import numpy as np
from datetime import datetime,timedelta
from time import sleep
import os
import pytz
class TemperatureSensor:
    
    def __init__(self,address=0x48,busnum=None,
                gain=1,channel=0,
                integration_secs=60,output_path=None):
        self.integration_time=timedelta(seconds=integration_secs)
        self.adc=ADS1015(address=address,busnum=busnum)
        self.gain=gain
        self.channel=channel
        self.output_path="/home/pi/src/temperature.csv"
        self.__recycle_file=False
        self.__val2volt=lambda val:8.8*val/2048.
        self.__val2temp=lambda val:self.__val2volt(val)*6.625-3.969
        if not os.path.exists(self.output_path):
              self.save_header()
    
    def save_header(self,):
        with open(self.output_path, "w") as obj:
            line="date,value,std,temp,std\n"
            obj.write(line)
    
    def get_reading(self):
        readings=[]
        start=datetime.now(tz=pytz.utc)
        while (datetime.now(tz=pytz.utc)-start)<=self.integration_time:
            value=self.adc.get_last_result()
            readings.append(value)
            sleep(0.5)
        dt=start+self.integration_time/2.
        val=np.nanmedian(readings)
        std=np.nanstd(readings)
        ts=list(map(self.__val2temp,readings))
        tval=np.nanmedian(ts)
        tstd=np.nanstd(ts)
        return dt,val,std,tval,tstd
    
    def save_reading(self,dt,val,std,temp,tstd):
        if self.__recycle_file:
            self.__recycle_file=False
            self.save_header()
        with open(self.output_path, "a") as obj:
            line="%s,%i,%.3f,%.3f,%.3f\n"%(dt.strftime("%Y/%m/%d %H:%M:%S"),val,std,temp,tstd)
            obj.write(line)
        
    def read_continuously(self):
        now=datetime.now()
        
        self.adc.start_adc(self.channel,gain=self.gain)
        
        while True:
            vals=self.get_reading()
            self.save_reading(*vals)
            if (datetime.now()-now).days>=7:
                self.__recycle_file=True
                now=datetime.now()

if __name__ == "__main__":
    obj=TemperatureSensor()
    obj.read_continuously()
    


























