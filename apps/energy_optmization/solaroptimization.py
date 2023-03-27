import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime, timedelta

class Solaroptimization(hass.Hass):
    def initialize(self):
        self.listen_state(self.optimize, "solar_energy_free", new="on")
        self.listen_state(self.turnoff, "solar_energy_free", new="off")
    
    def optimize(self):
        if (self.get_state("sensor.spot_sell"))<(self.get_state("sensor.spot_cost_low")):
            self.call_service("switch/turn_on", entity_id="switch.varaaja")
    
    
    def turnoff(self):
        self.call_service("switch/turn_off", entity_id="switch.varaaja")



