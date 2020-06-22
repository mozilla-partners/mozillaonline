#!/usr/bin/env python

import argparse
import codecs
import configparser
import datetime
import json
import os
import shutil
import zipfile


LEGACY_DISTROS = {
    "baidu": "firefox.baidusd",
    "baizhu": "firefox.dw",
    "cumulon": "firefox.newhua",
    "kingsoft": "firefox.kis",
    "mainOther": "firefox.com.cn",
    "mainWinFull": "full.firefox.com.cn",
    "mainWinStub": "stub.firefox.com.cn",
    "mainWinStubFallback": "firefox.latest",
    "mydown": "firefox.yesky",
    "others": "firefox.others",
    "qihoo": "firefox.3gj",
    "tencent": "firefox.qm",
    "xbsafe": "firefox.xbsafe2",
    "zol": "firefox.zol"
}


def update_dist_extension(distro, extensions):
    for ext_id in extensions:
        filename = "{}.xpi".format(ext_id)

        ext_path = os.path.join("..", distro, "distribution",
                                "extensions", filename)
        if os.path.exists(ext_path):
            print("Updating {}".format(ext_path))
            shutil.copy2(extensions[ext_id], ext_path)
            continue

        opt_ext_path = os.path.join("..", distro, "distribution",
                                    "optional-extensions", filename)
        if os.path.exists(opt_ext_path):
            print("Updating {}".format(opt_ext_path))
            shutil.copy2(extensions[ext_id], opt_ext_path)


def update_dist_ini(distro, version):
    legacy_distro = LEGACY_DISTROS.get(distro, "firefox.com.cn")

    cfg = configparser.ConfigParser()
    cfg.optionxform = str
    cfg.read([
        os.path.join("templates", "distribution.ini"),
        os.path.join("..", distro, "dist_addition.ini")
    ], "utf-8")

    cfg["Global"]["version"] = version
    cfg["Preferences"]["app.distributor.channel"] = json.dumps(distro)
    cfg["Preferences"]["app.partner.{}".format(distro)] = json.dumps(distro)
    cfg["Preferences"]["app.chinaedition.channel"] = json.dumps(legacy_distro)

    dist_ini_path = os.path.join("..", distro,
                                 "distribution", "distribution.ini")
    print("Updating {}".format(dist_ini_path))
    with codecs.open(dist_ini_path, "wb", "utf-8") as dist_ini:
        cfg.write(dist_ini, space_around_delimiters=False)


def update_extension(args):
    extensions = {}

    if args.ext:
        exts = args.ext
    else:
        ext_dir = os.path.join("templates", "extensions")
        exts = [os.path.join(ext_dir, ext_name)
            for ext_name in os.listdir(ext_dir)
            if ext_name.endswith(".xpi")]

    for ext in exts:
        with zipfile.ZipFile(ext) as ext_file:
            try:
                manifest_file = ext_file.open("manifest.json")
            except KeyError:
                manifest_file = ext_file.open("webextension/manifest.json")
            manifest = json.loads(manifest_file.read().decode("utf-8"))
            manifest_file.close()

            ext_id = manifest.get("applications", {}).get("gecko", {}).get("id")
            if not ext_id:
                print("id not found for extension: {}".format(ext))
                continue

            extensions[ext_id] = ext

    for distro in os.listdir(".."):
        if not os.path.exists(os.path.join("..", distro, "repack.cfg")):
            continue

        update_dist_extension(distro, extensions)



def update_ini(args):
    for distro in os.listdir(".."):
        if not os.path.exists(os.path.join("..", distro, "repack.cfg")):
            continue

        update_dist_ini(distro, "{}.{}".format(args.year, args.month))


def main():
    today = datetime.date.today()

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
      description='subcommands to update parts of the each distribution',
      help='run each subcommand to see more details')

    ini_parser = subparsers.add_parser('ini')
    ini_parser.add_argument("-y", "--year", default=today.year, type=int,
      help="set year part of distribution version", metavar="YYYY")
    ini_parser.add_argument("-m", "--month", default=today.month, type=int,
      help="set month part of distribution version", metavar="MM")
    ini_parser.set_defaults(func=update_ini)

    ext_parser = subparsers.add_parser('extension')
    ext_parser.add_argument("-e", "--ext", nargs='+',
      help="the extension file(s) to copy into each distribution",
      metavar="ext.xpi")
    ext_parser.set_defaults(func=update_extension)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
