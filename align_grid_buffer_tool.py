# -*- coding: utf-8 -*-
import os
import math
import processing

from qgis.PyQt.QtGui import QPixmap, QIcon
from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtWidgets import (QFileDialog, QMessageBox, QGroupBox, QGridLayout, 
                                 QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                                 QComboBox, QCheckBox, QPushButton, QRadioButton, QAction)
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsPointXY, QgsWkbTypes, QgsVectorFileWriter
)
from qgis.utils import iface

# =========================================
# 🗺️ INTERACTIVE CANVAS CLICKING TOOL
# =========================================
class CanvasAngleTool(QgsMapToolEmitPoint):
    def __init__(self, canvas, dialog_parent, on_angle_calc_callback):
        super().__init__(canvas)
        self.canvas = canvas
        self.dialog = dialog_parent
        self.callback = on_angle_calc_callback
        self.points = []
        
        self.rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rubber_band.setColor(QtCore.Qt.red)
        self.rubber_band.setWidth(2)

    def canvasPressEvent(self, event):
        click_point = self.toMapCoordinates(event.pos())
        try:
            utm_text = self.dialog.editUTM.text().strip()
            if "EPSG:" in utm_text:
                target_crs = QgsCoordinateReferenceSystem(utm_text)
                src_crs = self.canvas.mapSettings().destinationCrs()
                transform = QgsCoordinateTransform(src_crs, target_crs, QgsProject.instance())
                point = transform.transform(click_point)
            else:
                point = click_point
        except Exception:
            point = click_point

        self.points.append(point)
        self.rubber_band.addPoint(click_point)

        if len(self.points) == 1:
            iface.messageBar().pushMessage("Angle Tool", "First point captured! Click the second point.", level=0, duration=3)
        elif len(self.points) == 2:
            pt1, pt2 = self.points[0], self.points[1]
            if pt1.x() == pt2.x() and pt1.y() == pt2.y():
                QMessageBox.warning(self.canvas.parent(), "Invalid Clicks", "Clicks in same spot. Retry.")
                self.reset_tool()
                self.dialog.show_and_focus()
                return

            dx = pt2.x() - pt1.x()
            dy = pt2.y() - pt1.y()
            angle = math.degrees(math.atan2(dy, dx))
            adjusted_angle = -angle
            if adjusted_angle < 0: adjusted_angle += 180
            
            self.callback(adjusted_angle % 180)
            self.reset_tool()
            self.dialog.show_and_focus()

    def deactivate(self):
        self.reset_tool()
        super().deactivate()

    def reset_tool(self):
        self.points = []
        self.rubber_band.reset(QgsWkbTypes.LineGeometry)
        self.canvas.unsetMapTool(self)


# =========================================
# 🧠 ROBUST MATH UTILITIES
# =========================================
def area_to_m2(val, unit):
    unit = unit.lower()
    if unit == "sqkm": return val * 1_000_000
    elif unit == "sqm": return val
    elif unit == "sqcm": return val / 10_000
    elif unit == "sqft": return val * 0.092903
    else: raise Exception("Invalid area unit")

def to_meters(val, unit):
    unit = unit.lower()
    if "km" in unit: return val * 1000
    elif "cm" in unit: return val / 100
    elif "mm" in unit: return val / 1000
    elif "feet" in unit or "ft" in unit: return val * 0.3048
    elif "mile" in unit: return val * 1609.34
    else: return val

def compute_utm_epsg(layer):
    crs_wgs = QgsCoordinateReferenceSystem("EPSG:4326")
    transform = QgsCoordinateTransform(layer.crs(), crs_wgs, QgsProject.instance())
    center = layer.extent().center()
    geo = transform.transform(QgsPointXY(center.x(), center.y()))
    zone = int((geo.x() + 180) / 6) + 1
    return 32600 + zone if geo.y() >= 0 else 32700 + zone


# =========================================
# 🚀 MAIN PLUGIN AND INTERFACE CLASS
# =========================================
class AlignGridPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.dialog = None
        self.action = None

    def initGui(self):
        # QGIS Toolbar aur Menu mein entry setup karne ke liye
        icon_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            icon = QIcon() # Fallback blank icon if logo not found

        self.action = QAction(icon, "AlignGrid Buffer Tool", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        
        self.iface.addPluginToVectorMenu("AlignGrid Buffer Tool", self.action)
        self.iface.addVectorToolBarIcon(self.action)

    def unload(self):
        # Uninstall ya deactivate hone par button hatane ke liye
        if self.action:
            self.iface.removePluginVectorMenu("AlignGrid Buffer Tool", self.action)
            self.iface.removeVectorToolBarIcon(self.action)

    def run(self):
        if not self.dialog:
            self.dialog = WorldBufferDialog(self.iface)
        self.dialog.show_and_focus()


class WorldBufferDialog(QtWidgets.QDialog):
    def __init__(self, iface):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.setWindowTitle("AlignGrid Buffer Tool - Public Release")
        self.resize(550, 620)
        
        self.setup_dynamic_ui()
        
        self.bufferUnit.addItems(["meters", "kilometers", "centimeters", "millimeters", "feet", "miles"])
        self.gridAreaUnit.addItems(["sqkm", "sqm", "sqcm", "sqft"]) 
        self.outputFormat.addItems(["ESRI Shapefile", "GeoJSON", "GPKG", "KML", "KMZ"]) 
        self.reportName.setText("output_result")
        self.editCustomAngle.setText("0.0")

        self.btnBrowse.clicked.connect(self.browse_input)
        self.btnBrowseOutput.clicked.connect(self.browse_output)
        self.btnRunAll.clicked.connect(self.run_all)
        self.btnRefreshCanvas.clicked.connect(self.refresh_map)
        self.btnCaptureAngle.clicked.connect(self.activate_canvas_clicker)
        self.radioNatural.toggled.connect(self.toggle_angle_mode)
        self.radioCustomClick.toggled.connect(self.toggle_angle_mode)
        
        self.toggle_angle_mode()

    def setup_dynamic_ui(self):
        main_layout = QVBoxLayout(self)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 5, 10)
        
        self.logoLabel = QLabel(self)
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            self.logoLabel.setPixmap(pixmap.scaledToHeight(50, QtCore.Qt.SmoothTransformation))
        else:
            self.logoLabel.setText("🌐")
            self.logoLabel.setStyleSheet("font-size: 32px; margin-right: 10px;")
            
        self.titleLabel = QLabel("ALIGNGRID BUFFER TOOL", self)
        self.titleLabel.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; font-family: 'Segoe UI', Arial;")
        header_layout.addWidget(self.logoLabel)
        header_layout.addWidget(self.titleLabel)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Configs
        group_in = QGroupBox("Input Configurations", self)
        layout_in = QGridLayout(group_in)
        self.inputPath = QLineEdit(group_in)
        self.btnBrowse = QPushButton("Browse...", group_in)
        layout_in.addWidget(QLabel("Input Vector File (SHP/KML/KMZ):", group_in), 0, 0)
        layout_in.addWidget(self.inputPath, 0, 1)
        layout_in.addWidget(self.btnBrowse, 0, 2)
        main_layout.addWidget(group_in)

        # Orientation
        group_angle = QGroupBox("Grid Orientation / Angle Mode", self)
        layout_angle = QGridLayout(group_angle)
        self.radioNatural = QRadioButton("Natural Optimization (Normal 0° Grid)", group_angle)
        self.radioNatural.setChecked(True)
        self.radioCustomClick = QRadioButton("Interactive Alignment (Click 2 Points on Map)", group_angle)
        self.editCustomAngle = QLineEdit(group_angle)
        self.editCustomAngle.setReadOnly(True)
        self.btnCaptureAngle = QPushButton("🎯 Select Baseline via Map", group_angle)
        layout_angle.addWidget(self.radioNatural, 0, 0, 1, 3)
        layout_angle.addWidget(self.radioCustomClick, 1, 0, 1, 3)
        layout_angle.addWidget(QLabel("Angle Setting (°):"), 2, 0)
        layout_angle.addWidget(self.editCustomAngle, 2, 1)
        layout_angle.addWidget(self.btnCaptureAngle, 2, 2)
        main_layout.addWidget(group_angle)

        # Parameters
        group_param = QGroupBox("Processing Parameters", self)
        layout_param = QGridLayout(group_param)
        self.gridAreaSqkm = QLineEdit(group_param)
        self.gridAreaUnit = QComboBox(group_param)
        self.chkClipGrid = QCheckBox("Clip grid to exact boundary", group_param)
        self.chkClipGrid.setChecked(True) 
        layout_param.addWidget(QLabel("Grid Cell Size:", group_param), 0, 0)
        layout_param.addWidget(self.gridAreaSqkm, 0, 1)
        layout_param.addWidget(self.gridAreaUnit, 0, 2)
        layout_param.addWidget(self.chkClipGrid, 0, 3)

        self.bufferDistance = QLineEdit(group_param)
        self.bufferUnit = QComboBox(group_param)
        layout_param.addWidget(QLabel("Buffer Distance:", group_param), 1, 0)
        layout_param.addWidget(self.bufferDistance, 1, 1)
        layout_param.addWidget(self.bufferUnit, 1, 2, 1, 2)

        self.editUTM = QLineEdit(group_param)
        self.editUTM.setReadOnly(True)
        layout_param.addWidget(QLabel("Target UTM CRS:", group_param), 2, 0)
        layout_param.addWidget(self.editUTM, 2, 1, 1, 3)
        main_layout.addWidget(group_param)

        # Output Settings
        group_out = QGroupBox("Output Settings", self)
        layout_out = QGridLayout(group_out)
        self.reportName = QLineEdit(group_out)
        self.outputFormat = QComboBox(group_out)
        layout_out.addWidget(QLabel("Base Name:", group_out), 0, 0)
        layout_out.addWidget(self.reportName, 0, 1)
        layout_out.addWidget(QLabel("Format:", group_out), 0, 2)
        layout_out.addWidget(self.outputFormat, 0, 3)

        self.outputPath = QLineEdit(group_out)
        self.btnBrowseOutput = QPushButton("Browse...", group_out)
        layout_out.addWidget(QLabel("Output Folder:", group_out), 1, 0)
        layout_out.addWidget(self.outputPath, 1, 1, 1, 2)
        layout_out.addWidget(self.btnBrowseOutput, 1, 3)
        main_layout.addWidget(group_out)

        layout_actions = QHBoxLayout()
        self.btnRefreshCanvas = QPushButton("Refresh Map Canvas", self)
        self.btnRunAll = QPushButton("🚀 Run Processing", self)
        self.btnRunAll.setDefault(True)
        layout_actions.addWidget(self.btnRefreshCanvas)
        layout_actions.addWidget(self.btnRunAll)
        main_layout.addLayout(layout_actions)

        self.statusLabel = QLabel("Ready", self)
        self.statusLabel.setFrameShape(QtWidgets.QFrame.StyledPanel)
        main_layout.addWidget(self.statusLabel)

    def toggle_angle_mode(self):
        is_manual = self.radioCustomClick.isChecked()
        self.btnCaptureAngle.setEnabled(is_manual)
        if self.radioNatural.isChecked():
            self.editCustomAngle.setText("0.0 (Normal Grid)")
        else:
            self.editCustomAngle.setText("0.0")

    def activate_canvas_clicker(self):
        self.hide()
        self.click_tool = CanvasAngleTool(self.canvas, self, self.receive_calculated_angle)
        self.canvas.setMapTool(self.click_tool)

    def show_and_focus(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def receive_calculated_angle(self, computed_angle):
        self.editCustomAngle.setText(f"{round(computed_angle, 2)}")

    def browse_input(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Vector File", "", "Vector (*.shp *.gpkg *.kml *.kmz)")
        if path: 
            self.inputPath.setText(path)
            self.update_utm_display(path)

    def update_utm_display(self, path):
        try:
            if not os.path.exists(path): return
            test_layer = QgsVectorLayer(path, "UTM_Test", "ogr")
            if test_layer.isValid() and test_layer.featureCount() > 0:
                utm_code = compute_utm_epsg(test_layer)
                self.editUTM.setText(f"EPSG:{utm_code}")
        except Exception:
            self.editUTM.setText("Error reading CRS")

    def browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder: self.outputPath.setText(folder)

    def refresh_map(self):
        self.canvas.refresh()

    def run_all(self):
        try:
            self.statusLabel.setText("Processing...")
            QtCore.QCoreApplication.processEvents()

            input_path = self.inputPath.text().strip()
            out_dir = self.outputPath.text().strip()
            base_name = self.reportName.text().strip()

            if not os.path.exists(input_path) or not os.path.exists(out_dir):
                raise Exception("Invalid input file or output folder path.")

            raw_layer = QgsVectorLayer(input_path, "AOI", "ogr")
            if not raw_layer.isValid() or raw_layer.featureCount() == 0:
                raw_layer = QgsVectorLayer(f"{input_path}|layername=features", "AOI_KML", "ogr")
                if not raw_layer.isValid():
                    raise Exception("Loaded vector layer is corrupted or empty.")

            aoi = processing.run("native:dropmzvalues", {
                "INPUT": raw_layer, "DROP_M_VALUES": True, "DROP_Z_VALUES": True, "OUTPUT": "memory:"
            })["OUTPUT"]

            utm_text = self.editUTM.text().strip()
            crs = QgsCoordinateReferenceSystem(utm_text) if "EPSG:" in utm_text else QgsCoordinateReferenceSystem(f"EPSG:{compute_utm_epsg(aoi)}")
            
            aoi = processing.run("native:reprojectlayer", {"INPUT": aoi, "TARGET_CRS": crs, "OUTPUT": "memory:"})["OUTPUT"]
            aoi = processing.run("native:fixgeometries", {"INPUT": aoi, "OUTPUT": "memory:"})["OUTPUT"]

            if aoi.geometryType() == 1: 
                buffer_aoi = processing.run("native:buffer", {"INPUT": aoi, "DISTANCE": 0.01, "OUTPUT": "memory:"})["OUTPUT"]
                aoi_for_grid = processing.run("native:dissolve", {"INPUT": buffer_aoi, "OUTPUT": "memory:"})["OUTPUT"]
            else:
                aoi_for_grid = processing.run("native:dissolve", {"INPUT": aoi, "OUTPUT": "memory:"})["OUTPUT"]

            angle = 0.0 if self.radioNatural.isChecked() else float(self.editCustomAngle.text() or 0.0)

            grid_val = float(self.gridAreaSqkm.text())
            area_m2 = area_to_m2(grid_val, self.gridAreaUnit.currentText())
            cell_size = math.sqrt(area_m2)

            ext = aoi_for_grid.extent()
            center_pt = ext.center()

            if abs(angle) > 0.01:
                max_dim = max(ext.xMaximum() - ext.xMinimum(), ext.yMaximum() - ext.yMinimum())
                padding = cell_size * 2 
                extent_str = f"{center_pt.x() - (max_dim / 2) - padding},{center_pt.x() + (max_dim / 2) + padding},{center_pt.y() - (max_dim / 2) - padding},{center_pt.y() + (max_dim / 2) + padding}"
            else:
                extent_str = f"{ext.xMinimum()},{ext.xMaximum()},{ext.yMinimum()},{ext.yMaximum()}"
            
            grid = processing.run("native:creategrid", {
                "TYPE": 2, "EXTENT": extent_str, "HSPACING": cell_size, "VSPACING": cell_size, 
                "HOVERLAP": 0, "VOVERLAP": 0, "CRS": aoi_for_grid.crs(), "OUTPUT": "memory:"
            })["OUTPUT"]
            
            if abs(angle) > 0.01:
                grid.startEditing()
                for feature in grid.getFeatures():
                    geom = feature.geometry()
                    if not geom.isEmpty():
                        geom.rotate(angle, center_pt)
                        grid.changeGeometry(feature.id(), geom)
                grid.commitChanges()

            grid = processing.run("native:extractbylocation", {
                "INPUT": grid, "PREDICATE": [0], "INTERSECT": aoi_for_grid, "OUTPUT": "memory:"
            })["OUTPUT"]

            if self.chkClipGrid.isChecked():
                grid = processing.run("native:clip", {"INPUT": grid, "OVERLAY": aoi_for_grid, "OUTPUT": "memory:"})["OUTPUT"]

            centroids = processing.run("native:centroids", {"INPUT": grid, "OUTPUT": "memory:"})["OUTPUT"]

            buf_val = float(self.bufferDistance.text())
            buffer = processing.run("native:buffer", {"INPUT": aoi, "DISTANCE": to_meters(buf_val, self.bufferUnit.currentText()), "OUTPUT": "memory:"})["OUTPUT"]

            # Exports
            selected_format = self.outputFormat.currentText()
            format_map = {
                "ESRI Shapefile": {"ext": ".shp", "driver": "ESRI Shapefile"},
                "GeoJSON": {"ext": ".geojson", "driver": "GeoJSON"},
                "GPKG": {"ext": ".gpkg", "driver": "GPKG"},
                "KML": {"ext": ".kml", "driver": "KML"},
                "KMZ": {"ext": ".kmz", "driver": "LIBKML"}
            }
            fmt_config = format_map.get(selected_format, format_map["ESRI Shapefile"])
            ext_str = fmt_config["ext"]
            
            grid_path = os.path.join(out_dir, f"{base_name}_grid{ext_str}")
            buffer_path = os.path.join(out_dir, f"{base_name}_buffer{ext_str}")
            cent_path = os.path.join(out_dir, f"{base_name}_centroids{ext_str}")

            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = fmt_config["driver"]
            options.fileEncoding = "UTF-8"

            if selected_format in ["KML", "KMZ"]:
                wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
                grid = processing.run("native:reprojectlayer", {"INPUT": grid, "TARGET_CRS": wgs84, "OUTPUT": "memory:"})["OUTPUT"]
                buffer = processing.run("native:reprojectlayer", {"INPUT": buffer, "TARGET_CRS": wgs84, "OUTPUT": "memory:"})["OUTPUT"]
                centroids = processing.run("native:reprojectlayer", {"INPUT": centroids, "TARGET_CRS": wgs84, "OUTPUT": "memory:"})["OUTPUT"]

            QgsVectorFileWriter.writeAsVectorFormatV3(grid, grid_path, aoi.transformContext(), options)
            QgsVectorFileWriter.writeAsVectorFormatV3(buffer, buffer_path, aoi.transformContext(), options)
            QgsVectorFileWriter.writeAsVectorFormatV3(centroids, cent_path, aoi.transformContext(), options)

            QgsProject.instance().addMapLayer(QgsVectorLayer(grid_path, f"{base_name.capitalize()} Grid Mesh", "ogr"))
            QgsProject.instance().addMapLayer(QgsVectorLayer(buffer_path, f"{base_name.capitalize()} Buffer", "ogr"))
            QgsProject.instance().addMapLayer(QgsVectorLayer(cent_path, f"{base_name.capitalize()} Centroids", "ogr"))

            QMessageBox.information(self, "Success", "Processing complete successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Execution Error", str(e))
        finally:
            self.statusLabel.setText("Ready")
