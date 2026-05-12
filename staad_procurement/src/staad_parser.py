"""
STAAD.Pro STD File Parser
Extracts all plate/section data and calculates material procurement
"""

import re
import math
from pathlib import Path


STEEL_DENSITY = 7833.41  # kg/m3 (STAAD.Pro default is ~7833.41 kg/m3 or 490 lb/ft3)
G = 9.80665              # m/s² — for kg → Newton conversion


def parse_joints(lines):
    """Extract joint coordinates {joint_id: (x, y, z)}"""
    joints = {}
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("JOINT COORDINATES"):
            in_section = True
            continue
        if in_section:
            if re.match(r'^[A-Z]', stripped) and not re.match(r'^\d', stripped):
                break
            # Handle semicolon-separated entries on one line
            entries = stripped.split(";")
            for entry in entries:
                entry = entry.strip()
                parts = entry.split()
                if len(parts) >= 4:
                    try:
                        jid = int(parts[0])
                        x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                        joints[jid] = (x, y, z)
                    except ValueError:
                        continue
    return joints


def parse_member_incidences(lines):
    """Extract member connectivity {member_id: (start_joint, end_joint)}"""
    members = {}
    in_section = False
    full_text = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("MEMBER INCIDENCES"):
            in_section = True
            continue
        if in_section:
            if re.match(r'^[A-Z]', stripped) and not re.match(r'^\d', stripped):
                break
            full_text += " " + stripped.rstrip("-").strip()

    entries = full_text.split(";")
    for entry in entries:
        parts = entry.strip().split()
        if len(parts) >= 3:
            try:
                mid = int(parts[0])
                s, e = int(parts[1]), int(parts[2])
                members[mid] = (s, e)
            except ValueError:
                continue
    return members


def member_length(mid, members, joints):
    """Calculate length of a member in meters"""
    if mid not in members:
        return None
    s, e = members[mid]
    if s not in joints or e not in joints:
        return None
    x1, y1, z1 = joints[s]
    x2, y2, z2 = joints[e]
    return math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)


def expand_member_list(tokens):
    """Expand STAAD member list with TO ranges into list of ints"""
    result = []
    i = 0
    while i < len(tokens):
        try:
            val = int(tokens[i])
            if i + 2 < len(tokens) and tokens[i+1].upper() == "TO":
                end = int(tokens[i+2])
                result.extend(range(val, end+1))
                i += 3
            else:
                result.append(val)
                i += 1
        except ValueError:
            i += 1
    return result


def parse_member_properties(lines):
    """
    Parse all MEMBER PROPERTY sections (AMERICAN, TATASTRUCTURA, etc.).
    Returns list of dicts:
      {
        'members': [list of member ids],
        'type': 'TAPERED' | 'PRIS' | 'ROUND' | 'OTHER',
        'params': [...raw float params...],
        'raw': 'original line'
      }
    """
    props = []
    # Join continuation lines (ending with -)
    joined = []
    current = ""
    for line in lines:
        stripped = line.strip()
        if stripped.endswith("-"):
            current += " " + stripped[:-1]
        else:
            current += " " + stripped
            joined.append(current.strip())
            current = ""
    if current.strip():
        joined.append(current.strip())

    # Non-property major keywords that end a MEMBER PROPERTY section
    STOP_KEYWORDS = re.compile(
        r'^(DEFINE|CONSTANTS|SUPPORTS|MEMBER RELEASE|MEMBER TENSION|MEMBER TRUSS|'
        r'LOAD|PERFORM|FINISH|STEEL|CHECK|UNIT|JOINT LOAD|ELEMENT LOAD|'
        r'FLOOR LOAD|WIND LOAD|SELFWEIGHT)',
        re.IGNORECASE
    )
    MEMBER_PROP = re.compile(r'^MEMBER PROPERTY', re.IGNORECASE)

    # Map member_id -> property dict to ensure only the LAST property is kept
    # This reflects STAAD's behavior where subsequent assignments override previous ones.
    member_to_prop = {}

    in_section = False
    i = 0
    while i < len(joined):
        line = joined[i]

        if MEMBER_PROP.match(line):
            in_section = True
            i += 1
            continue

        if in_section:
            if STOP_KEYWORDS.match(line):
                in_section = False
                # Don't skip — let outer loop re-evaluate
                continue

            tokens = line.split()
            if not tokens:
                i += 1
                continue

            # Find first type keyword — handle "PRIS ROUND" as ROUND
            TYPE_KW = ["TAPERED", "PRIS", "PRISMATIC", "TABLE", "ROUND", "PIPE", "YD", "ZD"]
            type_idx = None
            prop_type = "OTHER"
            for j, t in enumerate(tokens):
                if t.upper() in TYPE_KW:
                    type_idx = j
                    prop_type = t.upper()
                    # If "PRIS" followed by "ROUND", treat whole thing as ROUND
                    if t.upper() == "PRIS" and j + 1 < len(tokens) and tokens[j+1].upper() == "ROUND":
                        prop_type = "ROUND"
                        type_idx = j
                    break

            if type_idx is None:
                i += 1
                continue

            member_tokens = tokens[:type_idx]
            member_ids = expand_member_list(member_tokens)

            params = []
            for p in tokens[type_idx + 1:]:
                try:
                    params.append(float(p))
                except ValueError:
                    break

            if member_ids:
                prop_data = {
                    'type': prop_type,
                    'params': params,
                    'raw': line
                }
                for mid in member_ids:
                    member_to_prop[mid] = prop_data

        i += 1

    # Group members back by property for efficient processing
    unique_props = []
    prop_groups = {}
    for mid, data in member_to_prop.items():
        key = (data['type'], tuple(data['params']), data['raw'])
        if key not in prop_groups:
            prop_groups[key] = {**data, 'members': []}
        prop_groups[key]['members'].append(mid)

    return list(prop_groups.values())


def extract_plate_info(prop):
    """
    Extract plate/section info matching STAAD.Pro selfweight calculation.

    STAAD TAPERED selfweight formula (per docs TR.32.9.1):
      Weight = (Web_area + TopFlange_area + BotFlange_area) × Length × Density
      Where:
        Web_area       = D_avg × tw          (FULL depth — flanges are NOT subtracted)
        TopFlange_area = bf_top × tf_top
        BotFlange_area = bf_bot × tf_bot

    STAAD PRIS ROUND selfweight formula:
      Weight = π/4 × (OD² - ID²) × Length × Density
      ID = OD - 2 × THI

    Returns list of plate dicts:
      { part, thickness_m, width_m, is_web, area_override (optional) }
    """
    plates = []

    if prop['type'] == 'TAPERED':
        p = prop['params']
        if len(p) >= 5:
            D_start = p[0]   # m — total depth at start node
            tw      = p[1]   # m — web thickness
            D_end   = p[2]   # m — total depth at end node
            bf_top  = p[3]   # m — top flange width
            tf_top  = p[4]   # m — top flange thickness
            # Bottom flange (optional — defaults to same as top if not given)
            bf_bot  = p[5] if len(p) >= 6 else bf_top
            tf_bot  = p[6] if len(p) >= 7 else tf_top

            # STAAD uses average depth for tapered member web
            D_avg = (D_start + D_end) / 2

            # Web: CLEAR depth (D_avg - tf_top - tf_bot)
            # This matches STAAD Steel Take-off calculation for built-up sections
            # to avoid double-counting the flange-web intersection area.
            web_depth = D_avg - tf_top - tf_bot
            if web_depth < 0: web_depth = 0

            plates.append({
                'part': 'Web',
                'thickness_m': tw,
                'width_m': web_depth,
                'is_web': True
            })
            # Top flange
            plates.append({
                'part': 'Top Flange',
                'thickness_m': tf_top,
                'width_m': bf_top,
                'is_web': False
            })
            # Bottom flange
            plates.append({
                'part': 'Bot Flange',
                'thickness_m': tf_bot,
                'width_m': bf_bot,
                'is_web': False
            })

    elif prop['type'] in ('PRIS', 'PRISMATIC'):
        # PRIS YD <depth> [ZD <width>]  — solid rectangular section
        raw = prop['raw']
        p   = prop['params']
        yd_m = re.search(r'YD\s+([\d.eE+\-]+)', raw, re.IGNORECASE)
        zd_m = re.search(r'ZD\s+([\d.eE+\-]+)', raw, re.IGNORECASE)
        if yd_m:
            yd = float(yd_m.group(1))
            zd = float(zd_m.group(1)) if zd_m else yd
            plates.append({'part': 'Plate', 'thickness_m': yd, 'width_m': zd, 'is_web': False})
        elif len(p) >= 1:
            plates.append({'part': 'Plate', 'thickness_m': p[0],
                           'width_m': p[1] if len(p) > 1 else p[0], 'is_web': False})

    elif prop['type'] == 'PIPE':
        # "PIPE OD <outer_dia> ID <inner_dia>"  — STAAD direct pipe property
        # Hollow circular section. Weight = π/4 × (OD² - ID²) × L × ρ
        raw   = prop['raw']
        od_m  = re.search(r'OD\s+([\d.eE+\-]+)', raw, re.IGNORECASE)
        id_m  = re.search(r'\bID\s+([\d.eE+\-]+)', raw, re.IGNORECASE)
        if od_m and id_m:
            od  = float(od_m.group(1))      # outer diameter (m)
            id_ = float(id_m.group(1))      # inner diameter (m)
            thk = (od - id_) / 2.0          # wall thickness (m)
            if thk < 0: thk = 0
            cross_area = math.pi / 4 * (od**2 - id_**2)   # m²
            plates.append({
                'part': 'Pipe',
                'thickness_m': thk,
                'width_m': od,
                'is_web': False,
                'area_override': cross_area,
            })

    elif prop['type'] == 'ROUND':
        # "PRIS ROUND STA <OD> END <OD> THI <wall_thk>" — hollow circular pipe
        # STAAD selfweight: W = π/4 × (OD² - ID²) × L × ρ
        # Store as area_override so build_procurement uses it directly
        raw   = prop['raw']
        thk_m = re.search(r'THI\s+([\d.eE+\-]+)', raw, re.IGNORECASE)
        sta_m = re.search(r'STA\s+([\d.eE+\-]+)', raw, re.IGNORECASE)
        if thk_m and sta_m:
            thk = float(thk_m.group(1))   # wall thickness (m)
            od  = float(sta_m.group(1))   # outer diameter (m)
            id_ = od - 2 * thk            # inner diameter (m)
            cross_area = math.pi / 4 * (od**2 - id_**2)   # m²
            plates.append({
                'part': 'Pipe/Round',
                'thickness_m': thk,
                'width_m': od,
                'is_web': False,
                'area_override': cross_area   # use this directly for weight calc
            })
        elif thk_m:
            thk = float(thk_m.group(1))
            plates.append({'part': 'Pipe/Round', 'thickness_m': thk,
                           'width_m': thk, 'is_web': False})

    return plates


def build_procurement(props, members, joints):
    """
    Build procurement records per member.
    Weight = cross_section_area × length × density  (matches STAAD selfweight)

    Returns (plate_records, pipe_records):
      - plate_records: rectangular plate parts (Web / Top Flange / Bot Flange / Plate)
      - pipe_records:  hollow circular sections (PRIS ROUND), reported with
                       outer_diameter / wall_thickness / length / weight only.
    """
    plate_records = []
    pipe_records  = []

    for prop in props:
        plates = extract_plate_info(prop)
        if not plates:
            continue
        for mid in prop['members']:
            length = member_length(mid, members, joints)
            if length is None:
                length = 0.0
            for plate in plates:
                thk_mm  = round(plate['thickness_m'] * 1000, 2)
                width_m = plate['width_m']

                if 'area_override' in plate:
                    # Hollow pipe — store as a pipe record, not a plate
                    cross_area_m2 = plate['area_override']
                    volume_m3     = cross_area_m2 * length
                    weight_kg     = volume_m3 * STEEL_DENSITY
                    od_mm         = round(width_m * 1000, 2)            # outer diameter (mm)
                    surface_area  = math.pi * width_m * length            # π × OD × L (m²)

                    pipe_records.append({
                        'Member ID':           mid,
                        'OD (mm)':             od_mm,
                        'Wall Thickness (mm)': thk_mm,
                        'Length (m)':          round(length, 3),
                        'Surface Area (m²)':   round(surface_area, 4),
                        'Weight (kg)':         round(weight_kg, 2),
                    })
                else:
                    cross_area_m2 = plate['thickness_m'] * width_m
                    area_m2       = length * width_m                      # surface area (L × width)
                    volume_m3     = cross_area_m2 * length
                    weight_kg     = volume_m3 * STEEL_DENSITY

                    plate_records.append({
                        'Member ID':        mid,
                        'Part':             plate['part'],
                        'Thickness (mm)':   thk_mm,
                        'Width (m)':        round(width_m, 4),
                        'Length (m)':       round(length, 3),
                        'Area (m²)':        round(area_m2, 4),
                        'Weight (kg)':      round(weight_kg, 2),
                    })

    return plate_records, pipe_records


def parse_std_file(filepath):
    """Full parse pipeline. Returns (plate_records, pipe_records, filename)"""
    path = Path(filepath)
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    joints  = parse_joints(lines)
    members = parse_member_incidences(lines)
    props   = parse_member_properties(lines)
    plate_records, pipe_records = build_procurement(props, members, joints)
    return plate_records, pipe_records, path.stem
