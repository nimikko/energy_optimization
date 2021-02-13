import appdaemon.plugins.hass.hassapi as hass

class Deviceoptimization2(hass.Hass):
    def initialize(self):
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
            self.service_under=self.args["service_under"]
        except KeyError:
            self.log("Service under not defined")
        try:
            self.service_over=self.args["service_over"]
        except KeyError:
            self.log("Service over not defined")       
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

        
        
        future=self.get_state("sensor.spot_cost_today")
        futurelist=future.replace('[','').replace(']','').split(", ")
        self.set_state(self.limitid, state=futurelist[self.hours])
        if self.domain== "climate": 
            if self.boost:
                self.set_state(self.limitidb, state=futurelist[self.hoursBoost])
        self.listen_state(self.callservice, "sensor.spot_cost")
        self.listen_state(self.updatelimitday, "sensor.spot_cost_today")
        self.run_daily(self.updatelimitnight, "00:55:00")
    
    def callservice(self, entity, attribute, old, new, kwargs):
        if self.domain == "climate":
            if self.get_state(self.entity_id) != "fan_only":
                if float(new)<=float(self.get_state(self.limitidb)) and self.boost:
                    self.call_service(self.service_boost, entity_id = self.entity_id, temperature=float(self.get_state(self.temperature))+self.boost_amount) 
                if float(new)>float(self.get_state(self.limitidb)) and self.boost:
                    self.call_service(self.service_boost, entity_id = self.entity_id, temperature=float(self.get_state(self.temperature)))
                if float(new)<=float(self.get_state(self.limitid)):
                    self.call_service(self.service_under, entity_id = self.entity_id)
                if float(new)>float(self.get_state(self.limitid)):
                    self.call_service(self.service_over, entity_id = self.entity_id)
        else:
            if float(new)<=float(self.get_state(self.limitid)):
                self.call_service(self.service_under, entity_id = self.entity_id)
            if float(new)>float(self.get_state(self.limitid)):
                self.call_service(self.service_over, entity_id = self.entity_id)
    
    def updatelimitnight(self, kwargs):
        future=self.get_state("sensor.spot_cost_future")
        futurelist=future.replace('[','').replace(']','').split(", ")
        self.set_state(self.limitid, state=futurelist[self.hours])
        if self.domain== "climate": 
            if self.boost:
                self.set_state(self.limitidb, state=futurelist[self.hoursBoost])

    def updatelimitday(self, entity, attribute, old, new, kwargs):
        future=self.get_state("sensor.spot_cost_today")
        futurelist=future.replace('[','').replace(']','').split(", ")
        if self.get_state(self.limitid) == float('inf'):
            self.set_state(self.limitid, state=futurelist[self.hours])
        if self.domain== "climate":
            if self.boost:
                if self.get_state(self.limitid) == float('inf'):
                    self.set_state(self.limitidb, state=futurelist[self.hoursBoost])