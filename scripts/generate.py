import errno
from multiprocessing import Pool
import os
from pathlib import Path
import random as rnd
import sys
from tqdm import tqdm

import numpy as np
from trdg.run import parse_arguments
from trdg.data_generator import FakeTextDataGenerator
from trdg.string_generator import (
    create_strings_from_dict,
    create_strings_from_file,
    create_strings_from_wikipedia,
    create_strings_randomly,
)
from trdg.utils import load_dict, load_fonts


def generate_part(args):
    """
    Description: Main function
    """

    # Fix seeding
    # cf. https://github.com/clovaai/synthtiger/blob/master/synthtiger/gen.py#L76
    rnd.seed(0)
    np.random.set_state(np.random.RandomState(np.random.MT19937(0)).get_state())

    # Create the directory if it does not exist.
    try:
        os.makedirs(args.output_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    # Creating word list
    if args.dict:
        lang_dict = []
        if os.path.isfile(args.dict):
            with open(args.dict, "r", encoding="utf8", errors="ignore") as d:
                lang_dict = [l for l in d.read().splitlines() if len(l) > 0]
        else:
            sys.exit("Cannot open dict")
    else:
        lang_dict = load_dict(
            Path("trdg/dicts") / (args.language + ".txt")
        )

    # Create font (path) list
    if args.font_dir:
        # fonts = [
        #    os.path.join(args.font_dir, p)
        #    for p in os.listdir(args.font_dir)
        #    if os.path.splitext(p)[1] == ".ttf"
        # ]

        fonts = [
            [str(ttf_f) for ttf_f in f.glob("*.ttf")]
            for f in Path(args.font_dir).iterdir()
        ]
        fonts = [f for f in fonts if f]
    elif args.font:
        if os.path.isfile(args.font):
            fonts = [args.font]
        else:
            sys.exit("Cannot open font")
    else:
        fonts = load_fonts(args.language)

    # Creating synthetic sentences (or word)
    strings = []

    if args.use_wikipedia:
        strings = create_strings_from_wikipedia(args.length, args.count, args.language)
    elif args.input_file != "":
        strings = create_strings_from_file(args.input_file, args.count)
    elif args.random_sequences:
        strings = create_strings_randomly(
            args.length,
            args.random,
            args.count,
            args.include_letters,
            args.include_numbers,
            args.include_symbols,
            args.language,
            args.rs_mean,
            args.rs_std,
        )
        # include a quarter of natural language
        # wiki_strings = (create_strings_from_wikipedia(args.length, int(args.count * 0.25), args.language))
        # Set a name format compatible with special characters automatically if they are used
        if args.include_symbols or True not in (
            args.include_letters,
            args.include_numbers,
            args.include_symbols,
        ):
            args.name_format = 2
    else:
        strings = create_strings_from_dict(
            args.length, args.random, args.count, lang_dict
        )

    if args.language == "ar":
        from arabic_reshaper import ArabicReshaper
        from bidi.algorithm import get_display

        arabic_reshaper = ArabicReshaper()
        strings = [
            " ".join(
                [get_display(arabic_reshaper.reshape(w)) for w in s.split(" ")[::-1]]
            )
            for s in strings
        ]
    if args.case == "upper":
        strings = [x.upper() for x in strings]
    if args.case == "lower":
        strings = [x.lower() for x in strings]

    string_count = len(strings)

    p = Pool(args.thread_count)
    for _ in tqdm(
        p.imap_unordered(
            FakeTextDataGenerator.generate_from_tuple,
            zip(
                [i for i in range(0, string_count)],
                strings,
                [fonts[rnd.randrange(0, len(fonts))] for _ in range(0, string_count)],
                [args.output_dir] * string_count,
                [args.format] * string_count,
                [args.extension] * string_count,
                [args.skew_angle] * string_count,
                [args.random_skew] * string_count,
                [args.blur] * string_count,
                [args.random_blur] * string_count,
                [args.background] * string_count,
                [args.distorsion] * string_count,
                [args.distorsion_orientation] * string_count,
                [args.handwritten] * string_count,
                [args.name_format] * string_count,
                [args.width] * string_count,
                [args.alignment] * string_count,
                [args.text_color] * string_count,
                [args.orientation] * string_count,
                [args.space_width] * string_count,
                [args.character_spacing] * string_count,
                [args.margins] * string_count,
                [args.random_margins] * string_count,
                [args.fit] * string_count,
                [args.output_mask] * string_count,
                [args.word_split] * string_count,
                [args.image_dir] * string_count,
                [args.stroke_width] * string_count,
                [args.stroke_fill] * string_count,
                [args.erode_quant] * string_count,
                [args.random_stroke] * string_count,
                [args.image_mode] * string_count,
                [args.output_bboxes] * string_count,
            ),
        ),
        total=args.count,
    ):
        pass
    p.terminate()

    if args.name_format == 2:
        # Create file with filename-to-label connections
        with open(
            os.path.join(args.output_dir, "labels.txt"), "w", encoding="utf8"
        ) as f:
            for i in range(string_count):
                file_name = str(i) + "." + args.extension
                label = strings[i]
                if args.space_width == 0:
                    label = label.replace(" ", "")
                f.write("{} {}\n".format(file_name, label))

if __name__ == "__main__":
    # Argument parsing
    args = parse_arguments()
    output_root_dir = args.output_dir

    parts = args.count // 10000
    for part in range(parts):
        args.output_dir = str(Path(output_root_dir) / str(part+1)) 
        args.count = 10000
        print(args.output_dir)
        generate_part(args)