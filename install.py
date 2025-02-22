#!/usr/bin/env python3
# Minecraft-in-python, a sandbox game
# Copyright (C) 2020-2023  Minecraft-in-python team
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import uuid
import venv
from json import dump, load
from os import chmod, environ, makedirs, mkdir, path, pathsep
from re import match, search
from shutil import copytree, rmtree
from stat import S_IRUSR, S_IWUSR, S_IXUSR
from subprocess import run
from sys import platform, version_info
from textwrap import dedent


def main():
    parser = argparse.ArgumentParser(
        description="Game installer", usage="%(prog)s [option]")
    parser.add_argument("--no-install-deps",
                        action="store_true", help="skip install game dependencies")
    parser.add_argument("--no-register",
                        action="store_true", help="skip register player")
    parser.add_argument("--no-gen-script", action="store_true",
                        help="skip generate startup script")
    args = parser.parse_args()
    # 检查python版本
    check_ver()
    # 最好遵守Mojang的Minecraft eula
    see_eula()
    # 安装
    install(args)
    # 注册玩家
    if not args.no_register:
        register_user()
    # 创建启动脚本
    if not args.no_gen_script:
        gen_script()
    # 完成！
    if platform.startswith("win"):
        pycmd = "python"
    else:
        pycmd = "python3"
    print("Use `%s -m minecraft` to start game." % pycmd)


def check_ver():
    if version_info[:2] < (3, 8):
        print("Minecraft-in-python needs Python3.8 or later, but %s found!" %
              ".".join([str(s) for s in version_info[:2]]))
        exit(1)


def see_eula():
    print("NOTE: This is not official Minecraft product. Not approved by or associated with Mojang.")
    print("      Visit `https://minecraft.net/term` for more information.")
    input("NOTE: Press ENTER when you have finished reading the above information: ")


def install(args):
    mcpypath = storage_dir()
    version = get_version()
    if not path.isdir(mcpypath):
        mkdir(mcpypath)
    install_settings()
    for name in ["log", "saves", "screenshot", "resource-pack", "version"]:
        if not path.isdir(path.join(mcpypath, name)):
            mkdir(path.join(mcpypath, name))
    if not path.isdir(path.join(mcpypath, "lib", version)):
        makedirs(path.join(mcpypath, "lib", version))
    if not path.isfile(path.join(mcpypath, "version", version, "pyvenv.cfg")):
        print("Creating virtual environments...")
        venv.create(path.join(mcpypath, "version", version), with_pip=True)
    if path.isdir(path.join(mcpypath, "version", version, "minecraft")):
        rmtree(path.join(mcpypath, "version", version, "minecraft"))
    copytree(get_file("minecraft"), path.join(
        mcpypath, "version", version, "minecraft"))
    if not args.no_install_deps:
        pybin = "Scripts\\python.exe" if platform.startswith(
            "win") else "bin/python"
        pybin_dir = "Scripts" if platform.startswith("win") else "bin"
        environ["PATH"] = path.join(mcpypath, "version", version, pybin_dir) + pathsep + environ["PATH"]
        environ["VITURAL_ENV"] = path.join(mcpypath, "version", version)
        code = run([path.join(mcpypath, "version", version, pybin), "-m", "pip", "install", "-U",
                   "-r", get_file("requirements.txt")], env=environ).returncode
        if code != 0:
            exit(1)


def install_settings():
    source = {
        "fov": 70,
        "lang": "${auto}",
        "resource-pack": ["${default}"],
        "viewport": {
            "width": 800,
            "height": 600
        }
    }
    target = {}
    mcpypath = storage_dir()
    if path.isfile(path.join(mcpypath, "settings.json")):
        target = load(open(path.join(mcpypath, "settings.json")))
    for k, v in source.items():
        if k not in target or not isinstance(target[k], type(v)):
            target[k] = v
    dump(target, open(path.join(mcpypath, "settings.json"), "w+"))


def register_user():
    mcpypath = storage_dir()
    is_ready = True
    previous_uuid = None
    # 如果之前已经存在玩家信息
    if path.isfile(path.join(mcpypath, "player.json")):
        player = load(open(path.join(mcpypath, "player.json")))
        # 是否符合当前的数据格式呢？
        try:
            if "uuid" not in player:
                is_ready = False
            if "name" not in player:
                is_ready = False
            if not match("^[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12}$", player["uuid"]):
                is_ready = False
        except:
            is_ready = False
        # 如果不符合，将之前的uuid记录下来（如果存在的话）
        if is_ready == False:
            s = open(path.join(mcpypath, "player.json"), "r").read()
            if (result := search("\"[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12}\"", s)) is not None:
                previous_uuid = result.group(0)[1:-1]
    else:
        is_ready = False
    if not is_ready:
        player_id = previous_uuid or str(uuid.uuid4())
        print("Your uuid is %s, do not change it!" % player_id)
        player_name = ""
        while all([c for c in map(lambda c: any(
                [c.isalpha(), c.isdigit(), c == "_"]), player_name)]) and len(player_name) < 5:
            player_name = input("Your name: ")
        dump({"uuid": player_id, "name": player_name}, open(
            path.join(mcpypath, "player.json"), "w+"))


def gen_script():
    # WARN: 启动脚本运行仍有问题
    while True:
        ret = input("Generate startup script[Y/n]? ")
        if (ret.lower() == "y") or (len(ret) == 0):
            break
        elif ret.lower() == "n":
            return
    mcpypath = storage_dir()
    version = get_version()
    if platform.startswith("win"):
        name = get_file("run.bat")
        script = dedent("""\
            @echo off
            cd {0}
            REM call Scripts\\active.bat
            python -m minecraft
            REM call Scripts\\deactive.bat
        """.format(path.join(mcpypath, "version", version)))
    else:
        name = get_file("run.sh")
        script = dedent("""\
            #!/usr/bin/env sh
            cd {0}
            source bin/active
            python3 -m minecraft $*
            deactive
        """.format(path.join(mcpypath, "version", version)))
    with open(name, "w+") as f:
        f.write(script)
        print("Startup script at `%s`" % name)
    if not platform.startswith("win"):
        chmod(name, S_IRUSR | S_IWUSR | S_IXUSR)


def get_file(f):
    # 返回文件目录下的文件名
    return path.abspath(path.join(path.dirname(__file__), f))


def get_version():
    # 从`minecraft/utils/utils.py`文件里面把版本号"抠"出来
    f = open(path.join(get_file("minecraft"),
             "utils", "utils.py"), encoding="utf-8")
    start_find = False
    for line in f.readlines():
        if line.strip() == "VERSION = {":
            start_find = True
        elif (line.strip() == "}") and start_find:
            start_find = False
        elif line.strip().startswith("\"str\"") and start_find:
            # 匹配版本号
            # 一位主版本号, 两位小版本号/修订版本号
            # 匹配 -alpha, -beta 后缀, -pre, -rc 后跟数字
            return search(r"\d(\.\d{1,2}){2}(\-alpha|\-beta|\-pre\d+|\-rc\d+)?", line.strip()).group()


def storage_dir():
    # 搜索文件存储位置
    if "MCPYPATH" in environ:
        mcpypath = environ["MCPYPATH"]
    elif platform == "darwin":
        mcpypath = path.join(path.expanduser(
            "~"), "Library", "Application Support", "mcpy")
    else:
        mcpypath = path.join(path.expanduser("~"), ".mcpy")
    return mcpypath


if __name__ == "__main__":
    main()
