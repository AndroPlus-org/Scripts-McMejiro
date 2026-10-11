#!/bin/bash

bldblu=${txtbld}$(tput setaf 4)

mkdir -p mejiro mplus roboto
cd roboto
wget "https://github.com/google/fonts/raw/main/ofl/roboto/Roboto%5Bwdth,wght%5D.ttf" -O "Roboto[wdth,wght].ttf"
# 静的フォントはバリアブルフォントから切り出す (Google Fonts の ZIP 配布は終了)
for w in Thin:100 Light:300 Regular:400 Medium:500 Bold:700 Black:900; do
    fonttools varLib.instancer "Roboto[wdth,wght].ttf" wght=${w#*:} wdth=100 --static -o "Roboto-${w%%:*}.ttf"
done
cd ../

cd mplus
wget https://github.com/coz-m/MPLUS_FONTS/archive/refs/heads/master.zip -O mplus.zip
unzip -j mplus.zip "*.ttf"
cd ../

echo "McMejiro を生成するには FontForge をインストールし、以下を実行してください"
echo "fontforge -lang=py -script mejiro.py"
echo "バリアブルフォントを生成するには fontTools をインストールし、以下を実行してください"
echo "python3 mejiro_vf.py"
tput sgr0
