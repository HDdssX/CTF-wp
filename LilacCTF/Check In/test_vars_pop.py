
import collections
class LockedList(collections.UserList):
    def __setitem__(self, index, value):
        raise Exception("Forbidden")

def sandbox():
    status = LockedList([False])
    print(f"Before pop: {vars().keys()}")
    
    # Simulate user payload: vars().pop('status')
    # We use 'status' string directly as min(vars()) would behave
    try:
        s = vars().pop('status')
        print(f"Popped object: {s}")
        s.append('WIN')
    except Exception as e:
        print(f"Pop failed: {e}")

    print(f"After pop: {vars().keys()}")
    
    try:
        # Check if status variable is still accessible
        if status[0]:
            print("Status is accessible and Truthy!")
        else:
            print(f"Status is accessible but Falsey: {status}")
    except NameError:
        print("Status variable is GONE (NameError)")
    except Exception as e:
        print(f"Other error: {e}")

sandbox()
