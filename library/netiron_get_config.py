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
                           ofile=dict(required=True, default=None),
                           filter=dict(required=False, choices=['vlan-config', 'interface-config', 'mpls-config'], default=None)
                           ),
        supports_check_mode=False)

    host = module.params['host']
    port = module.params['port']
    user = module.params['user']
    passwd = module.params['passwd']
    ofile = module.params['ofile']

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
    GET_CONFIG = """
    <nc:rpc xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:brcd="http://brocade.com/ns/netconf/config/netiron-config/" message-id="1">
        <nc:get-config>
            <nc:source>
                <nc:running/>
            </nc:source>
            <nc:filter nc:type="subtree">
                <brcd:netiron-config>
                """.rstrip()
    if module.params['filter'] is not None:
        GET_CONFIG += " <brcd:".rstrip()
        GET_CONFIG += module.params['filter'].rstrip()
        GET_CONFIG += "/>".rstrip()
    GET_CONFIG += """
                </brcd:netiron-config>
            </nc:filter>
        </nc:get-config>
    </nc:rpc>]]>]]>"""

    ch.send(GET_CONFIG)

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

    try:
        # save reply in XML output file
        with open(ofile, 'w') as conf:
            conf.write(msg.split("]]>]]>", 1)[0])
    except Exception as err:
        msg = 'Unable write on file'
        module.fail_json(msg=msg)

    ch.close()
    transp.close()
    skt.close()

    module.exit_json(changed=False, msg=msg)

from ansible.module_utils.basic import *
main()