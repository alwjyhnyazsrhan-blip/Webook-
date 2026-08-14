import os, re
for dirpath, _, filenames in os.walk('/app'):
    for fn in filenames:
        if fn.endswith('.py'):
            p = os.path.join(dirpath, fn)
            content = open(p, 'rb').read()
            cleaned = re.sub(b'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', b'', content)
            open(p, 'wb').write(cleaned)

for dirpath, _, filenames in os.walk('/app'):
    for fn in filenames:
        if fn.endswith('.py'):
            p = os.path.join(dirpath, fn)
            data = open(p, 'rb').read()
            if data.startswith(b'\xef\xbb\xbf'):
                open(p, 'wb').write(data[3:])
