from logging.handlers import TimedRotatingFileHandler
import requests
import urllib.parse
import datetime as dt
from datetime import datetime, timedelta
from attr import attributes
import appdaemon.plugins.hass.hassapi as hass

class Windpower(hass.Hass):
    def initialize(self):
        try:
            self.apikey=self.args["fingridapikey"]
        except KeyError:
            self.log("Fingrid api key is needed")
        self.run_in(self.fetchwindpower, 0)
        hourly_start=datetime.today().hour
        self.run_hourly(self.fetchwindpower, dt.time(hourly_start, 0, 1))
   
   
    def fetchwindpower(self,kwargs):   
        Start=datetime.today()+timedelta(hours=-24)
        End=datetime.today()
        self._storevalue("sensor.windpowertoday", Start, End)
        Start=datetime.today()
        End=datetime.today()+timedelta(hours=24)
        self._storevalue("sensor.windpowertomorrow", Start, End)
        Start=datetime.today()+timedelta(hours=24)
        End=datetime.today()+timedelta(hours=48)
        self._storevalue("sensor.windpowerdayafter", Start, End)


    def _storevalue(self, sensor, start, end):
        
        URL="https://api.fingrid.fi/v1/variable/245/events/json?start_time="+urllib.parse.quote(str(start.astimezone().isoformat("T","seconds")))+"&end_time="+urllib.parse.quote(str(end.astimezone().isoformat("T","seconds")))
        PARAMS= {'x-api.key':self.apikey}
        r = requests.get(url = URL, params = PARAMS)
        data=r.json()
        self.set_state(sensor, state="on", attributes= {"raw": data})
