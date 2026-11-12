"""Mede linhas de texto (posição e altura) numa página de PDF via pdftotext -bbox-layout."""

import re
import subprocess
import sys

path, page = sys.argv[1], sys.argv[2]
xml = subprocess.run(
    ["pdftotext", "-f", page, "-l", page, "-bbox-layout", path, "-"],
    capture_output=True,
    text=True,
    check=True,
).stdout
for line in re.finditer(r"<line ([^>]*)>(.*?)</line>", xml, re.S):
    attrs = dict(re.findall(r'(\w+)="([0-9.]+)"', line.group(1)))
    words = " ".join(re.findall(r">([^<]+)</word>", line.group(2)))
    x0, y0, x1, y1 = (float(attrs[k]) for k in ("xMin", "yMin", "xMax", "yMax"))
    cm = 2.54 / 72
    print(f"x={x0 * cm:5.2f}cm y={y0 * cm:5.2f}cm w={(x1 - x0) * cm:5.2f}cm h={y1 - y0:5.1f}pt  {words[:60]}")
