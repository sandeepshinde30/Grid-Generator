# 🌐 Grid Generator Tool for QGIS

!\[QGIS Version](https://img.shields.io/badge/QGIS-3.0%2B-green?logo=qgis)
!\[License](https://img.shields.io/badge/License-MIT-blue.svg)
!\[Version](https://img.shields.io/badge/Version-1.0.0-orange.svg)

**Grid Generator Tool** is a robust QGIS plugin designed to generate highly customized, aligned grids, centroids, and precision buffers across multiple vector formats (SHP, KML, KMZ, GPKG). It bypasses standard QGIS limitations by offering interactive map-click alignment and micro-scale buffering down to centimeters and millimeters.

## ✨ Key Features

* **Interactive Grid Alignment:** Click directly on the map canvas to draw a baseline and automatically rotate your grid to match specific geographical features or property lines.
* **Smart CRS \& UTM Auto-Detection:** Automatically calculates and applies the correct UTM zone based on the input layer's centroid—no more manual reprojection guesswork.
* **Micro-Precision Buffering:** Create buffers not just in meters or kilometers, but in centimeters and millimeters for highly accurate engineering, drone mapping, and architectural setups.
* **Broad Format Support:** Natively processes and exports to ESRI Shapefile, GeoJSON, GeoPackage (GPKG), KML, and KMZ.
* **Automated Data Cleaning:** Automatically drops Z/M values, fixes invalid geometries, and reprojects layers on the fly during processing.
* **All-in-One Output:** Simultaneously generates the aligned grid mesh, boundary buffers, and grid cell centroids in a single run.

## 🚀 Installation

**Method 1: Install via QGIS Plugin Repository**

1. Open QGIS.
2. Go to `Plugins` > `Manage and Install Plugins...`
3. Search for **Grid Generator Tool** and click `Install Plugin`.

**Method 2: Manual Installation from GitHub**

1. Download this repository as a `.zip` file.
2. Open QGIS and navigate to `Plugins` > `Manage and Install Plugins...`
3. Select `Install from ZIP` on the left panel.
4. Browse to the downloaded `.zip` file and click `Install Plugin`.

## 🛠️ Usage Guide

1. **Launch the Tool:** Click the `🌐` icon in your Vector Toolbar or navigate to `Vector` > `Grid Generator Tool`.
2. **Input Layer:** Browse and select your target vector file (SHP/KML/KMZ).
3. **Grid Orientation:**

   * *Natural Optimization:* Keeps a standard North-Up (0°) grid.
   * *Interactive Alignment:* Click `🎯 Select Baseline via Map`, then click two points on your map to define the custom grid angle.
4. **Processing Parameters:**

   * Set your desired grid cell area (e.g., Sq Meter, Sq Km).
   * Specify the buffer distance and unit (meters, cm, mm).
5. **Output:** Define your output base name, format (e.g., GeoPackage or KML), and destination folder.
6. **Run:** Click `🚀 Run Processing`. The generated Grid, Buffer, and Centroids will automatically load into your QGIS canvas.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/yourusername/AlignGrid-Buffer-Tool/issues).

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

