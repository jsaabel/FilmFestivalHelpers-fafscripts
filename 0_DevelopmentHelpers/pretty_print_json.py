"""
(Nov 19, 2021)
Typically used to print response bodies in a more easily readable format for analysis. Also writes output to a .txt file.
Minor possible improvement: Add timestamp to output file to avoid overwriting files?
"""
from modules import eventive as e, notion as n
import json


test = n.get_db('events')
test2 = json.dumps(test, indent=2)
print(test2)

file = open('logs/json_dump.txt', 'w')
file.write(test2)
file.close()

print('File written.')