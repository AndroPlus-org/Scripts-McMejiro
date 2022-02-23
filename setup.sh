#!/bin/bash

bldblu=${txtbld}$(tput setaf 4)

mkdir -p mejiro mplus roboto
cd roboto
wget https://fonts.google.com/download?family=Roboto -O roboto.zip
unzip roboto.zip
cd ../

cd mplus
wget https://github.com/coz-m/MPLUS_FONTS/archive/refs/heads/master.zip -O mplus.zip
unzip -j mplus.zip "*.ttf"
cd ../

echo "McMejiro を生成するには FontForge をインストールし、以下を実行してください"
echo "fontforge -lang=py -script mejiro.py"
tput sgr0
