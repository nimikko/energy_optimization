import appdaemon.plugins.hass.hassapi as hass

class Deviceoptimization(hass.Hass):
    def initialize(self):
        future=self.get_state("sensor.spot_cost_today")
        futurelist=future.replace('[','').replace(']','').split(", ")
        self.set_state("sensor.testlimit", state=futurelist[3])
        self.listen_state(self.turnon, "sensor.spot_cost")
        self.listen_state(self.updatelimitday, "sensor.spot_cost_today")
        self.run_daily(self.updatelimitnight, "00:55:00")
    
    def turnon(self, entity, attribute, old, new, kwargs):
        if float(new)<=float(self.get_state("sensor.testlimit")):
            self.log("Device on, price is {} and limit {}".format(new,self.get_state("sensor.testlimit")))
            self.call_service("switch/turn_on", entity_id = "switch.varaaja")
        if float(new)>float(self.get_state("sensor.testlimit")):
            self.call_service("switch/turn_off", entity_id = "switch.varaaja")
    
    def updatelimitnight(self, kwargs):
        future=self.get_state("sensor.spot_cost_future")
        futurelist=future.replace('[','').replace(']','').split(", ")
        self.set_state("sensor.testlimit", state=futurelist[3])

    def updatelimitday(self, entity, attribute, old, new, kwargs):
        future=self.get_state("sensor.spot_cost_today")
        futurelist=future.replace('[','').replace(']','').split(", ")
        if self.get_state("sensor.testlimit") == float('inf'):
            self.set_state("sensor.testlimit", state=futurelist[3])