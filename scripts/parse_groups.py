import json, sys
d = json.load(sys.stdin)
vals = d['data']['valueRange']['values']
groups = set()
for v in vals[1:]:
    if v and v[0]:
        groups.add(v[0])
for g in sorted(groups):
    print(g)
print(f"\nTotal rows: {len(vals)}")
