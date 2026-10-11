# Scripts

McMejiro をビルドするためのスクリプトです。

## 使い方

```
git clone https://github.com/AndroPlus-org/Scripts-McMejiro make_mejiro
```

```
cd make_mejiro
```

```
bash setup.sh
```

### FontForge interactive console

```
fontforge -lang=py -script mejiro.py
```

### バリアブルフォント (wght 100-900)

M+ 1 と Roboto のバリアブルフォントから `mejiro/McMejiro[wght].ttf` を生成します。

```
pip install fonttools
```

```
python3 mejiro_vf.py
```
