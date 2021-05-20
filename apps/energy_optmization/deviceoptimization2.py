import appdaemon.plugins.hass.hassapi as hass
from datetime import timedelta, datetime
import time

class Deviceoptimization2(hass.Hass):
    def initialize(self):
        self._initialize(self)
    def _initialize(self, kwargs):   
        try:
            self.entity_id=self.args["entity_id"]
            self.domain=self.entity_id.split('.')[0]
            self.limitid="sensor.limit"+self.args["entity_id"].replace('.','_')
        except KeyError:
            self.log("Entity_id not defined")
        try:
            self.hours=self.args["hours"]-1         
        except KeyError:
            self.log("Amount of hours not defined")
        try:
            self.dynamicentity=self.args["dynamicentity"] 
            self.dynamicvalue=True
        except KeyError:
            self.dynamicvalue=False
        try:   
            self.limitruntime=self.args["limitruntime"]
        except KeyError:
            self.limitruntime="23:59:50"
        try:
            self.hourslimit=self.args["hourslimit"]
        except KeyError:
            self.hourslimit=24
        try:
            self.selectvalueUnder=self.args["selectvalueUnder"]
            self.selectvalueOver=self.args["selectvalueOver"]
            self.selectvalueactive=True
        except KeyError:
            self.selectvalueactive=False
        try:
            self.service_under=self.args["service_under"]
        except KeyError:
            if self.selectvalueactive == False: 
                self.log("Service under not defined")
        try:
            self.service_over=self.args["service_over"]
        except KeyError:
            if self.selectvalueactive == False: 
                self.log("Service over not defined")
        try:
            self.timer=self.args["timer"]
            self.timerduration=self.args["timerduration"]
            self.timerActive=True
        except KeyError:
            self.timerActive=False
        try:
            self.conditon=self.args["condition"]
            self.conditonActive=True
            self.conditionset=True
        except KeyError:
            self.conditonActive=False
        try:
            self.awayhours=self.args["awayhours"]-1
            self.awayid=self.args["awayid"]      
            self.awaystatus=self.args["awaystatus"]
            self.away=True
        except KeyError:
            self.away=False
        if self.domain== "climate":
            try:
                self.hoursBoost=self.args["hoursBoost"]-1
                self.limitidb="sensor.limitb"+self.args["entity_id"].replace('.','_')
                self.boost=True
            except KeyError:
                self.log("Amount of boost hours not defined, boost disabled")
                self.boost=False        
            try:
                self.service_boost=self.args["service_boost"]
            except KeyError:
                self.log("Service boost not defined, boost disabled")
                self.boost=False
            try:
                self.boost_amount=self.args["boost_amount"]
            except KeyError:
                self.boost_amount=1
            try:
                self.temperature=self.args["temperature"]
            except KeyError:
                self.log("Target temperature not defined, boost disabled")
                self.boost=False 
        if self.get_state("sensor.pricetime") == "on":
            Pricesfound=True
        else:    
            Pricesfound=False
            self.run_in(self._initialize, 10)
        if Pricesfound:
            self.listen_state(self.callservice, "sensor.spot_cost")
            if self.dynamicvalue:
                self.listen_state(self.updatelimitdynamic, self.dynamicentity)
                self.run_daily(self.updatelimit, self.limitruntime) #Needed to force run dynamic entities on away mode
                if self.get_state(self.dynamicentity)=="on":
                    self.run_in(self.updatelimit, 5)
            else:
                self.run_in(self.updatelimit,5)      
                self.run_daily(self.updatelimit, self.limitruntime)
    
    def callservice(self, entity, attribute, old, new, kwargs):
        if self.entity_exists(self.limitid):
            if self.away:
                if self.get_state(self.awayid) == self.awaystatus:
                    self.conditonActive=False
                elif self.conditionset:
                    self.conditonActive=True
            if self.domain == "climate":
                if self.get_state(self.entity_id) != "fan_only":
                    if self.boost and self.entity_exists(self.limitidb):
                        if float(new)<=float(self.get_state(self.limitidb)):
                            self.call_service(self.service_boost, entity_id = self.entity_id, temperature=float(self.get_state(self.temperature))+self.boost_amount) 
                        else:
                            self.call_service(self.service_boost, entity_id = self.entity_id, temperature=float(self.get_state(self.temperature)))
                    if float(new)<=float(self.get_state(self.limitid)):
                        self.call_service(self.service_under, entity_id = self.entity_id)
                    else:
                        self.call_service(self.service_over, entity_id = self.entity_id)
            elif self.conditonActive:
                if (float(new)<=float(self.get_state(self.limitid)) and self.get_state(self.conditon) == "on"):
                    if self.selectvalueactive:
                        self.select_option(self.entity_id, self.selectvalueUnder)
                    else:
                        self.call_service(self.service_under, entity_id = self.entity_id)
                    if self.timerActive:
                        if self.get_state(self.timer) == "paused":
                            self.call_service("timer/start", entity_id=self.timer)
                        elif self.get_state(self.timer) == "idle":
                            self.call_service("timer/start", entity_id=self.timer, duration=self.get_state(self.timerduration))
                    else:
                        self.call_service("input_boolean/turn_off", entity_id = self.conditon)
                else:
                    if self.selectvalueactive:
                        self.select_option(self.entity_id, self.selectvalueOver)
                    else:
                        self.call_service(self.service_over, entity_id = self.entity_id)
                    if self.timerActive:
                        self.call_service("timer/pause", entity_id= self.timer)     
            else:
                if float(new)<=float(self.get_state(self.limitid)):
                    if self.selectvalueactive:
                        self.select_option(self.entity_id, self.selectvalueUnder)
                    else:
                        self.call_service(self.service_under, entity_id = self.entity_id)
                else:
                    if self.selectvalueactive:
                        self.select_option(self.entity_id, self.selectvalueOver)
                    else:
                        self.call_service(self.service_over, entity_id = self.entity_id)
    
    def updatelimitdynamic(self, entity, attribute, old, new, kwargs):
        self.run_in(self.updatelimit, 1)

    def updatelimit(self, kwargs):
        values=[]
        values=self.get_state("sensor.pricetime", attribute="raw")
        if self.get_state("sensor.pricetimetomorrow") == "on":
            values.extend(self.get_state("sensor.pricetimetomorrow", attribute="raw"))
        templist=[]
        for i in values:
            if (datetime.fromisoformat(i['start'])>self.get_now() and datetime.fromisoformat(i['start'])<self.get_now()+timedelta(hours=self.hourslimit)):
                templist.append(i['value'])
        if not self.dynamicvalue:
            self.set_state(self.limitid, state=sorted(templist)[self.hours])
        elif self.get_state(self.dynamicentity)=="on":       
            self.set_state(self.limitid, state=sorted(templist)[self.hours])
        if self.away:
            if self.get_state(self.awayid)==self.awaystatus:
                self.set_state(self.limitid, state=sorted(templist)[self.awayhours]) 
        if self.domain== "climate": 
            if self.boost:
                self.set_state(self.limitidb, state=sorted(templist)[self.hoursBoost])