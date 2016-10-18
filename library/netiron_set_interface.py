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
                           if_id=dict(required=True, default=None),
                           if_ip=dict(required=True, default=None),
                           enable=dict(required=False, type='bool', choices=BOOLEANS, default=True),
                           action=dict(required=True, choices=['create', 'delete'], default=None)
                           ),
        supports_check_mode=False)

    host = module.params['host']
    port = module.params['port']
    user = module.params['user']
    passwd = module.params['passwd']
    if_id = module.params['if_id']
    if_ip = module.params['if_ip']
    action = module.params['action']
    enable = module.params['enable']

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
    SET_INTERFACE = """
    <nc:rpc message-id="1"
	xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"
	xmlns:brcd="http://brocade.com/ns/netconf/config/netiron-config/">
	<nc:edit-config>
		<nc:target>
			<nc:running/>
		</nc:target>
		<nc:config>
			<brcd:netiron-config>
				<brcd:interface-config>
					<brcd:interface nc:operation='""" + action + """'>
						<brcd:interface-id>""" + if_id + """</brcd:interface-id>"""
    if enable:
        SET_INTERFACE += """
                        <brcd:enable></brcd:enable>
                        """
    else:
        SET_INTERFACE +="""
                        <brcd:disable></brcd:disable>
                        """ # doesn't work when action=delete
    SET_INTERFACE +="""
						<brcd:ip>
							<brcd:address>"""+ if_ip + """</brcd:address>
						</brcd:ip>
					</brcd:interface>
				</brcd:interface-config>
			</brcd:netiron-config>
		</nc:config>
	</nc:edit-config></nc:rpc>
]]>]]>"""

    ch.send(SET_INTERFACE)

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