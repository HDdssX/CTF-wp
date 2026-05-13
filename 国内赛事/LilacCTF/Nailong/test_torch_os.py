import torch
try:
    print(torch.os)
    print("torch.os is avail")
except:
    print("torch.os failed")

try:
    import torch.distributed
    print(torch.distributed.os)
except:
    pass
