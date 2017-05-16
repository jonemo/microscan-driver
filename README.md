# microscan-driver

[![Build Status](https://travis-ci.org/jonemo/microscan-driver.svg?branch=master)](https://travis-ci.org/jonemo/microscan-driver)

Python driver for Microscan barcode readers

The author of this software is not affiliated with Microscan Systems Inc.

"Microscan" and "MS3" are trademarks of Microscan Systems Inc. and are used in this software and its accompanying documentation to the benefit of the trademark owner, with no intention of infringement.


## How to install

Clone this git repository or download the repository as a [zip package](https://github.com/jonemo/microscan-driver/archive/master.zip) and extract.
Then, from the root folder of the repository, run

```
$ python setup.py install
```

Depending on your setup and environment, you might want to consider doing so inside a [virtualenv](https://virtualenv.pypa.io/).

This package only has a single requirement (which is automatically installed when running the above command):
The [`pyserial` library](https://pythonhosted.org/pyserial/) provides access to the serial port and is implemented in pure Python.
In other words: This driver does not use any C extensions and should work in many Python implementations.


## How to run unit tests

From the root folder of the repo, run:

```
$ python -m unittest
```

No additional dependencies are required.


## Supported devices

Currently, this library aims to implement all features documented in the MS3device user manual (with exceptions listed below).


## Not (yet) supported features

### Specific Settings

The configuration settings listed below are not currently implemented in this library.

* For the Host Port Protocol setting, the values "Multidrop", "User Defined", and "User Defined Multidrop" are not supported
* Matchcode (all functionality described in chapter 7 of the user manual)

A workaround for applications that require these features, is to send the corresponding configuration strings directly using the `MicroscanDriver.send_string()` method.

### General Functionality

No sanity checking is performed on the combinations of settings in a configuration. Only individual settings and their subsettings are (to limited degree) validated against the specification.
