from attr import attributes
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
        try:
            self.sellmargin=self.args["sellmargin"]
        except KeyError:
            self.sellmargin=0          
        if self.area =='FI':
            self.vat=1.10
            self.tz=pytz.timezone('Europe/Helsinki')
        self.run_in(self.getprices2, 0)
        self.run_in(self.updatecurrentprice, 0)
        self.run_daily(self.getprices2, "13:49:02") #New prices are published to Nordpool around 13:45 EET
        self.run_daily(self.getprices2, "23:55:02") #Update tommorrow to today after nordpool changes to next day
        self.run_daily(self.getprices2, "01:00:02") #Update tommorrow to today after nordpool changes to next day
        hourly_start=datetime.datetime.today().hour+1
        self.run_hourly(self.updatecurrentprice, datetime.time(hourly_start, 0, 1)) #Update prices every hour

    def getprices2 (self,kwargs):
        self.set_state("sensor.nordpooldebug", state="Started today")
        today = []
        try:
            today=self._prepare_values2(self.date())
        except:
            self.set_state("sensor.nordpooldebug", state="Today fetch failed")
            self.run_in(self.getprices2, 300)
        if today:
            self.set_state("sensor.pricetime", state="on", attributes= {"raw": today})
        else: 
            self.set_state("sensor.pricetime", state="off")
            self.run_in(self.getprices2, 300)
        self.set_state("sensor.nordpooldebug", state="Started tomorrow")
        if datetime.datetime.today().hour>=13: 
            tommorrow =[]
            try:
                tommorrow=self._prepare_values2(self.date()+datetime.timedelta(days=1))
            except:
                self.set_state("sensor.nordpooldebug", state="Tommorrow fetch failed")
                self.run_in(self.getprices2, 900) 
            if tommorrow:
                self.set_state("sensor.pricetimetomorrow", state="on", attributes= {"raw": tommorrow, "updated":datetime.datetime.today()})
                self.set_state("sensor.nordpooldebug", state="Tomorrow success")
            else:
                self.set_state("sensor.pricetimetomorrow", state="off", attributes= {"updated": datetime.datetime.today()})
                self.run_in(self.getprices2, 900) # If there is no prices yet check again in 15 minutes
                self.set_state("sensor.nordpooldebug", state="Tomorrow qued")
        else:
            self.set_state("sensor.pricetimetomorrow", state="off", attributes= {"updated": datetime.datetime.today()})
    def updatecurrentprice(self,kwargs): #Get current price once an hour and update it
        values=[]
        templist=[]
        values=self.get_state("sensor.pricetime", attribute="raw")
        if self.get_state("sensor.pricetimetomorrow") == "on":
            values.extend(self.get_state("sensor.pricetimetomorrow", attribute="raw"))
        for i in values:
            if (datetime.datetime.fromisoformat(i['start'])<self.get_now() and datetime.datetime.fromisoformat(i['end'])>self.get_now()):
                self.set_state("sensor.spot_cost", state=i['buy'], attributes={"unit_of_measurement":"snt/kWh"})
                self.set_state("sensor.spot_cost_eur", state=i['buy']/100, attributes={"unit_of_measurement":"eur/kWh"})
                self.set_state("sensor.spot_sell", state=i['sell'], attributes={"unit_of_measurement":"snt/kWh"})
                self.set_state("sensor.spot_sell_eur", state=i['sell']/100, attributes={"unit_of_measurement":"eur/kWh"})
            if (datetime.datetime.fromisoformat(i['start'])>self.get_now()):
                templist.append(i['buy'])
        self.set_state("sensor.spot_cost_low", state=sorted(templist)[0])
    def _prepare_values2(self, dateend) -> list:
        data=elspot.Prices().hourly(end_date=dateend,areas=[self.area])
        priceslisttemp= []
        for item in data['areas'][self.area]['values']:
            if float(item["value"]) != float('inf'):

                i = {
                    "start": (item["start"]).astimezone(self.tz).isoformat(),
                    "end": (item["end"]).astimezone(self.tz).isoformat(),
                    "buy": round(item["value"]/10*self.vat+self.extracost,3), #for buying there is VAT and extra costs added
                    "sell" :round(item["value"]/10-self.sellmargin,3), #Selling price is without VAT and deducting sales margin
                }
                priceslisttemp.append(i)
        return priceslisttemp