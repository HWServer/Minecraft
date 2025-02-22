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

import pyglet
from minecraft import resource_pack
from minecraft.gui.frame import Frame
from minecraft.scene import Scene
from minecraft.utils.utils import *
from pyglet.gl import *
from pyglet.sprite import Sprite
from pyglet.window import key, mouse


class GameScene(Scene):
    """这里就正式开始游戏喽！"""

    def __init__(self):
        super().__init__()