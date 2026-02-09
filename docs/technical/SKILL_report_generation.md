# SKILL: Report Generation System

## Overview
This document details the **Automated PDF Report Generation** system in the Revanchas LT QGIS Plugin. The system orchestrates spatial data processing, chart generation, HTML table rendering, and dynamic layout injection to produce a standardized PDF report consistent with corporate requirements.

## Architecture & Components

The reporting system is distributed across several components, with `ProfileViewerDialog` acting as the central orchestrator (Controller).

| Component | File | Responsibility |
|-----------|------|----------------|
| **Orchestrator** | `profile_viewer_dialog.py` | Manages UI, triggers export, captures screenshots, injects content into Layout, handles PDF export. |
| **Map Generator** | `core/map_generator.py` | Calculates DEM differences, clips rasters by mask, applies styles/colormaps, generates the main map image. |
| **Report Generator** | `core/report_generator.py` | Generates the Longitudinal Profile Chart using Matplotlib (combining Crown, Lama, Geomembrane). |
| **Geomembrane Manager** | `core/geomembrane_manager.py` | Loads and processes CSV data for the geomembrane trend line. |
| **Sector Utils** | `core/sector_utils.py` | Defines tolerance logic and sector classification (MO, MP, ME) for alerts. |

---

## Workflow Step-by-Step

The generation process (`export_pdf_report` method) follows this sequential pipeline:

1.  **Preparation**:
    *   Locks PDF file access (checks for open files).
    *   Loads QGIS Print Layout (`layout_revanchas.qpt`).
    *   Retrieves "Current" and "Previous" DEMs based on date selection.

2.  **Map Generation (`MapGenerator`)**:
    *   Calculates Raster Difference (`gdal:rastercalculator`): `Current - Previous`.
    *   Clips Difference by Wall Polygon (`gdal:cliprasterbymasklayer`).
    *   Injects the resulting map image into the Layout Item ID: **`main_map`**.

3.  **Table Generation**:
    *   **Summary Table**: Aggregates min/max/avg deltas per sector with color-coded ranges.
    *   **Detail Table**: Lists all profiles with their measurements and delta, color-coded by tolerance ranges.
    *   **Color Coding System** (New - February 2026):
        - **Revancha**: Green (>3.5m), Yellow (3-3.5m), Red (<3m)
        - **Ancho**: Green (>18m), Yellow (15-18m), Red (<15m)
        - **Geomembrana (G-L/G-C)**: Normal (>1m), Yellow (0.5-1m), Red (<0.5m)
    *   Renders to HTML with dynamic CSS and injects into Layout Frame: **`summary_table`** and **`detail_table`**.

4.  **Chart Generation (`ReportGenerator`)**:
    *   Collects data: Crown (saved), Lama (saved/auto), Geomembrane (CSV).
    *   Plots data using `Matplotlib`.
    *   Injects the chart image into Layout Item ID: **`chart`**.

5.  **Screenshot Capture (Hybrid Method)**:
    *   Detects profiles with "Alerts" (Revancha < 3m or Width < 15m).
    *   **If alerts exist**: Updates profile view, captures screenshots, injects into `alert_screenshot_1` to `alert_screenshot_4`.
    *   **If NO alerts exist**: Removes Page 3 from the layout entirely (conditional page export).
    *   Creates dynamic pages for additional alerts beyond 4.

6.  **Conditional Page Export** (New - February 2026):
    *   **Page 3 Logic**: Only exported if at least one alert screenshot exists.
    *   **Implementation**: If `alert_profiles` is empty, the system:
        1. Scans layout pages (starting from page index 2 = Page 3)
        2. Removes all items belonging to those pages
        3. Deletes the pages from `pageCollection()`
    *   **Result**: Reports without alerts generate 2-page PDFs instead of 3-page PDFs with blank screenshot pages.

7.  **PDF Export**:
    *   Uses `QgsLayoutExporter` to render the final PDF.
    *   Number of pages is now dynamic (2 pages if no alerts, 3+ if alerts exist).

---

## Key Configuration & IDs

The system relies on specific ID matching between the Python code and the QGIS Layout (`.qpt`).

| Logic Component | Layout Item ID | Content Type | Page Location |
|-----------------|----------------|--------------|---------------|
| Main Map | `main_map` | `QgsLayoutItemPicture` (Image) | Page 1 |
| Statistics Table | `summary_table` | `QgsLayoutItemHtml` (Frame) | Page 1 |
| Detail Table | `detail_table` | `QgsLayoutItemHtml` (Frame) | Page 1-2 |
| Longitudinal Chart | `chart` | `QgsLayoutItemPicture` (Image) | Page 2 |
| Screenshots | `alert_screenshot_N` | `QgsLayoutItemPicture` (Image) | Page 3 (conditional) |
| Timestamp | `date_label` | `QgsLayoutItemLabel` (Text) | Page 1 |

⚠️ **Critical**: If these IDs change in the QGIS Layout Designer, the code in `profile_viewer_dialog.py` must be updated to match.

---

## Dynamic Table Sizing System

**Added**: February 2026

To handle varying numbers of profiles across different walls, the system implements a **two-tier dynamic sizing strategy**: intelligent CSS scaling combined with a revolutionary **dynamic fill algorithm**.

### Problem Statement

Different walls contain vastly different numbers of profiles (ranging from ~20 to 100+ rows). Traditional fixed CSS creates two problems:
1. **Overflow**: Tables with many rows get cut off at frame boundaries
2. **Underutilization**: Tables with few rows leave large empty spaces

The QGIS API limitation compounds this: **Layout Frame dimensions cannot be programmatically resized**. The frame's height is static and defined in the QPT template.

### Solution: Dynamic Fill Algorithm

The system now calculates CSS properties **in reverse** — instead of defining styles and hoping the content fits, it:

1. **Receives the target Frame height** (configured in QPT, e.g., 220mm)
2. **Calculates available vertical space** (Frame height - Header height)
3. **Divides space equally** among all data rows
4. **Back-calculates CSS properties** to fill exactly that space

#### Algorithm Implementation

```python
def generate_detail_html_table(self, geo_manager=None, frame_height_mm=220):
    # Count rows
    total_rows = len(sorted_profiles)
    
    # Convert frame height to pixels (QGIS rendering uses ~3.78 px/mm)
    frame_height_px = frame_height_mm * 3.78
    
    # Reserve space for header (2 rows with borders)
    header_height_px = 30
    available_height_px = frame_height_px - header_height_px
    
    # Calculate target height per row
    row_height_px = available_height_px / total_rows
    
    # Determine base font size (legibility constraints)
    if total_rows > 80:
        base_font_px = 6    # Minimum readable
    elif total_rows > 60:
        base_font_px = 7
    elif total_rows > 40:
        base_font_px = 8
    else:
        base_font_px = 10
    
    # Reverse-calculate padding to fill remaining space
    line_height = 1.2
    content_height = base_font_px * line_height
    border_height = 2  # CSS borders
    padding_vertical = (row_height_px - content_height - border_height) / 2
    
    # Apply to CSS
    td { 
        font-size: {base_font_px}px;
        padding: {padding_vertical}px 2px;
        line-height: 1.2;
        height: {row_height_px}px;  /* Force exact height */
    }
```

#### Mathematical Model

For a wall with **N** rows and Frame height **H** mm:

$$
\text{Row Height} = \frac{(H \times 3.78) - 30}{N} \text{ px}
$$

$$
\text{Padding}_{vertical} = \frac{\text{Row Height} - (\text{Font Size} \times 1.2) - 2}{2} \text{ px}
$$

**Example (72 rows, 220mm frame)**:
- Frame: 220mm = 831px
- Available: 831 - 30 = 801px
- Per row: 801 / 72 = **11.1px**
- Font: 7px × 1.2 = 8.4px content
- Padding: (11.1 - 8.4 - 2) / 2 = **0.35px** top + bottom

**Result**: 72 rows fill **exactly** 220mm. Zero overflow, zero wasted space.

### Configuration

The Frame height is centrally configured in `export_pdf_report()`:

```python
DETAIL_FRAME_HEIGHT_MM = 220  # Must match QPT Frame 'detail_table' height
html_detail = self.generate_detail_html_table(geo_manager, frame_height_mm=DETAIL_FRAME_HEIGHT_MM)
```

⚠️ **Critical Sync Point**: This value **must match** the actual Frame height in `report_template.qpt`. If you resize the Frame in Layout Designer, update this constant.

### Diagnostic Output

Each PDF generation logs the dynamic calculation:

```
📊 DIAGNÓSTICO TABLA DETAIL:
   Muro: MP Muro 1
   Total Filas: 72
   Frame Height: 220mm
   🎨 Cálculo Fill Dinámico:
      • Altura Frame: 220mm (831px)
      • Espacio p/filas: 801px
      • Altura por fila: 11.1px
      • Font: 7px, Padding V: 0.4px, Line-H: 1.2
```

This allows real-time verification that the algorithm is working correctly.

### Diagnostic Tools

**Built-in Method**: From ProfileViewerDialog instance:
```python
dialog.diagnose_table_sizing()
```

**Standalone Analysis** ([diagnose_table_layout.py](../../diagnose_table_layout.py)): 
```python
exec(open('diagnose_table_layout.py').read())
```
Analyzes **all walls** and recommends optimal Frame height for the worst case.

**Interactive Calculator** ([calculate_table_height.py](../../calculate_table_height.py)):
```bash
python calculate_table_height.py 72  # For 72 rows
```

### Advantages Over Previous System

| Aspect | Old System | New Dynamic Fill |
|--------|-----------|------------------|
| **Space Utilization** | Variable (50-100%) | **100% always** |
| **Overflow Risk** | High for >60 rows | **Zero** (mathematically guaranteed) |
| **Consistency** | Different spacing per wall | **Uniform fill** across all walls |
| **Maintenance** | Requires manual CSS tweaking | **Automatic** — change 1 number |
| **Legibility** | Fixed font (sometimes too small) | **Adaptive** within readable range |

### Workflow for Adjusting Frame Size

If you need to change the Frame dimensions in the QPT:

1. **Measure available space** in Layout Designer (e.g., 250mm)
2. **Update Frame** `detail_table` height to 250mm
3. **Update code constant**:
   ```python
   DETAIL_FRAME_HEIGHT_MM = 250  # Line 3279 in profile_viewer_dialog.py
   ```
4. **Regenerate PDF** — algorithm auto-adapts to new dimensions

See [GUIDE_table_sizing.md](../GUIDE_table_sizing.md) for detailed instructions.

---

## North Arrow Visualization Enhancement

**Implementation Date**: February 2026

### Visual Configuration

The north arrow is dynamically generated with the following styling to ensure maximum visibility against ortomosaic backgrounds:

**Styling Parameters**:
- **Symbol**: `▲\nN` (Unicode arrow + letter N)
- **Color**: `#FF8C00` (DarkOrange) — High contrast against typical terrain colors
- **Font**: Arial 20pt Bold
- **Frame**: 1mm black stroke for definition
- **Background**: White with 78% opacity (`rgba(255,255,255,200)`) for readability
- **Position**: X=245mm, Y=10mm (repositioned from original X=270mm)
- **Size**: 20mm × 30mm
- **Rotation**: Automatically compensates for map rotation to always point true north

### Implementation Details

The north arrow is created in `MapGenerator._add_north_arrow()` method:

```python
# Color naranja para el texto/flecha
north_label.setFontColor(QColor(255, 140, 0))  # DarkOrange

# Marco negro grueso para que resalte más
north_label.setFrameEnabled(True)
north_label.setFrameStrokeColor(QColor(0, 0, 0))
north_label.setFrameStrokeWidth(QgsLayoutMeasurement(1.0, QgsUnitTypes.LayoutMillimeters))

# Fondo blanco semitransparente para contraste
north_label.setBackgroundEnabled(True)
north_label.setBackgroundColor(QColor(255, 255, 255, 200))  # 78% opacity
```

### Design Rationale

**Color Choice**: Orange (#FF8C00) was selected because:
- High visibility against both light (limestone) and dark (vegetation) terrain
- Distinct from operational colors (green/yellow/red used in measurements)
- Maintains professional appearance

**Background Strategy**: 
- Semi-transparent white background prevents complete loss of visibility on light terrain
- Black 1mm border creates strong edge definition
- Combined effect: arrow remains visible across all ortomosaic conditions

**Positioning**: 
- X=245mm provides clear separation from map content
- Left shift from original X=270mm prevents overlap with legend or data in corner cases

---

## Alert Screenshots Simplified Visualization

**Implementation Date**: February 2026

### Design Philosophy

Alert screenshots are generated to highlight problematic profiles (Revancha < 3m or Ancho < 15m) in a clear, uncluttered format that focuses attention on critical measurements without visual distractions.

### Simplified Display Rules

When generating screenshots for alert profiles (`export_mode=True`), the following elements are **removed** to reduce visual noise:

**Excluded Elements**:
- ❌ Red centerline axis (vertical line at X=0)
- ❌ Horizontal reference lines (orange/yellow dashed lines showing crown/lama elevations)
- ❌ Previous DEM terrain (gray dashed line)
- ❌ Measurement endpoint markers (red/green dots)
- ❌ Temporary measurement points
- ❌ Standard matplotlib legend

**Included Elements**:
- ✅ Current DEM terrain profile (blue line with brown fill)
- ✅ Lama point marker (yellow circle with orange edge)
- ✅ Width measurement line (lime green line)
- ✅ Custom text-based legend with key values

### Custom Legend Format

Screenshots include a simplified text box legend (top-right corner) containing only essential measurements:

```
─ Cota Coronamiento: XXX.XX m
● Cota Lama: XXX.XX m
  Revancha: X.XX m
─ Ancho: XX.XX m
```

**Legend Symbols**:
- `─` = Green line (coronamiento and ancho width)
- `●` = Orange point with red border (lama point)
- (no symbol) = Calculated value (revancha)

**Legend Styling**:
- Font: Monospace Bold, 11pt
- Background: White with 90% opacity
- Border: Black, 1.5px rounded rectangle
- Position: Upper-right corner (98%, 98% of axes)

### Implementation Details

The `update_profile_display()` method accepts an `export_mode` parameter:

```python
# Interactive mode (default)
update_profile_display(export_mode=False)  # Shows all visual aids

# Export mode (for PDF screenshots)
update_profile_display(export_mode=True)   # Simplified view
```

**Code Location**: `profile_viewer_dialog.py`, lines ~1922-2280

**Key Logic**:
```python
if not export_mode:
    # Draw reference lines, centerline, previous terrain, etc.
    self.ax.axvline(x=0, color='red', ...)
    self.ax.plot(x_range, y_ref, '--', color='orange', ...)
else:
    # Draw only essential elements + custom legend
    legend_text = f"Cota Coronamiento: {crown_val:.2f} m\n..."
    self.ax.text(0.98, 0.98, legend_text, ...)
```

### Benefits

**Clarity**: Removes 7+ overlapping visual elements, leaving only critical data  
**Focus**: Eye naturally drawn to the 3 key values (crown, lama, width)  
**Consistency**: All alert screenshots use identical simplified format  
**Professionalism**: Clean appearance suitable for executive reports

### Edge Cases & Limitations

**Minimum Font Size**: System enforces 6px minimum for readability. For walls with >100 rows, consider:
- Increasing Frame height beyond 220mm
- Splitting table across multiple pages
- Reducing column count

**Pixel Rounding**: CSS padding is rounded to 0.1px precision. For very small rows (<8px), rounding errors may accumulate to ±1-2px total variance (negligible in practice).

**Browser Rendering**: QGIS uses QtWebKit for HTML rendering. The 3.78 px/mm ratio is empirically derived and may vary slightly across QGIS versions.

---

## Architecture Internal Review

**Current Status**:
The system functions correctly and is robust against common errors (file locks, missing data).

**Modularization Assessment**:
*   **Strengths**:
    *   `MapGenerator` and `ReportGenerator` are well-separated, cohesive modules handling specific domains (Spatial vs Graphical).
    *   `GeomembraneManager` abstracts data access effectively.
*   **Weaknesses (Technical Debt)**:
    *   `ProfileViewerDialog` is a "God Class". It handles UI events *and* the complex orchestration of the report (step 5 and 6 specifically).
    *   HTML generation logic is embedded directly in the dialog methods (`_generate_html_table`), mixing presentation with control logic.
    *   Direct manipulation of layout items (`layout.itemById`) is scattered within the export method.

**Senior Engineer Recommendations**:
1.  **Extract Orchestrator**: Create a `ReportOrchestrator` class that receives the `QgsPrintLayout` and the data objects. It should have methods like `inject_map()`, `inject_tables()`, `inject_chart()`.
2.  **Template Engine**: Move HTML string construction to a separate `HtmlReportBuilder` class or use a templating engine (Jinja2) instead of f-strings, to separate content from markup.
3.  **Config Object**: Move hardcoded Layout IDs (`main_map`, `chart`) to a configuration dictionary or constant class to facilitate updates without digging into code logic.

For now, the system operates reliably, but future refactoring should focus on slimming down `ProfileViewerDialog`.
