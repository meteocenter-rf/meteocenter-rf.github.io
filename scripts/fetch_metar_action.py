#!/usr/bin/env python3
"""
Fetches live METAR observations for major WMO/ICAO stations across Russia & CIS
and writes normalized JSON to data/metar_fact.json.

Primary source: aviationweather.gov Data API
Fallback source (per missing station): metar.vatsim.net
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ICAO_LIST = [
    "UUEE", "UUWW", "UUDD", "ULLI", "UOOO", "UUOO", "URSS", "URKK", "URRP",
    "USSS", "UNNT", "UWKD", "UWGG", "UWWW", "UWUU", "UEEE", "ULMM", "UHWW",
    "UHHH", "UNKL", "UIII", "USTR", "USCC", "UMMS", "UAAA", "UACC",
]

HEADERS = {
    "User-Agent": "MeteoPortal-RF/2.0 (https://meteocenter-rf.github.io)",
    "Accept": "application/json, text/plain, */*",
}


def normalize_aw_item(item: dict) -> dict | None:
    icao = item.get("icaoId") or item.get("icao")
    if not icao:
        return None
    normalized = dict(item)
    normalized["icaoId"] = icao
    normalized["icao"] = icao
    if item.get("dewp") is not None and normalized.get("dew_point") is None:
        normalized["dew_point"] = item["dewp"]
    if item.get("wdir") is not None and normalized.get("wind_dir") is None:
        normalized["wind_dir"] = item["wdir"]
    if (item.get("reportTime") or item.get("time")) and not normalized.get("time"):
        normalized["time"] = item.get("reportTime") or item.get("time")
    return normalized


def fetch_aviationweather(icaos: list[str]) -> dict[str, dict]:
    ids = ",".join(icaos)
    url = f"https://aviationweather.gov/api/data/metar?ids={urllib.parse.quote(ids)}&format=json"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    out: dict[str, dict] = {}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                norm = normalize_aw_item(item)
                if norm:
                    out[norm["icao"]] = norm
    return out


def _metar_signed_temp(token: str) -> int:
    return -int(token[1:]) if token.startswith("M") else int(token)


def parse_raw_metar(line: str, now_utc: datetime | None = None) -> dict | None:
    line = line.strip()
    if not line:
        return None
    tokens = line.split()
    if tokens and tokens[0] in ("METAR", "SPECI"):
        tokens = tokens[1:]
    if not tokens:
        return None

    icao = tokens[0].upper()
    if not re.fullmatch(r"[A-Z0-9]{4}", icao):
        return None

    now = now_utc or datetime.now(timezone.utc)
    obs_dt = now

    for tok in tokens[1:4]:
        m_time = re.fullmatch(r"(\d{2})(\d{2})(\d{2})Z", tok)
        if m_time:
            day, hour, minute = int(m_time.group(1)), int(m_time.group(2)), int(m_time.group(3))
            try:
                cand = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
            except ValueError:
                prev_month = (now.replace(day=1) - timedelta(days=1))
                cand = prev_month.replace(day=min(day, prev_month.day), hour=hour, minute=minute, second=0, microsecond=0)
            if cand - now > timedelta(days=2):
                prev_month = (now.replace(day=1) - timedelta(days=1))
                cand = prev_month.replace(day=min(day, prev_month.day), hour=hour, minute=minute, second=0, microsecond=0)
            obs_dt = cand
            break

    wdir = None
    wspd_kt = None
    m_wind = re.search(r"\b(\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?(MPS|KT)\b", line)
    if m_wind:
        if m_wind.group(1) != "VRB":
            wdir = int(m_wind.group(1))
        spd_val = int(m_wind.group(2))
        unit = m_wind.group(4)
        wspd_kt = round(spd_val / 0.514444, 1) if unit == "MPS" else float(spd_val)

    temp = None
    dewp = None
    m_temp = re.search(r"\b(M?\d{2})/(M?\d{2}|//)\b", line)
    if m_temp:
        temp = _metar_signed_temp(m_temp.group(1))
        if m_temp.group(2) != "//":
            dewp = _metar_signed_temp(m_temp.group(2))

    if temp is None:
        return None

    altim = None
    m_qnh = re.search(r"\bQ(\d{4})\b", line)
    if m_qnh:
        altim = int(m_qnh.group(1))
    else:
        m_alt = re.search(r"\bA(\d{4})\b", line)
        if m_alt:
            altim = round(int(m_alt.group(1)) / 100.0 * 33.8639)

    vis_km = None
    if re.search(r"\bCAVOK\b", line):
        vis_km = 10.0
    else:
        m_vis = re.search(r"\s(\d{4})(?:\s|$)", line)
        if m_vis and not re.search(r"^0000", m_vis.group(1)):
            v_m = int(m_vis.group(1))
            vis_km = 10.0 if v_m >= 9999 else round(v_m / 1000.0, 1)

    iso_time = obs_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    rec: dict = {
        "icaoId": icao,
        "icao": icao,
        "obsTime": int(obs_dt.timestamp()),
        "reportTime": iso_time,
        "time": iso_time,
        "temp": temp,
        "rawOb": line,
        "metarType": "METAR",
    }
    if dewp is not None:
        rec["dewp"] = dewp
        rec["dew_point"] = dewp
    if wdir is not None:
        rec["wdir"] = wdir
        rec["wind_dir"] = wdir
    if wspd_kt is not None:
        rec["wspd"] = wspd_kt
    if altim is not None:
        rec["altim"] = altim
    if vis_km is not None:
        rec["visib"] = vis_km
    return rec


def fetch_vatsim_metar(icaos: list[str]) -> dict[str, dict]:
    if not icaos:
        return {}
    ids = ",".join(icaos)
    url = f"https://metar.vatsim.net/metar.php?id={urllib.parse.quote(ids)}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    out: dict[str, dict] = {}
    for raw_line in text.splitlines():
        parsed = parse_raw_metar(raw_line)
        if parsed:
            out[parsed["icao"]] = parsed
    return out


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    out_path = repo_root / "data" / "metar_fact.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    existing: dict[str, dict] = {}
    if out_path.exists():
        try:
            old_list = json.loads(out_path.read_text(encoding="utf-8"))
            if isinstance(old_list, list):
                for item in old_list:
                    code = item.get("icao") or item.get("icaoId")
                    if code:
                        existing[code] = item
        except Exception:
            pass

    merged: dict[str, dict] = {}
    try:
        aw = fetch_aviationweather(ICAO_LIST)
        merged.update(aw)
        print(f"AviationWeather fetched: {len(aw)} stations")
    except Exception as exc:
        print(f"AviationWeather warning: {exc}")

    missing = [code for code in ICAO_LIST if code not in merged]
    if missing:
        try:
            vat = fetch_vatsim_metar(missing)
            merged.update(vat)
            print(f"VATSIM fallback fetched: {len(vat)} stations ({list(vat.keys())})")
        except Exception as exc:
            print(f"VATSIM fallback warning: {exc}")

    still_missing = [code for code in ICAO_LIST if code not in merged]
    for code in still_missing:
        if code in existing:
            merged[code] = existing[code]
            print(f"Preserved previous cached record for {code}")

    final_list = [merged[k] for k in sorted(merged.keys())]
    out_path.write_text(json.dumps(final_list, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    times = sorted({str(x.get("time") or x.get("reportTime") or "") for x in final_list if x.get("time") or x.get("reportTime")})
    print(f"Wrote {len(final_list)} stations to {out_path}")
    if times:
        print(f"Observation times range: {times[0]} .. {times[-1]}")
    return 0 if len(final_list) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
