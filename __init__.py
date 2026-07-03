# -*- coding: utf-8 -*-
def classFactory(iface):
    from .align_grid_buffer_tool import AlignGridPlugin
    return AlignGridPlugin(iface)