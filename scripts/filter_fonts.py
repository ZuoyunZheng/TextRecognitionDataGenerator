import argparse
from pathlib import Path
import numpy as np
from PIL import ImageFont, Image
from trdg import computer_text_generator
import shutil
from tqdm import tqdm
import random
from collections import defaultdict
from fontTools.ttLib import TTFont


# cf. https://superuser.com/a/1452828
def char_in_font(unicode_char, font):
    for cmap in font["cmap"].tables:
        if cmap.isUnicode():
            if ord(unicode_char) in cmap.cmap:
                return True
    return False


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--source",
        type=Path,
        default=Path(
            "/home/zuoyun.zheng/github/TextRecognitionDataGenerator/trdg/fonts/google-fonts/fonts-main/ofl"
        ),
        help="Path of original google fonts",
    )
    argparser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "/home/zuoyun.zheng/github/TextRecognitionDataGenerator/data/fonts/custom_fonts_2"
        ),
        help="Path of filtered google fonts",
    )
    args = argparser.parse_args()

    assert args.source.exists()
    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "_sanitycheck").mkdir(exist_ok=True)

    fonts = [str(f) for f in args.source.rglob("*.ttf")]
    print(fonts)
    manual_weird_fonts = [
        "flowblock",
        "flowcircular",
        "flowrounded",
        "jsmathcmex10",
        "jsmathcmsy10",
        "librebarcode39extended",
        "librebarcode39extendedtext",
        "librebarcode128",
        "librebarcode128text",
        "linefont",
        "redacted",
        "redactedscript",
        "wavefont",
    ]
    valid_fonts = defaultdict(list)
    char_set = "0123456789abcdefghijklmnopqrstuvwxyz!\"#$%&'()*+,-./:;?@[\\]^_`{|}~"

    for f in tqdm(fonts):
        # skip manual inspected weird fonts
        if f.split("/")[-2] in manual_weird_fonts:
            continue

        # check for unsuitable language. cf. https://superuser.com/a/1452828
        font = TTFont(f)
        _valid = True
        for c in char_set:
            if not char_in_font(c, font):
                print(f"{f} is not working, not supporting char set {c}")
                _valid = False
                break
        if not _valid:
            continue

        # check for trial rendering errors
        try:
            image, mask = computer_text_generator.generate(
                char_set,
                f,
                "#000010,#FFFFFF",
                64,
                0,
                1.0,
                0,
                True,
                False,
                3,
                "#000010,#FFFFFF",
            )
        except Exception as e:
            print(e, f"\n{f} is not working")
            continue

        # check for blank images ...
        if not np.array(image).any():
            print(f"{f} is not working")
            continue

        if f.split("/")[-2] not in valid_fonts:
            image.save(
                str(
                    args.output
                    / "_sanitycheck"
                    / (f.split("/")[-2] + "___" + Path(f).name.replace("ttf", "png"))
                )
            )
        valid_fonts[f.split("/")[-2]].append(f)

    for font_type in valid_fonts:
        for f in valid_fonts[font_type]:
            (args.output / f.split("/")[-2]).mkdir(exist_ok=True)
            shutil.copy(f, args.output / f.split("/")[-2] / Path(f).name)
