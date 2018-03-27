"""
Some basic utils
(previously were in helios module, but making things less interdependent

2010-08-17
"""


from __future__ import absolute_import
import json

## JSON
def to_json(d):
    return json.dumps(d, sort_keys=True)

def from_json(json_str):
    if not json_str: return None
    return json.loads(json_str)
