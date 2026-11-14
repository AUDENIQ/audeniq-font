"""어데닉 로고를 글리프로 — 워드마크(U+F8F0)와 A 심볼(U+F8F1).

외곽선은 어데닉 저장소의 새 로고(2026-11 정리, docs/brand/LOGO.md)를 그대로 옮겼다.
  워드마크: docs/brand/logo/wordmark-color.svg (= 앱의 AUDENIQ_Logo_Light.svg)
  A 심볼:   docs/brand/logo/mark.svg (= 앱의 favicon.svg에서 타일을 뺀 것)
색이 있는 부분(Q 꼬리 그라데이션, A 막대 파랑)은 COLRv1 층으로 남기고, 나머지는 글자 색을 따른다.
COLRv1을 못 읽는 사파리는 COLRv0 층으로 본체는 글자 색, 꼬리·막대는 한 색으로 보인다.
"""
from fontTools.colorLib.builder import buildCOLR, buildCPAL
from fontTools.misc.transform import Transform
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent

WORDMARK_CP = 0xF8F0
MARK_CP = 0xF8F1

# wordmark-color.svg (viewBox 0 0 1060 182). 글자 기준선 y=168, 대문자 윗선 y=14(오버슛 위아래 3).
WORDMARK_BODY = [
    "M22.5 168L75.13 21.46A15.8 15.8 0 0 1 104.87 21.46L157.5 168H127.5L90 63.59L52.5 168Z",  # A
    "M175.5 14H203.5V106C203.5 129.4 217.7 145 239 145C260.3 145 274.5 129.4 274.5 106V14H302.5V106"
    "C302.5 145 277.1 171 239 171C200.9 171 175.5 145 175.5 106Z",  # U
    "M323.5 14H378.5C425.9 14 457.5 44.8 457.5 91C457.5 137.2 425.9 168 378.5 168H323.5V142H378.5"
    "C408.5 142 428.5 121.6 428.5 91C428.5 60.4 408.5 40 378.5 40H323.5Z",  # D
    "M480.5 14H595.5V40H480.5Z",  # E 윗획(떨어져 있음)
    "M480.5 78H584.5V104H508.5V142H595.5V168H480.5Z",  # E 몸
    "M621.5 168V14H629.5L733.5 110V14H761.5V168H753.5L649.5 72V168Z",  # N
    "M799.5 14H827.5V168H799.5Z",  # I
    "M1011.22 127.75A83 80 0 1 0 972.89 163.36L952.43 142.9A54 54 0 1 1 989.4 105.93Z",  # Q
]
WORDMARK_TAIL = ["M932.5 106H972.5L1037.5 171H997.5Z"]  # Q 꼬리(그라데이션)
WORDMARK_BASE, WORDMARK_TOP = 168, 14
WORDMARK_LEFT, WORDMARK_RIGHT = 22.5, 1037.5
# 그라데이션: #3B63F3(--aq-blue-500) → #7A5AF8(--aq-violet-500), (932.5,106)에서 (1037.5,171)로
ACCENT_STOPS = [(0.0, "#3B63F3"), (1.0, "#7A5AF8")]
ACCENT_FROM, ACCENT_TO = (932.5, 106), (1037.5, 171)
ACCENT_FLAT = "#5B5EF6"  # 사파리(COLRv0)용 꼬리 한 색: 두 끝 색의 가운데

# mark.svg (64 격자). A 바닥 y=56, 꼭짓점 곡선 위 y≈8. 막대는 다리 밑에 깐다(먼저 그림).
MARK_BODY = ["M7 56L25.08 12.62A7.5 7.5 0 0 1 38.92 12.62L57 56H45L32 24.8L19 56Z"]
MARK_BAR = ["M24.17 40H39.83L44 50H20Z"]
MARK_BAR_COLOR = "#3B63F3"
MARK_BASE, MARK_TOP = 56, 8
MARK_LEFT, MARK_RIGHT = 7, 57

SIDE = 60  # 로고 양옆 여백(유닛)


def _hex(c):
    return tuple(int(c[i:i + 2], 16) / 255 for i in (1, 3, 5)) + (1.0,)


def _glyph(paths, transform, glyf):
    """SVG 경로들 → TrueType 글리프. 윤곽마다 시계 방향(TrueType 바깥 방향)으로 맞춘다."""
    tt = TTGlyphPen(None)
    for d in paths:
        rec = RecordingPen()
        parse_path(d, TransformPen(rec, transform))
        area = AreaPen()
        rec.replay(area)
        out = Cu2QuPen(tt, max_err=1.0, reverse_direction=False)
        rec.replay(ReverseContourPen(out) if area.value > 0 else out)
    g = tt.glyph()
    g.recalcBounds(glyf)
    return g


def _transform(base, top, left, cap):
    s = cap / (base - top)
    # SVG는 y가 아래로 자란다 → 뒤집고, 기준선을 0에, 왼쪽 잉크를 SIDE에.
    return Transform().translate(SIDE, 0).scale(s, -s).translate(-left, -base), s


def add_logo_glyphs(font):
    """워드마크·A 심볼 글리프와 COLR/CPAL을 더하고, 새 글리프 이름을 돌려준다."""
    glyf, hmtx, gvar = font["glyf"], font["hmtx"], font["gvar"]
    cap = font["OS/2"].sCapHeight
    order = font.getGlyphOrder()

    def put(name, glyph, adv):
        glyf[name] = glyph
        if name not in order:
            order.append(name)
        hmtx[name] = (adv, getattr(glyph, "xMin", 0))
        gvar.variations[name] = []  # 로고는 굵기와 상관없이 같은 모양

    def composite(name, parts, adv):
        g = Glyph()
        g.numberOfContours = -1
        g.components = []
        for i, p in enumerate(parts):
            c = GlyphComponent()
            c.glyphName, c.x, c.y = p, 0, 0
            c.flags = 0x0004 | (0x0400 if i == 0 else 0)  # ROUND_XY_TO_GRID, OVERLAP_COMPOUND
            g.components.append(c)
        g.recalcBounds(glyf)
        put(name, g, adv)

    t, s = _transform(WORDMARK_BASE, WORDMARK_TOP, WORDMARK_LEFT, cap)
    wm_adv = round((WORDMARK_RIGHT - WORDMARK_LEFT) * s + 2 * SIDE)
    put("aq.wordmark.body", _glyph(WORDMARK_BODY, t, glyf), wm_adv)
    put("aq.wordmark.tail", _glyph(WORDMARK_TAIL, t, glyf), wm_adv)
    composite("aq.wordmark", ["aq.wordmark.body", "aq.wordmark.tail"], wm_adv)
    g0, g1 = t.transformPoint(ACCENT_FROM), t.transformPoint(ACCENT_TO)

    tm, sm = _transform(MARK_BASE, MARK_TOP, MARK_LEFT, cap)
    mk_adv = round((MARK_RIGHT - MARK_LEFT) * sm + 2 * SIDE)
    put("aq.mark.body", _glyph(MARK_BODY, tm, glyf), mk_adv)
    put("aq.mark.bar", _glyph(MARK_BAR, tm, glyf), mk_adv)
    composite("aq.mark", ["aq.mark.body", "aq.mark.bar"], mk_adv)

    font.setGlyphOrder(order)
    glyf.glyphOrder = order
    for table in font["cmap"].tables:
        if table.isUnicode():
            table.cmap[WORDMARK_CP] = "aq.wordmark"
            table.cmap[MARK_CP] = "aq.mark"

    # 팔레트: 0–1 그라데이션, 2 심볼 막대 파랑, 3 사파리용 꼬리 한 색. 0xFFFF = 지금 글자 색.
    palette = [_hex(c) for _, c in ACCENT_STOPS] + [_hex(MARK_BAR_COLOR), _hex(ACCENT_FLAT)]
    font["CPAL"] = buildCPAL([palette])
    fg = {"Format": ot.PaintFormat.PaintSolid, "PaletteIndex": 0xFFFF, "Alpha": 1.0}
    # 그라데이션 축과 수직인 점 p2: p0에서 (p1-p0)을 90도 돌린 방향
    dx, dy = g1[0] - g0[0], g1[1] - g0[1]
    gradient = {
        "Format": ot.PaintFormat.PaintLinearGradient,
        "ColorLine": {"ColorStop": [{"StopOffset": o, "PaletteIndex": i, "Alpha": 1.0}
                                    for i, (o, _) in enumerate(ACCENT_STOPS)]},
        "x0": round(g0[0]), "y0": round(g0[1]), "x1": round(g1[0]), "y1": round(g1[1]),
        "x2": round(g0[0] - dy), "y2": round(g0[1] + dx),
    }
    bar = {"Format": ot.PaintFormat.PaintSolid, "PaletteIndex": 2, "Alpha": 1.0}

    def layers(*pairs):
        return {"Format": ot.PaintFormat.PaintColrLayers,
                "Layers": [{"Format": ot.PaintFormat.PaintGlyph, "Glyph": g, "Paint": p} for g, p in pairs]}

    glyph_map = font.getReverseGlyphMap(rebuild=True)
    colr = buildCOLR({
        "aq.wordmark": layers(("aq.wordmark.body", fg), ("aq.wordmark.tail", gradient)),
        "aq.mark": layers(("aq.mark.bar", bar), ("aq.mark.body", fg)),  # 막대를 다리 밑에
    }, version=1, glyphMap=glyph_map)
    # 사파리는 COLRv1(그라데이션)을 못 읽는다. 같은 글리프에 COLRv0 층(한 색)을 함께 넣으면
    # v1을 읽는 브라우저는 v1을, 사파리는 v0을 쓴다. 꼬리는 그라데이션 가운데 색(ACCENT_FLAT).
    v0 = {
        "aq.wordmark": [("aq.wordmark.body", 0xFFFF), ("aq.wordmark.tail", 3)],
        "aq.mark": [("aq.mark.bar", 2), ("aq.mark.body", 0xFFFF)],
    }
    t = colr.table
    bases, lays = [], []
    for base in sorted(v0, key=glyph_map.get):  # 글리프 번호 순
        rec = ot.BaseGlyphRecord()
        rec.BaseGlyph, rec.FirstLayerIndex, rec.NumLayers = base, len(lays), len(v0[base])
        bases.append(rec)
        for glyph, index in v0[base]:
            lay = ot.LayerRecord()
            lay.LayerGlyph, lay.PaletteIndex = glyph, index
            lays.append(lay)
    t.BaseGlyphRecordArray = ot.BaseGlyphRecordArray()
    t.BaseGlyphRecordArray.BaseGlyphRecord = bases
    t.LayerRecordArray = ot.LayerRecordArray()
    t.LayerRecordArray.LayerRecord = lays
    t.BaseGlyphRecordCount, t.LayerRecordCount = len(bases), len(lays)
    font["COLR"] = colr
    return ["aq.wordmark", "aq.mark"]
