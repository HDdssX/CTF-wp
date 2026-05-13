
import sys
import collections
import re

# Mock environment
class LockedList(collections.UserList):
    def __setitem__(self, index, value):
        raise Exception("Forbidden")

def sandbox(payload_arg):
    # Reset argv
    sys.argv = ['jail.py', payload_arg]
    
    # Logic from jail.py
    try:
        status = LockedList([False])
        
        # Determine strict input
        user_input = sys.argv[1].encode('idna').decode('ascii').rstrip('-')
        print(f"Payload: {user_input}")
        print(f"Length: {len(user_input)}")

        # Regex checks
        if re.search(r'[0-9A-Z]', user_input):
            print("FORBIDDEN: No numbers or alphas")
            return

        if re.search(r'[_\s=+\[\],"\'\<\>\-\*@#$%^&\\\|\{\}\:;]', user_input):
            print("FORBIDDEN: Incorrect symbol detected")
            return

        if re.search(r'(status|flag|update|setattr|getattr|eval|exec|import|locals|os|sys|builtins|open|or|and|not|is|breakpoint|exit|print|quit|help|input|globals)', user_input.casefold()):
            print("FORBIDDEN: Keywords detected")
            return

        print("Regex check passed!")
        
        # Cleanup locals to match jail.py environment more closely
        del payload_arg

        # Execution
        # We need to simulate the exact scope. In jail.py it's inside a function 'sandbox'.
        # vars() inside here will contain 'status', 'user_input'.
        # We need to ensure 'min(dir())' returns 'status'.
        
        print(f"Locals keys: {list(locals().keys())}")
        print(f"min(dir()) would be: {min(dir())}") 
        
        # eval is used in original? The provided snippet showed `sandbox` function but stopped before eval.
        # Assuming eval(user_input) is called.
        eval(user_input)
        
        if status[0]:
            print("SUCCESS: Status is Truthy!")
        else:
            print(f"FAIL: Status is {status}")
            
    except Exception as e:
        print(f"Runtime Error: {e}")

payload = "vars().get(min(dir())).append(~vars().get(min(dir())).pop())"
sandbox(payload)
