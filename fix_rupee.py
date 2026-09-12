import os

with open('frontend/src/pages/Dashboard.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('?', '\u20B9')

with open('frontend/src/pages/Dashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
