# Very rudimentary (and dirty) multi-smile plugwise

All files should be placed in your `custom_components/plugwise_dev` folder

Basic changes to laetificat/anna-ha and bouwew/plugwise_dev include:

 - Making it multi-device capable (although still only smile supported now)
 - Migrating sensor data (illuminance, boiler temp and water pressure) to individual sensor entities
 - Outdoor temperature is available as attribute from the cliamte entitiy but also as sensor entity

Todo

 - Check if this is what we envision
 - Alignment with HA upstream
 - How to change haanna so we can `self._api.get['illuminance']` instead of `self._api.get_illuminance` so we can call dynamically
 - In case of doubt on above statement, see fugly if statements in the sensor class :)
 - Return correct ICON per sensor (i.e. make better use of device-class)
 - Rework bouwew's work of async (just switched to sync to align with other examples, should be back to async)
 - ...


Include like (`configuration.yaml`)


```
plugwise_dev:
  smile:
    - name: Some Anna
      password: abcdefg
      host: 10.9.8.7
    - name: Other Anna
      password: abcdefg
      host: 10.9.8.6
```

