#Python 3.14.2
import re
from collections import UserList
from sys import argv

class LockedList(UserList):
    def __setitem__(self, key, value):
        raise Exception("Assignment blocked!")

def sandbox():
    if len(argv) != 2:
        print("ERROR: Missing code")
        return

    try:
        status = LockedList([False])
        status_id = id(status)
        user_input = argv[1].encode('idna').decode('ascii').rstrip('-')

        if re.search(r'[0-9A-Z]', user_input):
            print("FORBIDDEN: No numbers or alphas")

        if re.search(r'[_\s=+\[\],"\'\<\>\-\*@#$%^&\\\|\{\}\:;]', user_input):
            print("FORBIDDEN: Incorrect symbol detected")

        if re.search(r'(status|flag|update|setattr|getattr|eval|exec|import|locals|os|sys|builtins|open|or|and|not|is|breakpoint|exit|print|quit|help|input|globals)', user_input.casefold()):
            print("FORBIDDEN: Keywords detected")

        if len(user_input) > 60:
            print(f"FORBIDDEN: Input too long! Keep it concise and it is very simple. Length: {len(user_input)}")

        eval(user_input)
        print(vars())
        # vars().get(min(dir())).append(~vars().get(min(dir())).pop())
        if status[0] and id(status) == status_id:
            print("Success!")
        else:
            print(f"FAILURE: status is still {status}")
            
    except Exception as e:
        print(f"Don't be evil~ And I won't show you this error :) {e}")

if __name__ == '__main__':
    sandbox()