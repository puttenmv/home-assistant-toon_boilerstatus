[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)  [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/cyberjunkynl/)

# Toon Boiler Status Sensor Component
This is a Custom Component for Home-Assistant (https://home-assistant.io) that reads and displays the boiler status values from a rooted Toon thermostat.

NOTE: This component only works with rooted Toon devices.
Toon thermostats are available in The Netherlands and Belgium.

More information about rooting your Toon can be found here:
[Eneco Toon as Domotica controller](http://www.domoticaforum.eu/viewforum.php?f=87)

This fork is modified so that you do not need to install ToonStore and the BoilerStatus app, which helps if you have a first generation Toon with memory constraints.

## Installation

- Copy directory `custom_components/toon_boilerstatus` to your `<config dir>/custom_components` directory.
- Configure with config below.
- Restart Home-Assistant.

## Usage
To use this component in your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry

sensor:
  - platform: toon_boilerstatus
    name: Toon
    host: IP_ADDRESS
    port: 80
    scan_interval: 10
    resources:
      - boilersetpoint
      - boilerintemp
      - boilerouttemp
      - boilerpressure
      - boilermodulationlevel
      - roomtemp
      - roomtempsetpoint
```

Configuration variables:

- **name** (*Optional*): Prefix name of the sensors. (default = 'Toon')
- **host** (*Required*): The IP address on which the Toon can be reached.
- **port** (*Optional*): Port used by your Toon. (default = 80)
- **scan_interval** (*Optional*): Number of seconds between polls. (default = 10)
- **resources** (*Required*): This section tells the component which values to display and monitor.

By default the values are displayed as badges.

If you want them grouped instead of having the separate sensor badges, you can use these entries in your `groups.yaml`:

```yaml
# Example groups.yaml entry

Boiler Status:
  - sensor.toon_boiler_intemp
  - sensor.toon_boiler_outtemp
  - sensor.toon_boiler_setpoint
  - sensor.toon_boiler_pressure
  - sensor.toon_boiler_modulation
  - sensor.toon_room_temp
  - sensor.toon_room_temp_setpoint
```

## Screenshots

![alt text](https://github.com/cyberjunky/home-assistant-toon_boilerstatus/blob/master/screenshots/toon-boilerstatus.png?raw=true "Screenshot Toon Boiler Status")

## Debugging

Add the relevant lines below to the `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.toon_boilerstatus: debug
```

## Donation
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/cyberjunkynl/)
