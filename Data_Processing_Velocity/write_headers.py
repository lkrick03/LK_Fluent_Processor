import re
with open('mvel_functions.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if re.search(r'[\'"].*veloc.*[\'"]', line, re.I):
            print(f"{i}: {line.strip()}")
