#!/usr/bin/python

import paramiko
import socket

# XML static definitions #
CLOSE = """
<nc:rpc xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:brcd="http://brocade.com/ns/netconf/config/netiron-config/" message-id="1">
    <nc:close-session/>
</nc:rpc>]]>]]>"""

HELLO = """
<hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <capabilities>
        <capability>urn:ietf:params:netconf:base:1.0</capability>
    </capabilities>
</hello>]]>]]>
"""


def main():
    module = AnsibleModule(
        argument_spec=dict(host=dict(required=True, default=None),
                           user=dict(required=True, default=None),
                           passwd=dict(required=True, default=None),
                           port=dict(required=False, default=830),
                           vlan_id=dict(required=True, default=None),
                           vlan_name=dict(required=False, default=None),
                           tagged=dict(required=False, type='bool', choices=BOOLEANS, default=False),
                           vlan_interfaces=dict(required=False, default=None),
                           action=dict(required=True, choices=['create', 'delete'], default=None)
                           ),
        supports_check_mode=False)

    host = module.params['host']
    port = module.params['port']
    user = module.params['user']
    passwd = module.params['passwd']
    vlan_id = module.params['vlan_id']
    action = module.params['action']

    # connecting and creating channel
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # no ssh key problems
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        skt.connect((host, int(port)))
        transp = paramiko.Transport(skt)
        transp.connect(username=user, password=passwd)
        ch = transp.open_session()
        # chname = \
        ch.set_name('netconf')
        ch.invoke_subsystem('netconf') # Invoking netconf
    except Exception as err:
        msg = 'Unable to connect: {0}'.format(str(err))
        module.fail_json(msg=msg)

    # NetIron requires a first hello message from the client, it will not be answered
    ch.send(HELLO)


    # mount and send the netconf command
    SET_VLAN = """
    <nc:rpc message-id="1" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"  xmlns:brcd="http://brocade.com/ns/netconf/config/netiron-config/">
        <nc:edit-config>
            <nc:target>
                <nc:running/>
            </nc:target>
            <nc:default-operation>merge</nc:default-operation>
            <nc:config>
                <brcd:netiron-config>
                    <brcd:vlan-config>
                        <brcd:vlan nc:operation=\"""" + action + """\">
                            <brcd:vlan-id>""" + vlan_id + """</brcd:vlan-id>"""
    if module.params['vlan_name'] is not None:
        SET_VLAN += """<brcd:vlan-name>""" + module.params['vlan_name'] + """</brcd:vlan-name>"""

    if module.params['vlan_interfaces'] is not None:
        if module.params['tagged']:
            SET_VLAN += """<brcd:tagged>""" + module.params['vlan_interfaces'] + """</brcd:tagged>"""
        else:
            SET_VLAN += """<brcd:untagged>""" + module.params['vlan_interfaces'] + """</brcd:untagged>"""

    SET_VLAN +="""
                        </brcd:vlan>
                    </brcd:vlan-config>
                </brcd:netiron-config>
            </nc:config>
        </nc:edit-config>
    </nc:rpc>
    ]]>]]>
"""

    ch.send(SET_VLAN)

    # get reply
    reply = ch.recv(2048)
    msg=""
    while reply:
        reply = ch.recv(1024)
        msg += reply
        if reply.find("]]>]]>") >= 0: # That's the sign of the end of reply
            # close session
            ch.send(CLOSE)

    if msg.find("rpc-error") >= 0:
        parterr= msg.split("<nc:error-message>",1)[1]
        err = parterr.split("</nc:error-message>", 1)[0]
        module.fail_json(msg=err)

    ch.close()
    transp.close()
    skt.close()

    module.exit_json(changed=True, msg=msg)

from ansible.module_utils.basic import *
main()