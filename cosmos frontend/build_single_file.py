import base64
import os

print("Reading assets...")

with open('humanoid/mira-hair-v1.webp', 'rb') as f:
    hair_b64 = 'data:image/webp;base64,' + base64.b64encode(f.read()).decode('utf-8')

with open('humanoid/mira-idle-v1.webp', 'rb') as f:
    idle_b64 = 'data:image/webp;base64,' + base64.b64encode(f.read()).decode('utf-8')

print(f"Hair base64 length: {len(hair_b64)}")
print(f"Idle base64 length: {len(idle_b64)}")

with open('assets/index-BlszmC9G.css', 'r', encoding='utf-8') as f:
    css = f.read()

with open('assets/index-1PiDnpcG.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Replace all possible paths to the webp files with their base64 representation
js = js.replace('"./humanoid/mira-hair-v1.webp"', f'"{hair_b64}"')
js = js.replace('"/humanoid/mira-hair-v1.webp"', f'"{hair_b64}"')
js = js.replace('"./humanoid/mira-idle-v1.webp"', f'"{idle_b64}"')
js = js.replace('"/humanoid/mira-idle-v1.webp"', f'"{idle_b64}"')

# Escape any potential </script> closing tag
js_safe = js.replace('</script>', '<\\/script>')

single_html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>MIRA Humanoid</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet" />
    <style>
{css}
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module">
{js_safe}
    </script>
  </body>
</html>"""

out_file = 'index.html'
with open(out_file, 'w', encoding='utf-8') as f:
    f.write(single_html)

size = os.path.getsize(out_file)
print(f"Single-file {out_file} successfully created! Total size: {size:,} bytes ({size / 1024 / 1024:.2f} MB)")

