"""Entry point for reading MGZ-HD."""

# pylint: disable=invalid-name,no-name-in-module

__title__ = 'mgz_hd'
__description__ = 'Fork of mgz for parsing Age of Empires 2: HD replays'

from construct import (
    Struct, CString, Const, Int32ul, Embedded, Float32l,
    Terminated, If, Computed, this, Peek, Bytes, Int32ub
)

from mgz_hd.util import MgzPrefixed, ZlibCompressed, Version, VersionAdapter, get_version, get_save_version
from mgz_hd.header.ai import ai
from mgz_hd.header.replay import replay
from mgz_hd.header.map_info import map_info
from mgz_hd.header.initial import initial
from mgz_hd.header.achievements import achievements
from mgz_hd.header.scenario import scenario
from mgz_hd.header.lobby import lobby
from mgz_hd.header.hd import hd
# DE support can be commented or removed once HD parsing is complete
# from mgz_hd.header.de import de

compressed_header = Struct(
    "game_version"/CString(encoding='latin1'),
    "checker"/Peek(Float32l),
    "old_save_version"/VersionAdapter(Float32l),
    "new_save_version"/If(lambda ctx: ctx.old_save_version == -1, Int32ul),
    "save_version"/Computed(lambda ctx: get_save_version(ctx.old_save_version, ctx.new_save_version)),
    "version"/Computed(lambda ctx: get_version(ctx.game_version, ctx.save_version, None)),
    "hd"/If(lambda ctx: ctx.version == Version.HD and ctx.save_version > 12.34, hd),
    # "de"/If(lambda ctx: ctx.version == Version.DE, de),
    ai,
    replay,
    map_info,
    initial,
    achievements,
    scenario,
    lobby,
    Terminated
)

subheader = Struct(
    "check"/Peek(Int32ul),
    "chapter_address"/If(lambda ctx: ctx.check < 100000000, Int32ul),
    Embedded(MgzPrefixed(lambda ctx: ctx._.header_length - 4 - (4 if ctx.check < 100000000 else 0), ZlibCompressed(compressed_header)))
)

"""Header is compressed"""
header = Struct(
    "header_length"/Int32ul,
    Embedded(subheader),
    "log_version"/If(lambda ctx: ctx.save_version >= 11.76, Peek(Int32ul)),
    "version"/Computed(lambda ctx: get_version(ctx.game_version, ctx.save_version, ctx.log_version))
)
