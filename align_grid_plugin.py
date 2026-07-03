import os
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant
from .align_grid_buffer_tool import WorldBufferDialog

class WorldBufferPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.action = None
        self.dlg = None

    def initGui(self):
        # Icon ka absolute path create karna compulsory hai
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        
        # Agar icon.png folder mein nahi hai, to QGIS ka default system icon lag jayega
        if os.path.exists(icon_path):
            plugin_icon = QIcon(icon_path)
        else:
            plugin_icon = QIcon.fromTheme('mActionAllTouched') # Fallback standard QGIS icon
            
        # QAction ke andar text aur parent window dena zaroori hai
        self.action = QAction(
            plugin_icon, 
            "AlignGrid Buffer Tool", 
            self.iface.mainWindow()
        )
        
        # Tooltip aur Statusbar text set kar rahe hain taaki blank na dikhe
        self.action.setToolTip("AlignGrid Buffer Tool - Create Aligned Grids and Buffers")
        self.action.setStatusTip("Launch the AlignGrid Buffer Tool setup window")
        
        self.action.triggered.connect(self.run)
        
        # Toolbar aur Menu dono mein add kar rahe hain
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("AlignGrid Buffer Tool", self.action)

    def unload(self):
        try:
            if self.action:
                self.iface.removeToolBarIcon(self.action)
                self.iface.removePluginMenu("AlignGrid Buffer Tool", self.action)
        except Exception:
            pass

    def run(self):
        if not self.dlg:
            self.dlg = WorldBufferDialog(self.iface)
            
            self.dlg.outputFormat.clear()
            self.dlg.outputFormat.addItems([
                "ESRI Shapefile",
                "GeoJSON",
                "GPKG",
                "KML",
                "KMZ"
            ])
            
            if not self.dlg.reportName.text():
                self.dlg.reportName.setText("output_result")

        # CRITICAL FIX: exec_() ki jagah hum custom non-modal focus driver call kar rahe hain
        # Taaki Map Canvas Clicking Tool bina freeze huye background mein chal sake.
        self.dlg.show_and_focus()
