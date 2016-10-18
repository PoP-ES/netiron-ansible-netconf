## About

This is an Ansible module for Brocade NetIron, based on its limited NETCONF support.
For more details on NETCONF support on NetIron, see http://www.brocade.com/content/html/en/feature-support-matrix/netiron-05900-featuresupportmatrix/GUID-947AEB2E-4E00-4D01-8C59-FD22F3C9ABE3.html

## Modules

# netiron_get_config
* Get configuration related to vlan, interface and mpls, save on xml file
* Params:
 * host = required
 * user = required
 * passwd = required
 * port = not required, default = 830
 * ofile = output file, required
 * filter = not required, which subtree configuration. options: 'vlan-config', 'interface-config', 'mpls-config'

# netiron_get_state
* Get state related to vlan, interface and mpls, save on xml file
* Params:
 * host = required
 * user = required
 * passwd = required
 * port = not required, default = 830
 * ofile = output file, required
 * filter = not required, which subtree configuration. options: 'vlan-state', 'interface-state', 'mpls-state'

# netiron_set_interface
* Configure IP on interface
* Params:
 * host = required
 * user = required
 * passwd = required
 * port = not required, default = 830
 * if_id = required, interface ID
 * if_ip = required, interface IP
 * enable = not required, boolean. true if it is wanted to enable the interface. default=true
 * action = required, options: 'create', 'delete'

# netiron_set_vlan
* Configure vlan on interface
* Params:
 * host = required
 * user = required
 * passwd = required
 * port = not required, default = 830
 * vlan_id = required, vlan ID
 * vlan_name = not required, vlan name
 * tagged = not required, boolean. true if it is wanted to set the interface as tagged. default=false
 * action = required, options: 'create', 'delete'

# netiron_write_memory
* That's the only module not using NETCONF, a cli command is passed to write the configuration to the memory
* Params:
 * host = required
 * user = required
 * passwd = required

## Playbook examples

See files on this repo.

## Contributors
[Rafael Vencioneck](https://github.com/rdvencioneck)
