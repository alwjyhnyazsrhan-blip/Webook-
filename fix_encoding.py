#!/usr/bin/env python3
import os

filepath = 'apps/bot/handlers.py'

with open(filepath, 'rb') as f:
    content = f.read()

# Simple replacements for corrupted UTF-8
replacements = {
    b'\xc3\xa2\xe2\x80\x94': b'-',
    b'\xc3\xa2\xe2\x80\x93': b'-',
    b'\xe2\x80\x99': b"'",
    b'\xe2\x80\x9d': b'"',
    b'\xe2\x80\x9c': b'"',
    b'\xe2\x80\x93': b'-',
    b'\xe2\x80\x94': b'-',
    b'\xe2\x80\xa6': b'...',
    b'\xc3\xa2': b'a',
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(filepath, 'wb') as f:
    f.write(content)

print("Fixed encoding")