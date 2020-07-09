import appdaemon.plugins.hass.hassapi as hass
# import requests
# import json
import datetime
# import dateutil.parser
import pytz
# import asyncio
# import logging
# from collections import defaultdict
from nordpool import elspot

class PriceFetch(hass.Hass):
    def initialize(self):
        self.run_daily(self.getprices, "21:01:01")
        hourly_start=datetime.datetime.today().hour+1
        self.run_hourly(self.updatecurrentprice, time(hourly_start, 0, 1))
        prices_spot = elspot.Prices()
        now = datetime.datetime.now(pytz.utc)
        datatoday = prices_spot.hourly(end_date=date.today(),areas=['FI'])
        for rate in datatoday['areas']['FI']['values']:
            if rate['start'] <= now < rate['end']:        
                self.set_state("sensor.spot_cost", state=round(rate['value']/10*1.24+3.9+2.79372,3))
                self.set_state("sensor.spot_sell", state=round(rate['value']/10,3))
        datatomorrow = prices_spot.hourly(areas=['FI'])
        priceslist = []
        for i in datatoday['areas']['FI']['values']:
            priceslist.append(round(i['value']/10*1.24+3.9+2.79372,3))
        priceslistsorted=sorted(priceslist)
        self.set_state("sensor.spot_cost_today", state=priceslistsorted)
        priceslisttomorrow=[]
        for i in datatomorrow['areas']['FI']['values']:
            priceslisttomorrow.append(round(i['value']/10*1.24+3.9+2.79372,3))
        priceslisttomorrowsorted=sorted(priceslisttomorrow)
        self.set_state("sensor.spot_cost_future", state=priceslisttomorrowsorted)
            
    def getprices(self,kwargs):
        prices_spot = elspot.Prices()
        now = datetime.datetime.now(pytz.utc)
        datatoday = prices_spot.hourly(end_date=date.today(),areas=['FI'])
        datatomorrow = prices_spot.hourly(areas=['FI'])
        priceslisttomorrow = []
        for i in datatomorrow['areas']['FI']['values']:
            priceslisttomorrow.append(round(i['value']/10*1.24+3.9+2.79372,3))
        priceslisttomorrowsorted=sorted(priceslisttomorrow)
        self.set_state("sensor.spot_cost_future", state=priceslisttomorrowsorted)
        if priceslisttomorrow[0] == inf:
            self.run_in(self.getprices, 300)
            
        
    def updatecurrentprice(self,kwargs):
        prices_spot = elspot.Prices()
        now = datetime.datetime.now(pytz.utc)
        datatoday = prices_spot.hourly(end_date=date.today(),areas=['FI'])
        for rate in datatoday['areas']['FI']['values']:
            if rate['start'] <= now < rate['end']:
                self.set_state("sensor.spot_cost", state=round(rate['value']/10*1.24+3.9+2.79372,3))
                self.set_state("sensor.spot_sell", state=round(rate['value']/10,3))