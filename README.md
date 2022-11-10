# Energy optimization

Appdaemon for home assistant to control devices to run when energy price is lowest.

Prices are fetched from Nordpool API using python library  https://github.com/kipe/nordpool

## Price fetch
Pricefetch need to be running before the device optimization can run

**Parameters**

| Name          | Usage         |
| -----------   |-------------  |
|area           |Nordpool area where prices are fetched|
|extracost      |Amount of extra costs to be added on to of the price|

**Example app**

For fetching electric prices from Nordpool
>EPrice:  
  module: pricefetch2  
  class: PriceFetch2  
  extracost: 6.69372  
  area: FI  
  priority: 1

For fetching windpower estimates from Fingrid
>Windpower:  
  module: wind  
  class: Windpower  
  apikey: !secret fingridapikey  