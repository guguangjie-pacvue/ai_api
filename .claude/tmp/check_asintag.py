
import json

with open('C:/AI engineering/single-api/ai_api/single-api/mainapi/Amazon.Advertising.Api/AsinTag/task-2026-08-13-14-30-00/cases.json', encoding='utf-8') as f:
    cases = json.load(f)

paths = set()
for c in cases:
    for s in c['steps']:
        p = s.get('path', '')
        if p:
            paths.add(p)
        print(' ', s['name'], ':', p)

print()
print('Unique paths (' + str(len(paths)) + '):')
for p in sorted(paths):
    print(' ', p)

# Compare with swagger endpoints for AsinTag
with open('C:/AI engineering/single-api/ai_api/single-api/endpoints-Amazon.Advertising.Api.json', encoding='utf-8') as f:
    eps = json.load(f)

swagger_paths = set(e['path'] for e in eps if e['tag'] == 'AsinTag')
print()
print('Swagger AsinTag paths (' + str(len(swagger_paths)) + '):')
for p in sorted(swagger_paths):
    print(' ', p)

print()
print('In cases but NOT in swagger:')
for p in sorted(paths - swagger_paths):
    print(' ', p)
