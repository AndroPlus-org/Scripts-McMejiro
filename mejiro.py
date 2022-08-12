#!/usr/bin/env fontforge -lang=py -script
# -*- coding: utf-8 -*-

import fontforge
import psMat
from datetime import date

# Roboto のあるディレクトリのパス
roboto_path = "./roboto"

# M+ のあるディレクトリのパス
mplus_path = "./mplus"

# Mejiro を生成するディレクトリのパス
# 同じディレクトリに一時ファイルも生成される
mejiro_path = "./mejiro"

# フォントリスト
# Roboto ファイル名, M+ ファイル名, Mejiro ウェイト
font_list = [
	("Roboto-Thin.ttf", "Mplus1-Thin.ttf", "Thin"),
    ("Roboto-Light.ttf", "Mplus1-Light.ttf", "Light"),
    ("Roboto-Regular.ttf", "Mplus1-Regular.ttf", "Regular"),
    ("Roboto-Medium.ttf", "Mplus1-Medium.ttf", "Semibold"),
    ("Roboto-Bold.ttf", "Mplus1-Bold.ttf", "Bold"),
    ("Roboto-Black.ttf", "Mplus1-Black.ttf", "Extrabold"),
]

def main():
    # 縦書き対応
    fontforge.setPrefs('CoverageFormatsAllowed', 1)

    # バージョンを今日の日付から生成する
    today = date.today()
    version = "McMejiro-{0}".format(today.strftime("%Y%m%d"))

    for (rb, mp, weight) in font_list:
        rb_path = "{0}/{1}".format(roboto_path, rb)
        mp_path = "{0}/{1}".format(mplus_path, mp)
        ko_path = "{0}/McMejiro-{1}.ttf".format(mejiro_path, weight)
        generate_mejiro(rb_path, mp_path, ko_path, weight, version)

def mejiro_sfnt_names(weight, version):
    return (
        ('English (US)', 'Copyright',
         '''\
         McMejiro: Copyright (c) 2022- AndroPlus.

         Roboto: Copyright (c) 2012- Google.
         M+ FONTS: Copyright (C) 2021- M+ FONTS PROJECT.'''),
        ('English (US)', 'Family', 'McMejiro {0}'.format(weight)),
        ('English (US)', 'SubFamily', weight),
        ('English (US)', 'Fullname', 'McMejiro-{0}'.format(weight)),
        ('English (US)', 'Version', version),
        ('English (US)', 'PostScriptName', 'McMejiro-{0}'.format(weight)),
        ('English (US)', 'Vendor URL', 'https://mejiro.andro.plus'),
        ('English (US)', 'Preferred Family', 'McMejiro'),
        ('English (US)', 'Preferred Styles', weight),
        ('Japanese', 'Preferred Family', 'McMejiro'),
        ('Japanese', 'Preferred Styles', weight),
    )

def mejiro_gasp():
    return (
        (8, ('antialias',)),
        (13, ('antialias', 'symmetric-smoothing')),
        (65535, ('antialias', 'symmetric-smoothing')),
    )

def generate_mejiro(rb_path, mp_path, ko_path, weight, version):
    # M+ を開く
    font = fontforge.open(mp_path)

    # EMの大きさを2048に設定する
    font.em = 2048

    # Roboto を開く
    rbfont = fontforge.open(rb_path)

    # Roboto に含まれるグリフを削除する
    font.selection.none()
    rbfont.selection.all()
    for glyph in rbfont.selection.byGlyphs:
        if glyph.glyphname in font:
            font.selection.select(("more",), glyph.glyphname)
    font.clear()

    # Roboto をマージする
    font.mergeFonts(rb_path)
    for gs in font.gpos_lookups:
        li = font.getLookupInfo(gs)
        if li[2][0][0] == 'kern':
            font.removeLookup(gs)

    # ”fancy colon” U+EE01 を U+A789 にコピー
    font.selection.select(0xee01)
    font.copy()
    font.selection.select(0xa789)
    font.paste()

    # フォント情報の設定
    font.sfnt_names = mejiro_sfnt_names(weight, version)
    font.os2_vendor = "andp"

    # Grid Fittingの設定
    font.gasp = mejiro_gasp()

    # TTF の生成
    font.generate(ko_path, '', ('short-post', 'opentype', 'PfEd-lookups'))

if __name__ == '__main__':
    main()
