"""
STAAD.Pro Procurement API
FastAPI-based REST API for parsing .STD files and generating procurement data.
"""

import io
import os
import sys
import uuid
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Make sure src/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from staad_parser import parse_std_file, G
from excel_writer import generate_excel

# ── App setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="STAAD.Pro Procurement API",
    description=(
        "Upload a STAAD.Pro .STD file to extract member properties, "
        "calculate plate weights, and download a procurement Excel report."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temp directory to store generated files
TEMP_DIR = Path(tempfile.gettempdir()) / "staad_api_outputs"
TEMP_DIR.mkdir(exist_ok=True)


# ── Helper ────────────────────────────────────────────────────────────────────
def _parse_upload(file: UploadFile) -> tuple:
    """Save upload to a temp file, parse it, return (plate_records, pipe_records, stem, tmp_path)."""
    if not file.filename.upper().endswith(".STD"):
        raise HTTPException(status_code=400, detail="Only .STD files are accepted.")

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    tmp_path = TEMP_DIR / f"{uuid.uuid4().hex}_{file.filename}"
    tmp_path.write_bytes(content)

    try:
        plate_records, pipe_records, stem = parse_std_file(str(tmp_path))
    except Exception as e:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Failed to parse STD file: {e}")

    return plate_records, pipe_records, stem, tmp_path


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """Health check — confirm the API is running."""
    return {
        "status": "ok",
        "message": "STAAD.Pro Procurement API is running.",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


# ─────────────────────────────────────────────────────────────────────────────
# POST /parse  →  returns JSON summary + all member records
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/parse", tags=["Procurement"])
async def parse_std(file: UploadFile = File(..., description="STAAD.Pro .STD file")):
    """
    Parse a STAAD.Pro .STD file and return procurement data as JSON.

    **Response includes:**
    - `summary`  — totals grouped by plate thickness
    - `records`  — every member × plate combination with weight
    - `stats`    — overall totals
    """
    plate_records, pipe_records, stem, tmp_path = _parse_upload(file)
    tmp_path.unlink(missing_ok=True)

    if not plate_records and not pipe_records:
        raise HTTPException(status_code=422, detail="No plate/member data found in STD file.")

    # ── Build thickness-wise summary (plates only) ──
    from collections import defaultdict
    by_thk: dict = defaultdict(lambda: {
        "thickness_mm": 0,
        "plate_count": 0,
        "member_count": 0,
        "members": set(),
        "total_area_m2": 0.0,
        "total_weight_kg": 0.0,
    })

    for r in plate_records:
        thk = r["Thickness (mm)"]
        by_thk[thk]["thickness_mm"]    = thk
        by_thk[thk]["plate_count"]     += 1
        by_thk[thk]["members"].add(r["Member ID"])
        by_thk[thk]["total_area_m2"]   += r["Area (m²)"]
        by_thk[thk]["total_weight_kg"] += r["Weight (kg)"]

    summary = []
    for thk in sorted(by_thk):
        d = by_thk[thk]
        count = d["plate_count"]
        wt    = round(d["total_weight_kg"], 2)
        summary.append({
            "thickness_mm":       thk,
            "plate_count":        count,
            "member_count":       len(d["members"]),
            "wt_per_plate_kg":    round(wt / count, 2) if count else 0,
            "total_area_m2":      round(d["total_area_m2"], 3),
            "total_weight_kg":    wt,
            "total_weight_ton":   round(wt / 1000, 3),
            "grade":              "IS 2062 E250",
        })

    total_wt   = round(sum(r["Weight (kg)"] for r in plate_records), 2)
    total_area = round(sum(r["Area (m²)"] for r in plate_records), 3)
    total_kn   = round(total_wt * G / 1000, 3)   # kg → kN (STAAD default unit)

    # ── Pipe aggregates ──
    pipe_total_wt = round(sum(r["Weight (kg)"] for r in pipe_records), 2)
    pipe_total_len = round(sum(r["Length (m)"] for r in pipe_records), 3)
    pipe_total_area = round(sum(r["Surface Area (m²)"] for r in pipe_records), 3)
    pipe_members = sorted({r["Member ID"] for r in pipe_records})

    # Group pipes by (OD, wall thickness) — useful summary
    pipe_groups: dict = defaultdict(lambda: {
        "count": 0,
        "total_length_m": 0.0,
        "total_weight_kg": 0.0,
        "members": set(),
    })
    for r in pipe_records:
        key = (r["OD (mm)"], r["Wall Thickness (mm)"])
        pipe_groups[key]["count"]            += 1
        pipe_groups[key]["total_length_m"]   += r["Length (m)"]
        pipe_groups[key]["total_weight_kg"]  += r["Weight (kg)"]
        pipe_groups[key]["members"].add(r["Member ID"])

    pipe_summary = [
        {
            "od_mm":             od,
            "wall_thickness_mm": wt,
            "count":             d["count"],
            "member_count":      len(d["members"]),
            "total_length_m":    round(d["total_length_m"], 3),
            "total_weight_kg":   round(d["total_weight_kg"], 2),
            "total_weight_ton":  round(d["total_weight_kg"] / 1000, 3),
        }
        for (od, wt), d in sorted(pipe_groups.items())
    ]

    return JSONResponse({
        "filename": stem,
        "stats": {
            "total_members":    len(set(r["Member ID"] for r in plate_records)),
            "total_records":    len(plate_records),
            "thicknesses_mm":   sorted(set(r["Thickness (mm)"] for r in plate_records)),
            "total_area_m2":    total_area,
            "total_weight_kg":  total_wt,
            "total_weight_ton": round(total_wt / 1000, 3),
            "total_weight_kn":  total_kn,
        },
        "summary": summary,
        "records": [
            {
                "member_id":      r["Member ID"],
                "part":           r["Part"],
                "thickness_mm":   r["Thickness (mm)"],
                "width_m":        r["Width (m)"],
                "length_m":       r["Length (m)"],
                "area_m2":        r["Area (m²)"],
                "weight_kg":      r["Weight (kg)"],
            }
            for r in plate_records
        ],
        "part_breakup": [
            {
                "part":           p,
                "thickness_mm":   t,
                "count":          sum(1 for r in plate_records if r["Part"] == p and r["Thickness (mm)"] == t),
                "total_area_m2":  round(sum(r["Area (m²)"] for r in plate_records if r["Part"] == p and r["Thickness (mm)"] == t), 3),
                "total_weight_kg": round(sum(r["Weight (kg)"] for r in plate_records if r["Part"] == p and r["Thickness (mm)"] == t), 2)
            }
            for p, t in sorted(set((r["Part"], r["Thickness (mm)"]) for r in plate_records))
        ],
        "pipe_stats": {
            "total_pipes":        len(pipe_records),
            "total_members":      len(pipe_members),
            "total_length_m":     pipe_total_len,
            "total_surface_m2":   pipe_total_area,
            "total_weight_kg":    pipe_total_wt,
            "total_weight_ton":   round(pipe_total_wt / 1000, 3),
            "total_weight_kn":    round(pipe_total_wt * G / 1000, 3),
        },
        "pipe_summary": pipe_summary,
        "pipes": [
            {
                "member_id":           r["Member ID"],
                "od_mm":               r["OD (mm)"],
                "wall_thickness_mm":   r["Wall Thickness (mm)"],
                "length_m":            r["Length (m)"],
                "surface_area_m2":     r["Surface Area (m²)"],
                "weight_kg":           r["Weight (kg)"],
            }
            for r in pipe_records
        ],
    })


# ─────────────────────────────────────────────────────────────────────────────
# POST /download  →  returns Excel file
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/download", tags=["Procurement"])
async def download_excel(file: UploadFile = File(..., description="STAAD.Pro .STD file")):
    """
    Parse a STAAD.Pro .STD file and return a **downloadable Excel** procurement report.

    The Excel file contains three sheets:
    1. **Procurement Summary** — grouped by plate thickness
    2. **Member Detail**       — every member × part
    3. **Part-wise Breakup**   — grouped by part type
    """
    plate_records, pipe_records, stem, tmp_path = _parse_upload(file)
    tmp_path.unlink(missing_ok=True)

    if not plate_records and not pipe_records:
        raise HTTPException(status_code=422, detail="No plate/member data found in STD file.")

    out_path = TEMP_DIR / f"{uuid.uuid4().hex}_{stem}_Procurement.xlsx"
    generate_excel(plate_records, stem, str(out_path), pipe_records=pipe_records)

    return FileResponse(
        path=str(out_path),
        filename=f"{stem}_Procurement.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /summary  →  returns only the thickness-wise summary (lightweight)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/summary", tags=["Procurement"])
async def get_summary(file: UploadFile = File(..., description="STAAD.Pro .STD file")):
    """
    Lightweight endpoint — returns **only** the thickness-wise summary table
    (no full record list). Ideal for dashboard cards / frontend tables.
    """
    plate_records, pipe_records, stem, tmp_path = _parse_upload(file)
    tmp_path.unlink(missing_ok=True)

    if not plate_records and not pipe_records:
        raise HTTPException(status_code=422, detail="No plate/member data found in STD file.")

    from collections import defaultdict
    by_thk: dict = defaultdict(lambda: {
        "plate_count": 0, "members": set(),
        "total_area_m2": 0.0, "total_weight_kg": 0.0,
    })

    for r in plate_records:
        thk = r["Thickness (mm)"]
        by_thk[thk]["plate_count"]     += 1
        by_thk[thk]["members"].add(r["Member ID"])
        by_thk[thk]["total_area_m2"]   += r["Area (m²)"]
        by_thk[thk]["total_weight_kg"] += r["Weight (kg)"]

    summary = []
    for thk in sorted(by_thk):
        d     = by_thk[thk]
        count = d["plate_count"]
        wt    = round(d["total_weight_kg"], 2)
        summary.append({
            "thickness_mm":     thk,
            "plate_count":      count,
            "member_count":     len(d["members"]),
            "wt_per_plate_kg":  round(wt / count, 2) if count else 0,
            "total_area_m2":    round(d["total_area_m2"], 3),
            "total_weight_kg":  wt,
            "total_weight_ton": round(wt / 1000, 3),
            "grade":            "IS 2062 E250",
        })

    total_wt      = round(sum(r["Weight (kg)"] for r in plate_records), 2)
    pipe_total_wt = round(sum(r["Weight (kg)"] for r in pipe_records), 2)

    return JSONResponse({
        "filename":         stem,
        "total_weight_kg":  total_wt,
        "total_weight_ton": round(total_wt / 1000, 3),
        "total_weight_kn":  round(total_wt * G / 1000, 3),
        "pipe_total_weight_kg":  pipe_total_wt,
        "pipe_total_weight_ton": round(pipe_total_wt / 1000, 3),
        "summary":          summary,
    })


# ─────────────────────────────────────────────────────────────────────────────
# POST /members  →  returns per-member breakdown filtered by thickness
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/members", tags=["Procurement"])
async def get_members(
    file: UploadFile = File(...),
    thickness_mm: Optional[float] = Query(None, description="Filter by plate thickness (mm)"),
    part: Optional[str] = Query(None, description="Filter by part name e.g. Web, Top Flange"),
):
    """
    Returns per-member records.
    Optionally filter by **thickness_mm** and/or **part** name.
    """
    plate_records, _pipe_records, stem, tmp_path = _parse_upload(file)
    tmp_path.unlink(missing_ok=True)

    if not plate_records:
        raise HTTPException(status_code=422, detail="No plate/member data found in STD file.")

    filtered = plate_records
    if thickness_mm is not None:
        filtered = [r for r in filtered if r["Thickness (mm)"] == thickness_mm]
    if part:
        filtered = [r for r in filtered if part.lower() in r["Part"].lower()]

    return JSONResponse({
        "filename":      stem,
        "filter":        {"thickness_mm": thickness_mm, "part": part},
        "total_records": len(filtered),
        "records": [
            {
                "member_id":    r["Member ID"],
                "part":         r["Part"],
                "thickness_mm": r["Thickness (mm)"],
                "width_m":      r["Width (m)"],
                "length_m":     r["Length (m)"],
                "area_m2":      r["Area (m²)"],
                "weight_kg":    r["Weight (kg)"],
            }
            for r in filtered
        ],
    })
