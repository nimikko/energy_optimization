import appdaemon.plugins.hass.hassapi as hass
import datetime
import pytz
from nordpool import elspot

class PriceFetch2(hass.Hass):
    def initialize(self):
        try:
            self.area=self.args["area"]
        except KeyError:
            self.area='FI'
        try:
            self.extracost=self.args["extracost"]
        except KeyError:
            self.extracost=0
        if self.area =='FI':
            self.vat=1.24
            self.tz=pytz.timezone('Europe/Helsinki')
        self.run_in(self.getprices2, 0)
        self.run_in(self.updatecurrentprice, 0)
        self.run_daily(self.getprices2, "13:32:02") #New prices are published to Nordpool around 13:30 EET
        self.run_daily(self.getprices2, "01:00:02") #Update tommorrow to today after nordpool changes to next day
        hourly_start=datetime.datetime.today().hour+1
        self.run_hourly(self.updatecurrentprice, datetime.time(hourly_start, 0, 1)) #Update prices every hour

    def getprices2 (self,kwargs):
        today = []
        today=self._prepare_values2(self.date())
        if today:
            self.set_state("sensor.pricetime", state="on", attributes= {"raw": today})
        else: 
            self.set_state("sensor.pricetime", state="off")
        tommorrow =[]
        tommorrow=self._prepare_values2(self.date()+datetime.timedelta(days=1))
        if tommorrow:
            self.set_state("sensor.pricetimetomorrow", state="on", attributes= {"raw": tommorrow})
        else:
            self.set_state("sensor.pricetimetomorrow", state="off")
            if datetime.datetime.today().hour>10: # only check again during afternoon, Today() is in UTC time
                self.run_in(self.getprices2, 300) # If there is no prices yet check again in 5 minutes
        
    def updatecurrentprice(self,kwargs): #Get current price once an hour and update it
        values=[]
        values=self.get_state("sensor.pricetime", attribute="raw")
        if self.get_state("sensor.pricetimetomorrow") == "on":
            values.extend(self.get_state("sensor.pricetimetomorrow", attribute="raw"))
        for i in values:
            if (datetime.datetime.fromisoformat(i['start'])<self.get_now() and datetime.datetime.fromisoformat(i['end'])>self.get_now()):
                self.set_state("sensor.spot_cost", state=i['value'])
    
    def _prepare_values2(self, dateend) -> list:
        data=elspot.Prices().hourly(end_date=dateend,areas=[self.area])
        priceslisttemp= []
        for item in data['areas'][self.area]['values']:
            if float(item["value"]) != float('inf'):

                i = {
                    "start": (item["start"]).astimezone(self.tz).isoformat(),
                    "end": (item["end"]).astimezone(self.tz).isoformat(),
                    "value": round(item["value"]/10*self.vat+self.extracost,3),
                }
                priceslisttemp.append(i)
        return priceslisttemp