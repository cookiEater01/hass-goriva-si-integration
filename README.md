# Home Assistant integration for [goriva.si](https://www.goriva.si)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

## Installation:

Navigate to [HACS](https://hacs.xyz/) (Home Assistant Community Store) in HomeAssistant, open integrations, and add custom repository.

## Usage:

Add the folowing to the configuration.yaml:

| Parameter | Required | Value type | Description |
| :---: | :---: | :---: | :---: |
| location | true | string | Location from which to serach for petrol station |
| radius | true | int | Search radius from location |
| fuel_types | false | string-array | Available options: ["95", "dizel", "98", "100", "dizel-premium", "autoplin-lpg", "KOEL"] |
only_station | false | int-array | Only create entry for stations with the following ids. |

You can get stations id from [goriva.si](https://www.goriva.si). You need to open developer tools and find the correct API call in network tab.

### Example from configation.yaml:

```
goriva_si:
  location: "Lipe Slovenia"
  radius: 7000
  fuel_types:
    - "95"
    - "dizel"
  only_stations:
    - 2292
    - 2302
    - 770
    - 2052
    - 1590
```