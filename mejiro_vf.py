#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# McMejiro バリアブルフォント (wght 100-900) を生成するスクリプト
#
# M+ 1 と Roboto のバリアブルフォントから同じウェイトのインスタンスを切り出し、
# ウェイトごとに合成したものをマスターとして fontTools.varLib でまとめ直す。
# 両フォントとも 100 刻みで線形補間されているため、100〜900 の 9 マスターで
# 元のバリアブルフォントの形状をそのまま再現できる。

import copy
from datetime import date

from fontTools.designspaceLib import (
    AxisDescriptor,
    DesignSpaceDocument,
    InstanceDescriptor,
    SourceDescriptor,
)
from fontTools.otlLib.builder import buildStatTable
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.scaleUpem import scale_upem
from fontTools.ttLib.tables import ttProgram
from fontTools.varLib import build as build_vf
from fontTools.varLib.instancer import instantiateVariableFont
import fontTools.subset  # noqa: F401  GSUB/GPOS に subset_feature_tags などを生やす

# Roboto のバリアブルフォントのパス
roboto_vf_path = "./roboto/Roboto[wdth,wght].ttf"

# M+ 1 のバリアブルフォントのパス
mplus_vf_path = "./mplus/MPLUS1[wght].ttf"

# 生成する McMejiro バリアブルフォントのパス
mejiro_vf_path = "./mejiro/McMejiro[wght].ttf"

# EM の大きさ (Roboto に合わせる)
upem = 2048

# マスターにするウェイト, インスタンス名
weights = [
    (100, "Thin"),
    (200, "ExtraLight"),
    (300, "Light"),
    (400, "Regular"),
    (500, "Medium"),
    (600, "SemiBold"),
    (700, "Bold"),
    (800, "ExtraBold"),
    (900, "Black"),
]
default_weight = 400


def main():
    today = date.today()
    version = "McMejiro-{0}".format(today.strftime("%Y%m%d"))

    mpvf = TTFont(mplus_vf_path)
    rbvf = TTFont(roboto_vf_path)
    # Roboto は幅軸を標準幅で固定しておく
    rbvf = instantiateVariableFont(rbvf, {"wdth": 100})

    masters = {}
    for wght, name in weights:
        print("Merging master: wght={0} ({1})".format(wght, name))
        masters[wght] = generate_master(mpvf, rbvf, wght)

    replaced = set(TTFont(roboto_vf_path).getGlyphOrder())
    vf = build_mejiro_vf(masters)
    transplant_gsub(vf, mpvf, replaced)
    set_mejiro_info(vf, version)

    print("Saving: {0}".format(mejiro_vf_path))
    vf.save(mejiro_vf_path)


def generate_master(mpvf, rbvf, wght):
    font = instantiateVariableFont(mpvf, {"wght": wght}, static=True)
    rbfont = instantiateVariableFont(rbvf, {"wght": wght}, static=True)

    # EMの大きさを2048に設定する
    scale_upem(font, upem)

    decompose_replaced_refs(font, set(rbfont.getGlyphOrder()))
    merge_roboto(font, rbfont)
    remove_kern(font)
    # GSUB はウェイトごとに rvrn の適用結果が異なるため、後で M+ のものを移植する
    del font["GSUB"]
    return font


def decompose_replaced_refs(font, replaced):
    # M+ の複合グリフ (例: U+FF5E は asciitilde を参照) が Roboto のグリフを
    # 参照しないよう、置き換え前にアウトラインへ展開して M+ の字形を保つ
    glyf = font["glyf"]
    glyph_set = font.getGlyphSet()
    memo = {}

    def refs_replaced(name):
        if name not in memo:
            glyph = glyf[name]
            memo[name] = glyph.isComposite() and any(
                c.glyphName in replaced or refs_replaced(c.glyphName)
                for c in glyph.components
            )
        return memo[name]

    targets = [n for n in font.getGlyphOrder() if n not in replaced and refs_replaced(n)]
    outlines = {}
    for name in targets:
        rec = DecomposingRecordingPen(glyph_set)
        glyph_set[name].draw(rec)
        pen = TTGlyphPen(None)
        rec.replay(pen)
        outlines[name] = pen.glyph()
    for name, glyph in outlines.items():
        glyf[name] = glyph


def merge_roboto(font, rbfont):
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    vmtx = font["vmtx"] if "vmtx" in font else None
    rbglyf = rbfont["glyf"]
    rbhmtx = rbfont["hmtx"]
    ascent = font["OS/2"].sTypoAscender

    # Roboto に含まれるグリフで置き換え、M+ に無いものは追加する
    order = font.getGlyphOrder()
    known = set(order)
    for name in rbfont.getGlyphOrder():
        glyph = copy.deepcopy(rbglyf[name])
        # Roboto のヒンティング命令は M+ 側で使えないので取り除く
        if hasattr(glyph, "program"):
            glyph.program = ttProgram.Program()
            glyph.program.fromBytecode([])
        glyf.glyphs[name] = glyph
        hmtx.metrics[name] = rbhmtx.metrics[name]
        if name not in known:
            order.append(name)
            known.add(name)
    font.setGlyphOrder(order)
    glyf.glyphOrder = order

    # 縦書き用メトリクス
    if vmtx is not None:
        for name in rbfont.getGlyphOrder():
            glyph = glyf[name]
            glyph.recalcBounds(glyf)
            tsb = ascent - glyph.yMax if glyph.numberOfContours else 0
            vmtx.metrics[name] = (upem, tsb)

    # 文字コードの割り当てを Roboto のものにする
    rbcmap = rbfont.getBestCmap()
    for table in font["cmap"].tables:
        if not table.isUnicode():
            continue
        for code, name in rbcmap.items():
            if table.format == 4 and code > 0xFFFF:
                continue
            table.cmap[code] = name

    # "fancy colon" U+EE01 を U+A789 にも割り当てる
    if 0xEE01 in rbcmap:
        for table in font["cmap"].tables:
            if table.isUnicode():
                table.cmap[0xA789] = rbcmap[0xEE01]


def remove_kern(font):
    # 和欧で詰めが崩れるのでカーニングは使わない
    gpos = font["GPOS"]
    tags = {fr.FeatureTag for fr in gpos.table.FeatureList.FeatureRecord}
    gpos.subset_feature_tags(tags - {"kern"})
    gpos.prune_lookups()


def build_mejiro_vf(masters):
    ds = DesignSpaceDocument()

    axis = AxisDescriptor()
    axis.tag = "wght"
    axis.name = "Weight"
    axis.minimum = weights[0][0]
    axis.default = default_weight
    axis.maximum = weights[-1][0]
    ds.addAxis(axis)

    for wght, name in weights:
        src = SourceDescriptor()
        src.name = name
        src.font = masters[wght]
        src.location = {"Weight": wght}
        ds.addSource(src)

        inst = InstanceDescriptor()
        inst.familyName = "McMejiro"
        inst.styleName = name
        inst.postScriptFontName = "McMejiro-{0}".format(name)
        inst.location = {"Weight": wght}
        ds.addInstance(inst)

    vf, _, _ = build_vf(ds)
    return vf


def transplant_gsub(vf, mpvf, replaced):
    # ウェイトによる字形切り替え (rvrn) を残すため、M+ の GSUB をそのまま移植する
    gsub = copy.deepcopy(mpvf["GSUB"])
    table = gsub.table

    fv = getattr(table, "FeatureVariations", None)
    if fv is not None:
        to_user = make_mplus_to_user(mpvf)
        lookups = set()
        for rec in fv.FeatureVariationRecord:
            for cond in rec.ConditionSet.ConditionTable:
                cond.FilterRangeMinValue = normalize(to_user(cond.FilterRangeMinValue))
                cond.FilterRangeMaxValue = normalize(to_user(cond.FilterRangeMaxValue))
            for sub in rec.FeatureTableSubstitution.SubstitutionRecord:
                lookups.update(sub.Feature.LookupListIndex)
        # Roboto に置き換えたグリフが M+ の字形に戻らないようにする
        for index in lookups:
            for st in table.LookupList.Lookup[index].SubTable:
                if hasattr(st, "mapping"):
                    for name in replaced & set(st.mapping):
                        del st.mapping[name]

    vf["GSUB"] = gsub


def make_mplus_to_user(mpvf):
    # M+ の正規化座標 (avar 適用後) をウェイト値に戻す関数を作る
    axis = next(a for a in mpvf["fvar"].axes if a.axisTag == "wght")
    seg = sorted(mpvf["avar"].segments["wght"].items()) if "avar" in mpvf else [(-1.0, -1.0), (0.0, 0.0), (1.0, 1.0)]

    def to_user(v):
        n = v
        for (x0, y0), (x1, y1) in zip(seg, seg[1:]):
            if y0 <= v <= y1:
                n = x0 if y1 == y0 else x0 + (v - y0) * (x1 - x0) / (y1 - y0)
                break
        if n >= 0:
            return axis.defaultValue + n * (axis.maxValue - axis.defaultValue)
        return axis.defaultValue + n * (axis.defaultValue - axis.minValue)

    return to_user


def normalize(wght):
    lo, hi = weights[0][0], weights[-1][0]
    if wght >= default_weight:
        return (wght - default_weight) / (hi - default_weight)
    return (wght - default_weight) / (default_weight - lo)


def mejiro_sfnt_names(version):
    copyright = (
        "McMejiro: Copyright (c) 2022- AndroPlus. "
        "Roboto: Copyright (c) 2012- Google. "
        "M+ FONTS: Copyright (C) 2021- M+ FONTS PROJECT."
    )
    return {
        0: copyright,
        1: "McMejiro",
        2: "Regular",
        3: "{0};McMejiro-Regular".format(version),
        4: "McMejiro Regular",
        5: version,
        6: "McMejiro-Regular",
        11: "https://mejiro.andro.plus",
        25: "McMejiro",
    }


def mejiro_gasp():
    return {
        8: 0x0002,  # antialias
        13: 0x000A,  # antialias, symmetric-smoothing
        65535: 0x000A,
    }


def set_mejiro_info(vf, version):
    # フォント情報の設定 (ライセンス表記は M+ のものを残す)
    name = vf["name"]
    keep = {13, 14}
    name.names = [n for n in name.names if n.nameID >= 256 or n.nameID in keep]
    for name_id, value in mejiro_sfnt_names(version).items():
        name.setName(value, name_id, 3, 1, 0x409)
    name.setName("McMejiro", 1, 3, 1, 0x411)

    buildStatTable(
        vf,
        [
            dict(
                tag="wght",
                name="Weight",
                values=[
                    dict(value=wght, name=style, flags=0x2 if wght == default_weight else 0)
                    for wght, style in weights
                ],
            )
        ],
        elidedFallbackName=2,
    )

    vf["OS/2"].achVendID = "andp"

    # Grid Fittingの設定
    vf["gasp"].gaspRange = mejiro_gasp()


if __name__ == "__main__":
    main()
