# Scripts

[McMejiro](https://github.com/AndroPlus-org/McMejiro) をビルドするためのスクリプトです。

| スクリプト | 生成物 | 必要なもの |
|:---|:---|:---|
| `mejiro.py` | 静的フォント `mejiro/McMejiro-*.ttf` (6 ウェイト) | FontForge |
| `mejiro_vf.py` | バリアブルフォント `mejiro/McMejiro[wght].ttf` | Python 3, fontTools |

## 使い方

```
git clone https://github.com/AndroPlus-org/Scripts-McMejiro make_mejiro
```

```
cd make_mejiro
```

M+ 1 と Roboto (静的フォント・バリアブルフォント) を `mplus/`、`roboto/` にダウンロードします。`wget`、`unzip`、fontTools (`pip install fonttools`) が必要です。Roboto の静的フォントはバリアブルフォントから切り出します。

```
bash setup.sh
```

#### Ubuntu / WSL での fontTools の導入

apt の `python3-fonttools` は古く、`fonttools varLib.instancer: error: unrecognized arguments: --static` などのエラーになります。venv を作って pip で最新版を入れてください (Ubuntu 23.04 以降はシステムへの `pip install` が拒否されるため)。

```
sudo apt install python3-venv
python3 -m venv ~/.venv/mejiro
source ~/.venv/mejiro/bin/activate
pip install fonttools
```

以降は `source ~/.venv/mejiro/bin/activate` してから `setup.sh` や `mejiro_vf.py` を実行します。apt 版が入っている場合は `sudo apt remove python3-fonttools fonttools` で削除しておくと混同しません。

### 静的フォント

FontForge interactive console で実行します。

```
fontforge -lang=py -script mejiro.py
```

| McMejiro | M+ 1 | Roboto |
|:---:|:---:|:---:|
| **Thin** | Thin | Thin |
| **Light** | Light | Light |
| **Regular** | Regular | Regular |
| **Semibold** | Medium | Medium |
| **Bold** | Bold | Bold |
| **Extrabold** | Black | Black |

### バリアブルフォント (wght 100-900)

M+ 1 (`MPLUS1[wght].ttf`) と Roboto (`Roboto[wdth,wght].ttf`) のバリアブルフォントから `mejiro/McMejiro[wght].ttf` を生成します。

```
pip install fonttools
```

```
python3 mejiro_vf.py
```

- ウェイト軸 `wght` 100-900 (デフォルト 400)
- Roboto の幅軸 `wdth` は 100 で固定
- 100 刻みの 9 ウェイトでそれぞれ合成したものをマスターにしてまとめ直すため、元のバリアブルフォントの形状をそのまま再現します
- 名前付きインスタンス: Thin (100) / ExtraLight (200) / Light (300) / Regular (400) / Medium (500) / SemiBold (600) / Bold (700) / ExtraBold (800) / Black (900)

インスタンス名は標準的なウェイト名に合わせているため、静的フォントとは対応が異なります (静的フォントの Semibold は Medium から作っているので wght 500 相当)。
