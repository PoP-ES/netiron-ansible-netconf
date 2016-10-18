#!/usr/bin/python

import paramiko

def main():
    module = AnsibleModule(
        argument_spec=dict(host=dict(required=True, default=None),
                           user=dict(required=True, default=None),
                           port=dict(required=False, default=22),
                           passwd=dict(required=True, default=None)
                           ),
        supports_check_mode=False)

    hostname = module.params['host']
    port = module.params['port']
    username = module.params['user']
    password = module.params['passwd']
    try:
        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        s.load_system_host_keys()
        s.connect(hostname, int(port), username, password)
        channel = s.invoke_shell()
        channel.send('write memory\n')
    except Exception as err:
        msg = 'Unable to connect: {0}'.format(str(err))
        module.fail_json(msg=msg)

    reply = channel.recv(2048)
    while reply:
        reply = reply + channel.recv(1024)
        if reply.find("SSH") >= 0:
            break
    channel.send('exit\n')
    channel.send('exit\n')
    s.close()
    if reply.find("Done.") >= 0:
        module.exit_json(changed=True, msg=reply)
    else:
        module.exit_json(changed=False, msg=reply)

from ansible.module_utils.basic import *
main()