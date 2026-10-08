"""Make Qt's SVG output independent of `vector-effect="non-scaling-stroke"`.

pyqtgraph draws curves with cosmetic pens (a width in device pixels) under a scaling transform
(data units -> pixels). QSvgGenerator writes that as a `<g transform="matrix(...)">` holding
elements marked `vector-effect="non-scaling-stroke"`. Only some SVG viewers honour that attribute
(browsers, Qt); others (Inkscape, Illustrator, resvg) scale the stroke width with the transform and
draw huge bars. `bake_cosmetic_strokes` applies the transform to the coordinates instead, so the
stroke width is a plain width in pixels everywhere."""

import re

_NUMBER = r"-?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?"
_PAIR = re.compile(f"({_NUMBER}),({_NUMBER})")
# A group Qt wrote for one painter state: no nested groups inside.
_GROUP = re.compile(r'<g ([^>]*?)transform="matrix\(([^)]*)\)"([^>]*)>(.*?)</g>', re.S)
_ELEMENT = re.compile(r"<(\w+)\b[^>]*?/?>")
_POLYLINE = re.compile(r'<polyline fill="none" vector-effect="non-scaling-stroke" points="([^"]*)" />')
_COSMETIC = 'vector-effect="non-scaling-stroke"'


def _number(value):
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _apply(matrix, text):
    a, b, c, d, e, f = matrix

    def point(m):
        x, y = float(m.group(1)), float(m.group(2))
        return f"{_number(a * x + c * y + e)},{_number(b * x + d * y + f)}"

    return _PAIR.sub(point, text)


def _merge_polylines(body):
    """Join consecutive polylines where one ends at the next one's start (pyqtgraph writes every curve segment alone)."""
    out, run, last = [], None, None  # run: list of point strings of the polyline being extended
    pos = 0
    for m in _POLYLINE.finditer(body):
        points = m.group(1).split()
        gap = body[pos:m.start()]
        if run is not None and (gap.strip() or points[0] != last):
            out.append(run)
            run = None
        if run is None:
            if gap.strip():
                out.append(gap)
            run = list(points)
        else:
            run.extend(points[1:])
        last = points[-1]
        pos = m.end()
    if run is not None:
        out.append(run)
    out.append(body[pos:])
    return "\n".join(
        f'<polyline fill="none" vector-effect="non-scaling-stroke" points="{" ".join(p)}" />' if isinstance(p, list) else p
        for p in out
        if p
    )


def _bake_group(match):
    before, matrix_text, after, body = match.groups()
    matrix = [float(v) for v in matrix_text.split(",")]
    elements = _ELEMENT.findall(body)
    translation_only = matrix[:4] == [1, 0, 0, 1]
    only_cosmetic_lines = bool(elements) and all(e in ("polyline", "path") for e in elements) and body.count(_COSMETIC) == len(elements)
    if translation_only or not only_cosmetic_lines:
        return match.group(0)
    body = _merge_polylines(_apply(matrix, body).replace("\r\n", "\n"))
    return f"<g {before}{after}>{body}</g>"


def bake_cosmetic_strokes(svg):
    """`svg` text with scaled groups of cosmetic-pen lines rewritten into pixel coordinates."""
    return _GROUP.sub(_bake_group, svg)
