import datetime as dt
from datetime import datetime, timedelta

import appdaemon.plugins.hass.hassapi as hass


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
            self.batterysize=self.args["batterysize"]
            self.targetlevel=self.args["targetlevel"]
            self.currentlevel=self.args["currentlevel"]
            self.chargepower=self.args["chargepower"]
            self.readytime=self.args["readytime"]
            self.dynamicbattery=True
        except KeyError:
            self.dynamicbattery=False        
        try:
            if not self.dynamicbattery:
                self.hours=self.args["hours"]-1         
        except KeyError:
            self.log("Amount of hours not defined")
        try:
              self.expensivelimit=self.args["expensivelimit"]
              self.expensivehours=self.args["expensivehours"]-1
              self.expensivelimitactive= True
        except KeyError:
            self.expensivelimitactive=False
        try:
            self.dynamicentity=self.args["dynamicentity"] 
            self.dynamicvalue=True
        except KeyError:
            self.dynamicvalue=False
        try:   
            self.limitruntime=self.args["limitruntime"]
        except KeyError:
            self.limitruntime="23:58:50"
        try:
            self.hourslimit=self.args["hourslimit"]
        except KeyError:
            self.hourslimit=24
        try:
            self.staticlimit=self.args["staticlimit"]
        except KeyError:
            self.staticlimit=0
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
        try:
            self.timelimitlower=self.args["timelimitlower"]
            self.timelimitupper=self.args["timelimitupper"]+1
        except KeyError:
            self.timelimitlower=0
            self.timelimitupper=24
    
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
                self.high_amount=self.args["high_amount"]
                self.HightempActive=True
            except KeyError:
                self.HightempActive=False
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
            elif self.dynamicbattery:
                hourly_start=datetime.today().hour
                self.run_in(self.updatelimit,5)  
                self.run_hourly(self.updatelimit, dt.time(hourly_start, 55, 0))
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
                    if self.boost and self.entity_exists(self.limitidb) and self.HightempActive:
                        if float(new)<=float(self.get_state(self.limitidb)):
                            self.call_service(self.service_boost, entity_id = self.entity_id, temperature=float(self.get_state(self.temperature))+self.boost_amount) 
                        elif float(new)>float(self.get_state(self.limitid)):
                            self.call_service(self.service_over, entity_id = self.entity_id, temperature=float(self.get_state(self.temperature))+self.high_amount)
                        else:
                            self.call_service(self.service_under, entity_id = self.entity_id, temperature=float(self.get_state(self.temperature)))           
                    elif float(new)<=float(self.get_state(self.limitid)):
                        self.call_service(self.service_under, entity_id = self.entity_id, temperature=float(self.get_state(self.temperature)))
                    else:
                        self.call_service(self.service_over, entity_id = self.entity_id)
            elif self.conditonActive:
                if (float(new)<=float(self.get_state(self.limitid)) and self.get_state(self.conditon) == "on"):
                    if self.selectvalueactive:
                        self.select_option(self.entity_id, self.selectvalueUnder)
                        self.log("Charge car")
                    else:
                        self.call_service(self.service_under, entity_id = self.entity_id)
                    if self.timerActive:
                        if self.get_state(self.timer) == "paused":
                            self.call_service("timer/start", entity_id=self.timer)
                        elif self.get_state(self.timer) == "idle":
                            self.call_service("timer/start", entity_id=self.timer, duration=self.get_state(self.timerduration))
                    elif not self.dynamicbattery:
                        if self.hours<1:
                            self.call_service("input_boolean/turn_off", entity_id = self.conditon)
                else:
                    if self.dynamicbattery:
                        if self.get_state(self.targetlevel)<= self.get_state(self.currentlevel):
                            self.select_option(self.entity_id, self.selectvalueUnder)
                            self.log("Battery full")
                        else:
                            self.select_option(self.entity_id, self.selectvalueOver)
                            self.log("No charging, energy price over limit")
                    elif self.selectvalueactive:
                        self.select_option(self.entity_id, self.selectvalueOver)
                    else:
                        self.call_service(self.service_over, entity_id = self.entity_id)
                    if self.timerActive:
                        self.call_service("timer/pause", entity_id= self.timer)     
            else:
                if ((float(new)<=float(self.get_state(self.limitid)) or float(new)<=float(self.staticlimit)) and self.get_now().hour>=self.timelimitlower and self.get_now().hour<self.timelimitupper):
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
        if self.dynamicbattery:
            self.log(self.get_now().hour)
            self.log(datetime.strptime(self.get_state(self.readytime),'%H:%M:%S').hour)
            if self.get_now().hour>datetime.strptime(self.get_state(self.readytime),'%H:%M:%S').hour:

                self.hourslimit= 24-int(self.get_now().hour)+datetime.strptime(self.get_state(self.readytime),'%H:%M:%S').hour-1
                self.log(self.hourslimit)
                self.log("Ilta")
            else:
                self.hourslimit=datetime.strptime(self.get_state(self.readytime),'%H:%M:%S').hour-self.get_now().hour-1
                self.log(self.hourslimit)
                self.log("Aamu")
        values=[]
        values=self.get_state("sensor.pricetime", attribute="raw")
        if self.get_state("sensor.pricetimetomorrow") == "on":
            values.extend(self.get_state("sensor.pricetimetomorrow", attribute="raw"))
        templist=[]
        for i in values:
            if (datetime.fromisoformat(i['start'])>self.get_now() and datetime.fromisoformat(i['start'])<self.get_now()+timedelta(hours=self.hourslimit) and datetime.fromisoformat(i['start']).hour>=self.timelimitlower and datetime.fromisoformat(i['start']).hour<self.timelimitupper):
                templist.append(i['buy'])
        if not self.dynamicvalue and not self.dynamicbattery:
            self.set_state(self.limitid, state=sorted(templist)[self.hours])
        if self.expensivelimitactive:
            if sorted(templist)[self.hours]>self.expensivelimit:
                self.set_state(self.limitid, state=sorted(templist)[self.expensivehours])
        elif self.dynamicbattery:
            targetlevel=int(self.get_state(self.targetlevel))
            currentlevel=int(self.get_state(self.currentlevel))
            try:
                self.set_state(self.limitid, state=sorted(templist)[int((self.batterysize*((targetlevel-currentlevel)/100)/float(self.chargepower)))])
            except:
                self.set_state(self.limitid, state=sorted(templist)[-1])
            self.log(sorted(templist))
            self.log(self.get_state(self.limitid))
            self.log(currentlevel)
            self.log(targetlevel)
            self.log(int((self.batterysize*((targetlevel-currentlevel)/100)/float(self.chargepower))))
        elif self.dynamicvalue:
            if self.get_state(self.dynamicentity)=="on":       
                self.set_state(self.limitid, state=sorted(templist)[self.hours])
        if self.away:
            if self.get_state(self.awayid)==self.awaystatus:
                self.set_state(self.limitid, state=sorted(templist)[self.awayhours]) 
        if self.domain== "climate": 
            if self.boost:
                self.set_state(self.limitidb, state=sorted(templist)[self.hoursBoost])