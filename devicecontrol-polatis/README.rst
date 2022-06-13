=====================
devicecontrol-polatis
=====================


Small Python 3 library that allows the developer to send commands to Optical
Cross-Connectors from Polatis, through SCPI, while exposing a high level API.


Installation
============

Please make sure your Python version is greater than or equal to 3.4 (the
library itself is tested with Python 3.7), and use standard tools like ``pip``
to install ``devicecontrol-polatis`` If you don't have access to a package
index, you can install it directly from Github, for example:

.. code:: bash

    $ pip install git+ssh://git@github.com/hpn-bristol/devicecontrol-polatis.git@master#egg=devicecontol-polatis
    # Or if you prefer http:
    $ pip install git+https://github.com/hpn-bristol/devicecontrol-polatis.git


Quick Start
===========

Given a Polatis OXC Switch is properly setup to expose a SCPI interface on a
specific port, e.g. 5025, of an specific IP address, e.g. 192.168.0.3; the
developer can do:

.. code:: python

    from devicecontrol.polatis import Oxc

    IP_ADDR = "192.168.0.3"
    PORT = 5025

    polatis = Oxc(IP_ADDR, PORT)

    # Test communication channel and retrieve device specification and version:
    polatis.idn
    # => ('Polatis', 'N-VST-192x192-LA1-DMHNV-701', '001705', '6.5.1.7')

    # Retrieve number of ports in the device: (input, output)
    polatis.number_of_ports
    # => (192, 192)
    polatis.ports
    # => ([1, 2, ... 192], [193, 194, ..., 384])

    # Retrieve current connections:
    polatis.connections
    # => {}

    # Add new connections:
    polatis.connect({1: 193, 25: 195})
    polatis.connections
    # => {1: 193, 25: 195}
    polatis.connect({3: 194})
    polatis.connections
    # => {1: 193, 4:194, 25: 195}

    # Get power level readings:
    polatis.get_power([193, 194, 197])
    # => {193: -29.55, 194: -30.05, 197: -29.85}

    # Get all available power level readings:
    polatis.power
    # => {1: -29.55, 2: -30.05, ...}

    # Remove connections
    polatis.disconnect({1: 193, 4: 194})
    polatis.connections
    # => {25: 195}

    # Replace connections
    polatis.connections = {1: 201, 7: 207}
    polatis.connections
    # => {1: 201, 7: 207}

    # Remove all connections
    polatis.disconnect_all()
    polatis.connections
    # => {}

Notice that the argument for ``connect`` is a dictionary where keys and values
will be connected. The same representation is used when listing active
connections.
Moreover each model of the device presents limitations of which ports can be
connected (for example, in a device with 384 ports, ports from 1 to 192 can be
connected to ports from 193 to 384, but not between themselves). Therefore, if
you are able to call ``polatis.idn`` but the connections are not being
stablished, it might be worth to check if the connection between the specified
ports is valid from the device perspective.


Polatis Agent
===========

This agent should run on a PC connected to the same network of the Polatis to be controlled.

+ Server side:
  + navigate to ```installation_folder/devicecontrol-polatis/src/devicecontrol/polatis/```
  + start oxc_server.py as root: ```python3 oxc_server.py```

+ Client side:
  + import ```from devicecontrol.polatis import oxc_api```

# Examples:

All functions require the server ip and port.

.. code:: python

    from devicecontrol.polatis import oxc_api
	
    server_ip = '127.0.0.1'
    server_port = 25025
    polatis_ip = '137.222.204.36'

    # Test communication with the server.
    oxc_api.is_up(server_ip, server_port)
    # => True
    
    # From now on, all functions need the polatis ip in addition to the server's ip/port
    
    # Test communication with a particular Polatis
    oxc_api.idn(polatis_ip, server_ip, server_port)
    # => ['Polatis', 'N-VST-192x192-LU1-DMHNV-801', '001310', '5.1.9.18-2.3.1']
    
    # Add cross-connections
    connections_dict = {1:194, '2': 193, '3': '195'}
    oxc_api.connect(polatis_ip, connections_dict, server_ip, server_port)
    # => 'Ok.'
    
    # Check cross-connections
    oxc_api.connections(polatis_ip, server_ip, server_port)
    # => {'1': 194, '2': 193, '3': 195}
    
    # Remove cross-connections
    connections_dict = {1:194, '2': 193}
    oxc_api.disconnect(polatis_ip, cons, server_ip, server_port)
    # => 'Ok.'
    oxc_api.connections(polatis_ip, server_ip, server_port)
    # => {'3': 195}
    
    # Get power from selected ports
    port_list = [193, 2] # only some polatis suport power measurement on input ports
    oxc_api.get_power(polatis_ip, port_list, server_ip, server_port)
    # => {'193': -30.04, '2': -29.66}


Slicing (*Experimental*)
------------------------

This library implements slicing capabilities for Polatis OXC through the
``VirtualOxc`` class. This class implements the ``OxcInterface``, and therefore
is compatible with the standard ``Oxc`` class.
The instantiation of a slice of Polatis requires the developer to specify a
list of input ports and a list of output ports that are reserved for the slice,
as illustrated bellow:

.. code:: python

    from devicecontrol.polatis import Oxc
    from devicecontrol.polatis.slicing import VirtualOxc

    # First, an object that communicates with the real device should be
    # instantiated
    IP_ADDR = "192.168.0.3"
    PORT = 5025
    real_device = Oxc(IP_ADDR, PORT)

    # Then, the virtual OXC can be created
    reserved_input_ports = range(11, 26)
    reserved_output_ports = range(37, 45)
    voxc = VirtualOxc(real_device, reserved_input_ports, reserved_output_ports)

    # The VirtualOxc follows the same API as the original object
    voxc.power
    # => {1: -6.01, 2: -9.89, ..., 22: -29.33, 23: -29.53}
    voxc.connections
    # => {1: 16, 2: 17, ... 15: 23}

    # The ports in the VirtualOxc are renumbered to always start from 1
    # Internally the object keeps a mapping of the interfaces
    voxc.ports
    # => ([1, 2, ..., 16], [17, 18, ..., 23])


Note
====

This project has been set up using PyScaffold 3.1. For details and usage
information on PyScaffold see https://pyscaffold.org/.
