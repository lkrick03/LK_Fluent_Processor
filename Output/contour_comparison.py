"""
Contour Comparison — Side-by-Side
=================================
Takes contour PNGs exported by `paraview_contour_exporter.py` from two
different simulations and stitches them side-by-side at matching Angles
of Attack, producing comparison images and optional animated GIFs.

Supports multiple directories per side with 'Highest Version Wins'
deduplication — when two directories share the same identity but differ
in version number, only the highest version's frames are kept.

Usage:
    Run with standard Python (NOT pvpython).
    python contour_comparison.py
"""

import os
import re
import glob
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# CONFIGURATION — MODIFY THIS SECTION
# ============================================================

# --- 1. Base Directories ---
# Each side can have multiple directories (different versions).
# 'Highest Version Wins' deduplication is applied per side.
BASE_DIRS_A = [
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.1.NG\Countour_Plots\ParaView",
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.2.NG\Countour_Plots\ParaView",
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.3.NG\Countour_Plots\ParaView",
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.4.NG\Countour_Plots\ParaView",
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.5.NG\Countour_Plots\ParaView",
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.6.NG\Countour_Plots\ParaView",
    #r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.7.NG\Countour_Plots\ParaView",
    #r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.8.NG\Countour_Plots\ParaView",
]
CONFIG_NAMES_A = []  # Leave empty to auto-extract from directory paths

BASE_DIRS_B = [
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.1.G\Countour_Plots\ParaView",
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.2.G\Countour_Plots\ParaView",
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.3.G\Countour_Plots\ParaView",
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.4.G\Countour_Plots\ParaView",
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.5.G\Countour_Plots\ParaView",
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.6.G\Countour_Plots\ParaView",
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.7.G\Countour_Plots\ParaView",
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.8.G\Countour_Plots\ParaView",
]
CONFIG_NAMES_B = []  # Leave empty to auto-extract from directory paths

# --- 2. Simulation Labels ---
# Human-readable names printed above each panel.
# When multiple dirs exist on a side, the highest-versioned config name is used automatically.
NAME_A = "5.6.1.NG"
NAME_B = "5.6.1.G"

# --- 3. Output ---
OUTPUT_DIR = r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Contour_Exports\Contour_Comparisons\5.6.1.NG_vs_5.6.1.G_12_20"

# --- 4. AoA Selection ---
# Provide a list of AoA values to compare.
# Leave empty [] to auto-discover all AoAs that exist in BOTH sides.
AOA_LIST = [12,12.5,13,13.5,14,14.5,15,15.5,16,16.5,17,17.5,18,18.5,19,19.5,20]

# --- 4b. GIF Settings ---
CREATE_GIFS = True                 # Set False to skip GIF creation
FRAME_DURATION = 500           # Milliseconds per frame (500 = 0.5s per AoA)

# --- 5. Appearance ---
PAPER_MODE = False          # True = omit titles (keeps whitespace + AR for paper inserts)
LABEL_FONT_SIZE = 36          # Font size for the simulation labels
SUBLABEL_FONT_SIZE = 30       # Font size for the config name + AoA line
LABEL_COLOR = (0, 0, 0)       # Black text
LABEL_BAR_HEIGHT = 100         # Pixels reserved for the two-line label bar
PADDING = 10                   # Pixels of padding around panels
BACKGROUND_COLOR = (255, 255, 255)  # White background

# --- 6. Family Description ---
# Maps numeric parts of the config name to descriptive values.
# Schema: velocity.mesh.turbulence.version.grid  (e.g. 5.6.1.1.NG)
# These must match the mappings in  Data Processing/config.py
VALUE_MAPPINGS = {
    'velocity': {4: '24.38 m/s', 5: '14.3773 m/s'},
    'mesh':     {1: 'OLD', 2: 'OLD', 3: 'Medium', 4: 'Adapted', 5: 'Unstructured', 6: 'Fine'},
    'turbulence': {1: 'K-Omega SST', 2: 'K-Epsilon Std', 3: 'RSM'},
    'grid':     {'NG': 'No Grid', 'G': 'With Grid'},
}

# ============================================================
# SCRIPT LOGIC
# ============================================================


def _extract_config_name(base_dir):
    """Extract config name (e.g. '5.6.1.1.NG') from a base directory path.
    Expects structure like .../5.6.1.1.NG/Countour_Plots/ParaView."""
    import os
    parts = os.path.normpath(base_dir).split(os.sep)
    # Walk backwards to find the first part matching the config pattern (digits+dots+optional G/NG)
    for part in reversed(parts):
        if re.match(r'^\d+\.\d+\.\d+\.\d+\.(G|NG)$', part):
            return part
    # Fallback: use the grandparent of the deepest directory
    if len(parts) >= 3:
        return parts[-3]
    return os.path.basename(base_dir)


def describe_config(name):
    """
    Parse a config name like '5.6.1.1.NG' into a descriptive string
    using VALUE_MAPPINGS.  Returns e.g. '14.3773 m/s, Fine, K-Omega SST, No Grid'.
    """
    parts = name.split('.')
    grid = None
    if parts and parts[-1] in ('G', 'NG'):
        grid = parts[-1]
        numeric_parts = parts[:-1]
    else:
        numeric_parts = parts

    def _get(field, raw):
        try:
            return VALUE_MAPPINGS.get(field, {}).get(int(raw), raw)
        except (ValueError, TypeError):
            return raw

    pieces = []
    if len(numeric_parts) > 0:
        vel_str = str(_get('velocity', numeric_parts[0]))
        # Truncate velocity to 3 significant figures
        vel_num = ''.join(c for c in vel_str if c.isdigit() or c == '.')
        vel_suffix = vel_str[len(vel_num):]  # e.g. ' m/s'
        try:
            vel_str = f"{float(vel_num):.3g}{vel_suffix}"
        except ValueError:
            pass
        pieces.append(vel_str)
    if len(numeric_parts) > 1:
        pieces.append(str(_get('mesh', numeric_parts[1])))
    if len(numeric_parts) > 2:
        pieces.append(str(_get('turbulence', numeric_parts[2])))
    if grid:
        pieces.append(str(VALUE_MAPPINGS.get('grid', {}).get(grid, grid)))
    return ', '.join(pieces)


def parse_identity_and_version(config_name):
    """
    Extract identity (everything except version) and version number.

    Schema: velocity.mesh.turbulence.version.grid  (e.g. 5.6.1.1.NG)
    Returns:
        (identity_tuple, version_number)
    """
    parts = config_name.split('.')
    grid = None
    numeric_parts = parts
    if parts[-1] in ('G', 'NG'):
        grid = parts[-1]
        numeric_parts = parts[:-1]

    velocity = numeric_parts[0] if len(numeric_parts) > 0 else '?'
    mesh     = numeric_parts[1] if len(numeric_parts) > 1 else '?'
    turb     = numeric_parts[2] if len(numeric_parts) > 2 else '?'

    try:
        version = int(numeric_parts[3]) if len(numeric_parts) > 3 else 0
    except ValueError:
        version = 0

    identity = (velocity, mesh, turb, grid)
    return identity, version


def collect_images_with_version_priority(base_dirs, config_names, aoa_list):
    """
    Scan multiple directories, apply 'Highest Version Wins' per (AoA, suffix),
    and return a deduplicated index.

    Returns:
        dict: { (aoa_str, suffix): filepath }
        str:  the config name of the winning (highest-versioned) entry
    """
    # Build per-key candidates: (aoa_str, suffix) -> [(version, path), ...]
    candidates = defaultdict(list)

    # Also track best config name
    best_config = config_names[0]
    best_version = 0

    for base_dir, config_name in zip(base_dirs, config_names):
        _, version = parse_identity_and_version(config_name)
        if version > best_version:
            best_version = version
            best_config = config_name

        for aoa in aoa_list:
            aoa_str = str(aoa) if isinstance(aoa, int) else f"{aoa}"
            aoa_folder = os.path.join(base_dir, f"AoA_{aoa_str}")
            if not os.path.isdir(aoa_folder):
                continue
            for png in glob.glob(os.path.join(aoa_folder, "*.png")):
                _, suffix = extract_suffix(os.path.basename(png))
                if suffix:
                    candidates[(aoa_str, suffix)].append((version, png))

    # Resolve: keep only highest version per key
    index = {}
    for key, entries in candidates.items():
        entries.sort(key=lambda x: x[0], reverse=True)
        index[key] = entries[0][1]  # path from highest version

    return index, best_config


def discover_shared_aoas_multi(dirs_a, dirs_b):
    """Find AoA values that have folders in at least one dir on BOTH sides."""
    aoa_pattern = re.compile(r'^AoA_(-?\d+\.?\d*)$')

    def _aoas_in_dirs(dirs):
        found = set()
        for directory in dirs:
            if not os.path.isdir(directory):
                continue
            for entry in os.listdir(directory):
                m = aoa_pattern.match(entry)
                if m:
                    val = float(m.group(1))
                    if val == int(val):
                        val = int(val)
                    found.add(val)
        return found

    aoas_a = _aoas_in_dirs(dirs_a)
    aoas_b = _aoas_in_dirs(dirs_b)
    return sorted(aoas_a & aoas_b, key=float)


def extract_suffix(filename):
    """
    Strip the config prefix from a contour filename and return the
    comparable suffix: everything after the first '_AoA_' segment.

    Example:
        '5.6.1.1.NG_AoA_10_Velocity_Magnitude_airfoil_center.png'
        -> ('10', 'Velocity_Magnitude_airfoil_center')
    """
    if "_AoA_" not in filename:
        return None, None
    parts = filename.split("_AoA_", 1)
    if len(parts) < 2:
        return None, None
    remainder = parts[1]
    subparts = remainder.split("_", 1)
    if len(subparts) < 2:
        return None, None
    aoa_str = subparts[0]
    suffix = subparts[1].replace(".png", "")
    return aoa_str, suffix


def get_font(size):
    """Try to load a nice TrueType font; fall back to the default bitmap font."""
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size)
        except OSError:
            return ImageFont.load_default()


def _center_crop(img, target_w, target_h):
    """Center-crop an image to target_w × target_h. Only crops, never upscales."""
    w, h = img.size
    crop_w = min(w, target_w)
    crop_h = min(h, target_h)
    left = (w - crop_w) // 2
    top = (h - crop_h) // 2
    return img.crop((left, top, left + crop_w, top + crop_h))


def create_comparison(path_a, path_b, name_a, name_b, aoa_str, output_path):
    """Stitch two images side-by-side with a two-line label bar at the top.
    The final canvas is forced to 16:9 by center-cropping the input images."""
    img_a = Image.open(path_a)
    img_b = Image.open(path_b)

    # Use a fixed panel height so ALL comparison outputs have identical
    # canvas dimensions — this prevents GIF bouncing when source images
    # vary slightly in size across AoAs (e.g. trailing edge zoom).
    panel_h = 1080

    # In paper mode, skip the label bar space above the panels
    label_bar = 0 if PAPER_MODE else LABEL_BAR_HEIGHT

    # Compute the panel width that makes the final canvas exactly 16:9
    total_h = label_bar + 2 * PADDING + panel_h
    panel_w = int((total_h * 16 / 9 - 3 * PADDING) / 2)

    # Resize inputs to fit the panel slot (maintain aspect ratio, then center-crop)
    img_a = _center_crop(img_a, panel_w, panel_h)
    img_b = _center_crop(img_b, panel_w, panel_h)

    total_w = PADDING + panel_w + PADDING + panel_w + PADDING
    canvas = Image.new("RGB", (total_w, total_h), BACKGROUND_COLOR)

    # Paste panels (centered if an image was smaller than the panel slot)
    x_a = PADDING + (panel_w - img_a.width) // 2
    y_a = label_bar + PADDING + (panel_h - img_a.height) // 2
    canvas.paste(img_a, (x_a, y_a))

    x_b = PADDING + panel_w + PADDING + (panel_w - img_b.width) // 2
    y_b = label_bar + PADDING + (panel_h - img_b.height) // 2
    canvas.paste(img_b, (x_b, y_b))

    # Draw two-line labels (skip in paper mode)
    if not PAPER_MODE:
        draw = ImageDraw.Draw(canvas)
        font_main = get_font(LABEL_FONT_SIZE)
        font_sub = get_font(SUBLABEL_FONT_SIZE)

        def _draw_centered(text, font, center_x, y):
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            draw.text((center_x - tw // 2, y), text, fill=LABEL_COLOR, font=font)

        # Line 1: descriptive family (velocity, mesh, turbulence, grid)
        # Line 2: config name + AoA
        desc_a = describe_config(name_a)
        desc_b = describe_config(name_b)
        line1_y = 6
        line2_y = 6 + LABEL_FONT_SIZE + 4

        center_a = PADDING + panel_w // 2
        center_b = PADDING + panel_w + PADDING + panel_w // 2

        _draw_centered(desc_a, font_main, center_a, line1_y)
        _draw_centered(f"{name_a} — AoA {aoa_str}°", font_sub, center_a, line2_y)

        _draw_centered(desc_b, font_main, center_b, line1_y)
        _draw_centered(f"{name_b} — AoA {aoa_str}°", font_sub, center_b, line2_y)

    canvas.save(output_path)
    return output_path


def main():
    print("=" * 60)
    print("Contour Comparison — Side-by-Side")
    print("=" * 60)

    # Auto-derive CONFIG_NAMES if not provided
    config_names_a = CONFIG_NAMES_A if CONFIG_NAMES_A else [_extract_config_name(d) for d in BASE_DIRS_A]
    config_names_b = CONFIG_NAMES_B if CONFIG_NAMES_B else [_extract_config_name(d) for d in BASE_DIRS_B]

    # Print source directories
    print(f"\nSide A ({len(BASE_DIRS_A)} directories):")
    for i, (d, c) in enumerate(zip(BASE_DIRS_A, config_names_a)):
        print(f"  [{i+1}] {c} -> {d}")
    print(f"\nSide B ({len(BASE_DIRS_B)} directories):")
    for i, (d, c) in enumerate(zip(BASE_DIRS_B, config_names_b)):
        print(f"  [{i+1}] {c} -> {d}")

    # Determine AoA list
    aoa_list = AOA_LIST
    if not aoa_list:
        print("\nAOA_LIST is empty — auto-discovering shared AoAs...")
        aoa_list = discover_shared_aoas_multi(BASE_DIRS_A, BASE_DIRS_B)
        if not aoa_list:
            print("[WARNING] No shared AoA folders found between the two sides.")
            return
    print(f"AoAs to compare: {aoa_list}")

    # Collect images with version priority
    print("\nApplying 'Highest Version Wins' frame selection...")
    index_a, best_config_a = collect_images_with_version_priority(BASE_DIRS_A, config_names_a, aoa_list)
    index_b, best_config_b = collect_images_with_version_priority(BASE_DIRS_B, config_names_b, aoa_list)

    # Use the config names for labels (override NAME_A/B with best version)
    label_a = NAME_A
    label_b = NAME_B

    # Find matching pairs (same aoa + suffix in both)
    shared_keys = sorted(set(index_a.keys()) & set(index_b.keys()))

    if not shared_keys:
        print("[WARNING] No matching contour pairs found between the two sides.")
        print(f"  Side A has {len(index_a)} images, Side B has {len(index_b)} images.")
        return

    print(f"\nFound {len(shared_keys)} matching contour pairs.")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate comparison images and track them for GIF creation
    created = 0
    gif_groups = defaultdict(list)  # suffix -> [(aoa_float, path), ...]

    for aoa_str, suffix in shared_keys:
        # Group by variable/view type, not by AoA
        suffix_dir = os.path.join(OUTPUT_DIR, suffix)
        os.makedirs(suffix_dir, exist_ok=True)
        out_name = f"Comparison_AoA_{aoa_str}_{suffix}.png"
        out_path = os.path.join(suffix_dir, out_name)

        print(f"  -> AoA {aoa_str:>5s} | {suffix}")
        create_comparison(
            index_a[(aoa_str, suffix)],
            index_b[(aoa_str, suffix)],
            label_a,
            label_b,
            aoa_str,
            out_path,
        )
        created += 1
        gif_groups[suffix].append((float(aoa_str), out_path))

    print(f"\n{'=' * 60}")
    print(f"[OK] Created {created} comparison images.")
    print(f"Location: {OUTPUT_DIR}")

    # --- GIF Creation ---
    if CREATE_GIFS and gif_groups:
        print(f"\nCreating animated GIFs ({FRAME_DURATION}ms per frame)...")
        gif_dir = os.path.join(OUTPUT_DIR, "GIFs")
        os.makedirs(gif_dir, exist_ok=True)
        gifs_created = 0

        for suffix, frame_list in sorted(gif_groups.items()):
            # Sort frames by AoA (low → high)
            frame_list.sort(key=lambda x: x[0])

            frames = []
            target_size = None
            for _, path in frame_list:
                img = Image.open(path)
                if target_size is None:
                    target_size = img.size
                elif img.size != target_size:
                    img = img.resize(target_size, Image.LANCZOS)
                frames.append(img)
            if not frames:
                continue

            gif_name = f"{label_a}_vs_{label_b}_{suffix}.gif"
            gif_path = os.path.join(gif_dir, gif_name)

            frames[0].save(
                gif_path,
                save_all=True,
                append_images=frames[1:],
                duration=FRAME_DURATION,
                loop=0,  # Loop forever
            )
            aoa_range = [x[0] for x in frame_list]
            print(f"  -> {suffix}  ({len(frames)} frames, AoA {aoa_range[0]}–{aoa_range[-1]})")
            gifs_created += 1

        print(f"\n[OK] Created {gifs_created} animated GIFs.")
        print(f"Location: {gif_dir}")


if __name__ == "__main__":
    main()
