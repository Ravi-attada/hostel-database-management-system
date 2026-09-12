import os

with open('frontend/src/pages/Dashboard.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the ternary operator back
text = text.replace('progress !== undefined \u20B9 (', 'progress !== undefined ? (')

with open('frontend/src/pages/Dashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
