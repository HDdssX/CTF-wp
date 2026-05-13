import re
import string

for i in dir(__builtins__) + list(string.printable):
    if re.search(r'(status|flag|update|setattr|getattr|eval|exec|import|locals|os|sys|builtins|open|or|and|not|is|breakpoint|exit|print|quit|help|input|globals)', i):
        continue
    if re.search(r'[_\s=+\[\],"\'\<\>\-\*@#$%^&\\\|\{\}\:;]', i):
        continue
    if re.search(r'[0-9a-zA-Z]', i):
        continue
    print(i)