# -*- coding: utf-8 -*-
import os, re, json, zipfile, subprocess, threading, queue, traceback, unicodedata, tempfile, base64, zlib, atexit, ctypes, shutil, time
import xml.etree.ElementTree as ET
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = "OptitexMarkerFromCutplan"
OPTITEX_APP = r"C:\Program Files\Optitex\Optitex 21\App"
CSC = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"

HERE = Path(__file__).resolve().parent

# SINGLE-FILE BUILD:
# The Optitex C# bridge is embedded in this .pyw and compiled silently in Windows TEMP.
_ENGINE_PAYLOAD = """
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
"""
_ENGINE_TEMP_DIR = Path(tempfile.gettempdir()) / ("OptitexMarkerEngine_" + str(os.getpid()))
ENGINE_CS = _ENGINE_TEMP_DIR / "OptitexMarkerEngine.cs"
ENGINE_EXE = _ENGINE_TEMP_DIR / "OptitexMarkerEngine.exe"

def _cleanup_embedded_engine():
    for p in (ENGINE_CS, ENGINE_EXE):
        try:
            if p.exists():
                p.unlink()
        except:
            pass
    try:
        _ENGINE_TEMP_DIR.rmdir()
    except:
        pass

atexit.register(_cleanup_embedded_engine)

APPDATA = Path(os.environ.get("APPDATA", str(Path.home())))
CONFIG_DIR = APPDATA / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"

INVALID_WIN = '<>:"/\\|?*'


def hidden_run(cmd, **kwargs):
    # Prevent CMD/console windows from flashing while C# engine or csc runs.
    if os.name == "nt":
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    return subprocess.run(cmd, **kwargs)

def ascii_native_path_text(text):
    text = str(text).replace("Đ", "D").replace("đ", "d")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.encode("ascii", "ignore").decode("ascii")

def safe_name(s):
    # Optitex 21's native Marker save path is std::string based.
    # Keep generated folder/file names strictly ASCII.
    s = ascii_native_path_text(s)
    s = "".join("_" if c in INVALID_WIN else c for c in s)
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"_+", "_", s)
    s = s.strip(" _.")
    return s or "_"

def pds_last5(pds_path):
    stem = Path(pds_path).stem
    stem = ascii_native_path_text(stem)
    return safe_name(stem[-5:] if len(stem) >= 5 else stem)

def ratio_filename_text(ratio):
    # Windows file names cannot contain "/".
    # Keep the visual meaning of SIZE/QTY by using "-":
    #   XL/1 -> XL-1
    #   28/1 -> 28-1
    #   28/2 + 30/1 -> 28-2+30-1
    parts = []
    for size, qty in ratio.items():
        parts.append("%s-%s" % (safe_name(size), int(qty)))
    return "+".join(parts)

def short_fabric_name(fabric):
    # Compact common fabric names in the Marker filename.
    # Folder names still use the full fabric name.
    s = safe_name(fabric)
    u = s.upper()

    mappings = [
        ("VAI_CHINH", "VC"),
        ("VAI_LOT", "VL"),
        ("KEP_TANG", "KT"),
    ]
    for prefix, short in mappings:
        if u == prefix:
            return short
        if u.startswith(prefix + "_"):
            return short + s[len(prefix):]

    return s

def build_marker_filename(pds_path, fabric, table, ratio):
    # Required format:
    # 5 last PDS chars _ fabric _ table _ ratio
    #
    # Example:
    # DW0DW24479.pds + VẢI CHÍNH BLACK + B1 + S/1 + M/1
    # -> 24479_VC_BLACK_B1_S-1+M-1.mrk
    return "%s_%s_%s_%s.mrk" % (
        pds_last5(pds_path),
        short_fabric_name(fabric),
        safe_name(table),
        ratio_filename_text(ratio),
    )

def ensure_ascii_native_path(path_text, label):
    p = str(path_text)
    try:
        p.encode("ascii")
    except UnicodeEncodeError:
        raise ValueError(
            label + " đang có chữ tiếng Việt/ký tự Unicode trong đường dẫn.\\n"
            "Optitex native Save có thể không ghi được .mrk vào đường dẫn này.\\n\\n"
            "Hãy dùng đường dẫn không dấu, ví dụ:\\n"
            r"C:\OPTITEX_MARKER_OUTPUT"
        )

def col_index(ref):
    m = re.match(r"([A-Z]+)", ref.upper())
    n = 0
    for ch in m.group(1):
        n = n * 26 + ord(ch) - 64
    return n

def _shared_strings(z):
    p = "xl/sharedStrings.xml"
    if p not in z.namelist():
        return []
    root = ET.fromstring(z.read(p))
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    out = []
    for si in root.findall("m:si", ns):
        texts = []
        for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"):
            texts.append(t.text or "")
        out.append("".join(texts))
    return out

def read_xlsx_sheet(path, target_name="BIỂU CẮT"):
    with zipfile.ZipFile(path, "r") as z:
        ns = {
            "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
            "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
            "p": "http://schemas.openxmlformats.org/package/2006/relationships",
        }
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rid = None
        for sh in wb.findall("m:sheets/m:sheet", ns):
            if sh.attrib.get("name", "").strip().upper() == target_name.upper():
                rid = sh.attrib.get("{%s}id" % ns["r"])
                break
        if rid is None:
            raise ValueError("Không tìm thấy sheet BIỂU CẮT")

        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = None
        for rel in rels.findall("p:Relationship", ns):
            if rel.attrib.get("Id") == rid:
                target = rel.attrib["Target"]
                break
        if not target:
            raise ValueError("Không tìm thấy worksheet XML của BIỂU CẮT")
        if target.startswith("/"):
            sheet_path = target.lstrip("/")
        else:
            sheet_path = "xl/" + target.replace("\\", "/")
        while "/../" in sheet_path:
            parts = []
            for p in sheet_path.split("/"):
                if p == "..":
                    if parts: parts.pop()
                elif p != ".":
                    parts.append(p)
            sheet_path = "/".join(parts)

        shared = _shared_strings(z)
        root = ET.fromstring(z.read(sheet_path))
        rows = {}
        for c in root.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
            ref = c.attrib.get("r")
            if not ref:
                continue
            rm = re.search(r"(\d+)$", ref)
            if not rm:
                continue
            r = int(rm.group(1))
            col = col_index(ref)
            typ = c.attrib.get("t", "")
            val = None
            if typ == "inlineStr":
                texts = []
                for t in c.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"):
                    texts.append(t.text or "")
                val = "".join(texts)
            else:
                v = c.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
                raw = "" if v is None or v.text is None else v.text
                if typ == "s" and raw != "":
                    try: val = shared[int(raw)]
                    except: val = raw
                elif typ == "b":
                    val = (raw == "1")
                elif typ == "str":
                    val = raw
                else:
                    if raw == "":
                        val = None
                    else:
                        try:
                            f = float(raw)
                            val = int(f) if f.is_integer() else f
                        except:
                            val = raw
            rows.setdefault(r, {})[col] = val
        return rows

def parse_ratio(text):
    out = {}
    if not text:
        return out
    for part in str(text).replace("＋", "+").split("+"):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(.+?)\s*/\s*(\d+)\s*$", part)
        if not m:
            raise ValueError("Tỉ lệ không đọc được: " + part)
        size = m.group(1).strip()
        qty = int(m.group(2))
        if qty > 0:
            out[size] = out.get(size, 0) + qty
    return out

def analyze_cutplan(path):
    rows = read_xlsx_sheet(path, "BIỂU CẮT")

    style = ""
    sizes = []
    for r in sorted(rows):
        vals = rows[r]
        for v in vals.values():
            if isinstance(v, str):
                m = re.search(r"MÃ\s*HÀNG\s*/\s*STYLE\s*:\s*([^\s]+)", v, re.I)
                if m:
                    style = m.group(1).strip()
        # Tự nhận hàng cỡ: lấy các cột từ G cho tới ngay trước cột TỔNG/TOTAL.
        # Không còn bắt buộc phải đủ 6 cỡ XXS/XS/S/M/L/XL.
        # Ví dụ file chỉ có XS | S | M | TỔNG vẫn được nhận đúng là 3 cỡ.
        total_col = None
        for c in range(7, 61):  # G:BH, đủ rộng cho nhiều cỡ
            v = vals.get(c)
            if isinstance(v, str):
                key = re.sub(r"\s+", " ", v.strip().upper())
                key_ascii = key.replace("Ổ", "O").replace("Ô", "O")
                if key in ("TỔNG", "TỔNG CỘNG", "TOTAL", "TOTAL QTY", "TỔNG SL") or key_ascii in ("TONG", "TONG CONG"):
                    total_col = c
                    break

        if total_col is not None and total_col > 7:
            candidate = []
            ok = True
            for c in range(7, total_col):
                v = vals.get(c)
                if v is None or str(v).strip() == "":
                    ok = False
                    break
                text = str(v).strip()
                # Excel có thể lưu cỡ số dạng 28.0; hiển thị lại thành 28.
                if re.fullmatch(r"-?\d+\.0", text):
                    text = text[:-2]
                candidate.append(text)
            if ok and candidate and all(len(x) <= 20 for x in candidate):
                sizes = candidate
                break

    if not style:
        raise ValueError("Không tìm thấy MÃ HÀNG/STYLE trong sheet BIỂU CẮT")
    if not sizes:
        raise ValueError("Không tìm thấy hàng tiêu đề cỡ trước cột TỔNG/TOTAL")

    markers = []
    current_fabric = None
    for r in sorted(rows):
        vals = rows[r]
        a = vals.get(1)
        b = vals.get(2)
        c = vals.get(3)

        if isinstance(a, str) and a.strip() and re.match(r"^B\d+$", str(b or "").strip(), re.I) and c:
            current_fabric = a.strip()
        if not current_fabric:
            continue
        if not re.match(r"^B\d+$", str(b or "").strip(), re.I):
            continue
        if c is None or str(c).strip() == "":
            continue

        ratio = parse_ratio(c)
        if not ratio:
            continue
        markers.append({
            "row": r,
            "fabric": current_fabric,
            "table": str(b).strip(),
            "ratio_text": str(c).strip(),
            "ratio": ratio,
        })

    if not markers:
        raise ValueError("Không tìm thấy bàn có TỈ LỆ SƠ ĐỒ")
    return {"style": style, "sizes": sizes, "markers": markers}

def find_pds(folder, style):
    folder = Path(folder)
    if not folder.is_dir():
        return None, []
    hits = []
    style_u = style.upper()
    for p in folder.rglob("*.pds"):
        if style_u in p.name.upper():
            hits.append(p)
    hits.sort(key=lambda p: (0 if p.stem.upper().endswith(style_u) else 1, len(p.name), str(p).upper()))
    return (hits[0] if hits else None), hits

def load_config():
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except:
        pass
    return {"fabric": {}, "last_pds_file": "", "last_output_folder": "", "pds_material_catalog": {}}

def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

def compile_engine():
    if ENGINE_EXE.exists():
        return
    if not Path(CSC).exists():
        raise FileNotFoundError("Không tìm thấy CSC: " + CSC)

    _ENGINE_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        source = zlib.decompress(base64.b64decode(_ENGINE_PAYLOAD)).decode("utf-8")
        ENGINE_CS.write_text(source, encoding="utf-8")
        cmd = [
            CSC, "/nologo", "/unsafe", "/platform:x64", "/optimize+",
            "/out:" + str(ENGINE_EXE), str(ENGINE_CS)
        ]
        p = hidden_run(
            cmd,
            cwd=str(_ENGINE_TEMP_DIR),
            capture_output=True,
            text=True,
            errors="replace"
        )
        if p.returncode != 0 or not ENGINE_EXE.exists():
            raise RuntimeError(
                "Biên dịch Marker Engine thất bại:\n" +
                (p.stdout or "") + "\n" + (p.stderr or "")
            )
    finally:
        # Source C# is temporary only; delete it immediately after compile.
        try:
            if ENGINE_CS.exists():
                ENGINE_CS.unlink()
        except:
            pass


def col_letter(n):
    out = ""
    n = int(n)
    while n > 0:
        n, r = divmod(n - 1, 26)
        out = chr(65 + r) + out
    return out

def find_marker_length_column(xlsx_path):
    rows = read_xlsx_sheet(xlsx_path, "BIỂU CẮT")
    for r in sorted(rows):
        for c, v in rows[r].items():
            if not isinstance(v, str):
                continue
            u = " ".join(v.upper().replace("\n", " ").split())
            if "CHIỀU DÀI SƠ ĐỒ" in u or "MARKER LENGTH" in u:
                return int(c)
    # Current Biểu cắt layout uses D for Marker Length.
    return 4

def _resolve_sheet_xml_path(z, target_name="BIỂU CẮT"):
    ns = {
        "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "p": "http://schemas.openxmlformats.org/package/2006/relationships",
    }
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rid = None
    for sh in wb.findall("m:sheets/m:sheet", ns):
        if sh.attrib.get("name", "").strip().upper() == target_name.upper():
            rid = sh.attrib.get("{%s}id" % ns["r"])
            break
    if rid is None:
        raise ValueError("Không tìm thấy sheet BIỂU CẮT")

    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = None
    for rel in rels.findall("p:Relationship", ns):
        if rel.attrib.get("Id") == rid:
            target = rel.attrib["Target"]
            break
    if not target:
        raise ValueError("Không tìm thấy XML của sheet BIỂU CẮT")

    if target.startswith("/"):
        sheet_path = target.lstrip("/")
    else:
        sheet_path = "xl/" + target.replace("\\", "/")

    while "/../" in sheet_path:
        parts = []
        for part in sheet_path.split("/"):
            if part == "..":
                if parts:
                    parts.pop()
            elif part != ".":
                parts.append(part)
        sheet_path = "/".join(parts)

    return sheet_path

def update_excel_marker_lengths(xlsx_path, row_to_meters, length_col=None):
    """
    V23 SAFE EXCEL WRITER.

    Không parse rồi serialize lại cả worksheet bằng ElementTree nữa.
    Chỉ thay đúng XML của các ô CHIỀU DÀI SƠ ĐỒ cần cập nhật.
    Vì vậy các namespace, drawing, công thức, conditional formatting,
    extLst và cấu trúc gốc của Excel được giữ nguyên byte-for-byte
    ngoài các cell Marker Length được sửa.

    Ghi trực tiếp vào file gốc, nhưng chỉ sau khi file tạm đã được kiểm tra hợp lệ.
    """
    xlsx_path = Path(xlsx_path)
    if not xlsx_path.is_file():
        raise FileNotFoundError(str(xlsx_path))
    if not row_to_meters:
        raise ValueError("Không có chiều dài nào để ghi.")

    if length_col is None:
        length_col = find_marker_length_column(xlsx_path)

    col_name = col_letter(length_col)

    # V24: ghi trực tiếp vào FILE GỐC nhưng vẫn dùng file tạm để đảm bảo an toàn.
    # Chỉ khi file tạm đã kiểm tra hợp lệ mới replace file gốc.
    tmp_path = xlsx_path.with_name(
        xlsx_path.stem + ".__V24_SAFE_TMP__" + xlsx_path.suffix
    )

    def _numeric_text(value):
        # Excel stores numeric XML with dot decimal separator.
        return ("%.2f" % float(value)).encode("ascii")

    try:
        with zipfile.ZipFile(xlsx_path, "r") as zin:
            sheet_path = _resolve_sheet_xml_path(zin, "BIỂU CẮT")
            sheet_xml = zin.read(sheet_path)

            for row_num, meters in sorted(row_to_meters.items()):
                row_num = int(row_num)
                ref = ("%s%d" % (col_name, row_num)).encode("ascii")
                value_xml = _numeric_text(meters)

                # IMPORTANT: match self-closing cell FIRST.
                # If the order is reversed, a regex can accidentally consume
                # the following cell and corrupt sheet XML.
                self_closing = re.compile(
                    rb'<c\b(?=[^>]*\br="' + re.escape(ref) +
                    rb'")(?P<attrs>[^>]*)/>'
                )
                m = self_closing.search(sheet_xml)

                if m:
                    attrs = m.group("attrs")
                    # Remove the trailing "/" consumed by [^>]*, if present.
                    attrs = re.sub(rb'/\s*$', b'', attrs)
                    # Numeric cell must not keep string type.
                    attrs = re.sub(rb'\s+t="[^"]*"', b'', attrs)
                    replacement = (
                        b'<c' + attrs + b'><v>' +
                        value_xml + b'</v></c>'
                    )
                    sheet_xml = (
                        sheet_xml[:m.start()] +
                        replacement +
                        sheet_xml[m.end():]
                    )
                    continue

                normal_cell = re.compile(
                    rb'<c\b(?=[^>]*\br="' + re.escape(ref) +
                    rb'")(?P<attrs>[^>]*)>(?P<body>.*?)</c>',
                    re.S
                )
                m = normal_cell.search(sheet_xml)

                if m:
                    attrs = m.group("attrs")
                    attrs = re.sub(rb'\s+t="[^"]*"', b'', attrs)
                    replacement = (
                        b'<c' + attrs + b'><v>' +
                        value_xml + b'</v></c>'
                    )
                    sheet_xml = (
                        sheet_xml[:m.start()] +
                        replacement +
                        sheet_xml[m.end():]
                    )
                    continue

                # Generated Biểu cắt files already contain D cells on every table row.
                # If not found, fail safely rather than modify row XML heuristically.
                raise ValueError(
                    "Không tìm thấy ô %s trong sheet BIỂU CẮT. "
                    "File gốc không bị thay đổi." % ref.decode("ascii")
                )

            with zipfile.ZipFile(tmp_path, "w") as zout:
                for item in zin.infolist():
                    data = (
                        sheet_xml
                        if item.filename == sheet_path
                        else zin.read(item.filename)
                    )
                    # Preserve the original ZIP metadata for every workbook part.
                    zout.writestr(item, data)

        # Validate the ZIP package and the edited worksheet XML.
        with zipfile.ZipFile(tmp_path, "r") as check:
            required = {
                "[Content_Types].xml",
                "xl/workbook.xml",
                sheet_path,
            }
            missing = required.difference(check.namelist())
            if missing:
                raise ValueError(
                    "File Excel tạm thiếu thành phần: " +
                    ", ".join(sorted(missing))
                )

            # Parse only as validation; do not serialize it back.
            ET.fromstring(check.read(sheet_path))

        # Chỉ tới đây mới thay file gốc. Nếu có lỗi trước đó, file gốc vẫn nguyên vẹn.
        os.replace(tmp_path, xlsx_path)
        return xlsx_path

    except:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except:
            pass
        raise


class OptitexUsedLengthReader:
    """
    Read-only Optitex Marker reader.
    UsedLength is returned in the same SDK length unit as Width (cm on this setup).
    """
    def __init__(self):
        self.app = None
        self.drawdll = None
        self.markerdbt = None
        self.load_marker = None
        self.remove_marker = None
        self.destruct = None
        self.used_length = None
        self.table_length = None

    def __enter__(self):
        if os.name != "nt":
            raise RuntimeError("Chức năng đọc Marker chỉ chạy trên Windows.")

        draw_path = os.path.join(OPTITEX_APP, "OtDrawSDK142x64.dll")
        dbt_path = os.path.join(OPTITEX_APP, "MarkerDBT.dll")
        if not os.path.isfile(draw_path) or not os.path.isfile(dbt_path):
            raise FileNotFoundError(
                "Không tìm thấy DLL Optitex 21 trong:\n" + OPTITEX_APP
            )

        self.drawdll = ctypes.WinDLL(draw_path)
        self.markerdbt = ctypes.WinDLL(dbt_path)

        construct = self.drawdll[13]  # ConstructMarkerApp
        construct.argtypes = []
        construct.restype = ctypes.c_void_p

        self.destruct = self.drawdll[16]  # DestructApp
        self.destruct.argtypes = [ctypes.c_void_p]
        self.destruct.restype = None

        self.app = construct()
        if not self.app:
            raise RuntimeError("ConstructMarkerApp trả về NULL.")

        vt = ctypes.c_void_p.from_address(self.app).value
        if not vt:
            raise RuntimeError("MarkerApp vtable = NULL.")

        load_addr = ctypes.c_void_p.from_address(vt + 0x50).value
        remove_addr = ctypes.c_void_p.from_address(vt + 0x58).value
        if not load_addr or not remove_addr:
            raise RuntimeError("Không lấy được LoadMarker/RemoveMarker.")

        LOAD = ctypes.CFUNCTYPE(
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p
        )
        REMOVE = ctypes.CFUNCTYPE(
            ctypes.c_ubyte, ctypes.c_void_p, ctypes.c_void_p
        )
        self.load_marker = LOAD(load_addr)
        self.remove_marker = REMOVE(remove_addr)

        base = int(self.markerdbt._handle)

        # Confirmed on Optitex 21.0.300.0:
        # CMarkerAllData::UsedLength() -> RVA 0xAB510
        # CMarkerAllData::Length()     -> RVA 0xAA720
        GETDOUBLE = ctypes.CFUNCTYPE(ctypes.c_double, ctypes.c_void_p)
        self.used_length = GETDOUBLE(base + 0xAB510)
        self.table_length = GETDOUBLE(base + 0xAA720)

        return self

    def read(self, marker_path):
        p = str(marker_path)
        try:
            p.encode("ascii")
        except UnicodeEncodeError:
            raise ValueError(
                "Đường dẫn Marker có Unicode, Optitex SDK bản này dùng char*: " + p
            )

        marker = self.load_marker(self.app, os.fsencode(p))
        if not marker:
            raise RuntimeError("LoadMarker thất bại: " + p)

        try:
            used_cm = float(self.used_length(marker))
            table_cm = float(self.table_length(marker))
            return used_cm, table_cm
        finally:
            try:
                self.remove_marker(self.app, marker)
            except:
                pass

    def __exit__(self, exc_type, exc, tb):
        if self.app:
            try:
                self.destruct(self.app)
            except:
                pass
        self.app = None

def find_marker_for_cutplan_row(all_markers, marker_root, item):
    """
    Prefer exact filename suffix created by this tool.
    Fall back to fabric folder + table token.
    """
    expected_suffix = (
        "_" + short_fabric_name(item["fabric"]) +
        "_" + safe_name(item["table"]) +
        "_" + ratio_filename_text(item["ratio"]) +
        ".mrk"
    ).upper()

    exact = [
        p for p in all_markers
        if p.name.upper().endswith(expected_suffix)
    ]
    if exact:
        exact.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return exact[0], ("OK" if len(exact) == 1 else "Nhiều file - lấy file mới nhất")

    safe_fabric = safe_name(item["fabric"]).upper()
    table_token = "_" + safe_name(item["table"]).upper() + "_"
    fallback = []
    for p in all_markers:
        if table_token not in ("_" + p.stem.upper() + "_"):
            continue
        try:
            rel_parts = [x.upper() for x in p.relative_to(marker_root).parts[:-1]]
        except:
            rel_parts = [p.parent.name.upper()]
        if safe_fabric in rel_parts or p.parent.name.upper() == safe_fabric:
            fallback.append(p)

    if fallback:
        fallback.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return fallback[0], ("Khớp theo Loại vải+Bàn" if len(fallback) == 1 else "Nhiều file - lấy file mới nhất")

    return None, "Không tìm thấy Marker"



class VCheckBox(tk.Frame):
    """Ô tích hiển thị dấu ✓ thay cho dấu X."""
    def __init__(self, parent, variable, command=None, **kwargs):
        bg = kwargs.pop("bg", "white")
        super().__init__(parent, bg=bg, **kwargs)
        self.variable = variable
        self.command = command

        self.box = tk.Label(
            self,
            text="",
            width=2,
            bg="white",
            fg="#13833b",
            font=("Segoe UI Symbol", 12, "bold"),
            relief="solid",
            bd=1,
            cursor="hand2"
        )
        self.box.pack()

        self.box.bind("<Button-1>", self._toggle)
        self.bind("<Button-1>", self._toggle)

        try:
            self.variable.trace_add("write", self._on_var)
        except:
            pass

        self._refresh()

    def _on_var(self, *args):
        self._refresh()

    def _refresh(self):
        try:
            checked = bool(self.variable.get())
        except:
            checked = False

        self.box.configure(
            text="✓" if checked else "",
            bg="#eefaf2" if checked else "white",
            fg="#13833b"
        )

    def _toggle(self, event=None):
        try:
            self.variable.set(not bool(self.variable.get()))
            if self.command:
                self.command()
        except:
            pass
        return "break"



class MultiMaterialDropdown(ttk.Menubutton):
    def __init__(self, parent, materials, selected=None, width=22):
        self.display_var = tk.StringVar()
        super().__init__(parent, textvariable=self.display_var, width=width)
        self.menu = tk.Menu(self, tearoff=False)
        self["menu"] = self.menu
        self.vars = {}
        self.set_materials(materials, selected or [])

    def set_materials(self, materials, selected=None):
        selected_set = set(selected or self.get_selected())
        self.menu.delete(0, "end")
        self.vars = {}
        for mat in materials:
            mat = str(mat).strip()
            if not mat:
                continue
            v = tk.BooleanVar(value=(mat in selected_set))
            self.vars[mat] = v
            self.menu.add_checkbutton(
                label=mat,
                variable=v,
                command=self._refresh_text
            )
        self._refresh_text()

    def get_selected(self):
        return [m for m,v in self.vars.items() if v.get()]

    def _refresh_text(self):
        vals = self.get_selected()
        self.display_var.set(", ".join(vals) if vals else "(chưa chọn)")

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("OPTITEX MARKER TOOL - V32 ĐỐI RIÊNG TỪNG CỠ")
        self.root.geometry("1240x800")
        self.root.minsize(760, 520)
        self.cfg = load_config()
        self.plan = None
        self.fabric_vars = {}
        self.fabric_materials = {}
        self.material_widgets = {}
        self.fabric_enabled = {}
        self.fabric_opposite = {}
        self.material_catalog = []
        self.q = queue.Queue()
        # None trước khi phân tích; sau khi phân tích là tập index các bàn được chọn để tạo.
        self.selected_marker_indices = None

        self._setup_styles()

        self.excel_var = tk.StringVar()
        self.pds_file_var = tk.StringVar(value=self.cfg.get("last_pds_file", ""))
        self.output_var = tk.StringVar(value=self.cfg.get("last_output_folder", ""))
        self.pds_found_var = tk.StringVar(value="PDS: chưa phân tích")

        self._build()

    def _setup_styles(self):
        self.root.configure(bg="#eef3f8")
        style = ttk.Style(self.root)
        try:
            if "clam" in style.theme_names():
                style.theme_use("clam")
        except:
            pass

        style.configure(
            "Main.TNotebook",
            background="#eef3f8",
            borderwidth=0
        )
        style.configure(
            "Main.TNotebook.Tab",
            font=("Segoe UI", 11, "bold"),
            padding=(24, 12),
            background="#dfe8f2",
            foreground="#34495e"
        )
        style.map(
            "Main.TNotebook.Tab",
            background=[("selected", "#1f5fae"), ("active", "#cddbeb")],
            foreground=[("selected", "white"), ("active", "#1f3650")]
        )

        style.configure(
            "Blue.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
            background="#1f5fae",
            foreground="white",
            borderwidth=0
        )
        style.map(
            "Blue.TButton",
            background=[("active", "#174b8a"), ("pressed", "#143f74")]
        )

        style.configure(
            "Green.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
            background="#18864b",
            foreground="white",
            borderwidth=0
        )
        style.map(
            "Green.TButton",
            background=[("active", "#126c3c"), ("pressed", "#0f5a32")]
        )

        style.configure(
            "Orange.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
            background="#d97706",
            foreground="white",
            borderwidth=0
        )
        style.map(
            "Orange.TButton",
            background=[("active", "#b85f05"), ("pressed", "#984d04")]
        )

        style.configure(
            "Soft.TButton",
            font=("Segoe UI", 9, "bold"),
            padding=(9, 6)
        )

        style.configure(
            "Card.Treeview",
            font=("Segoe UI", 9),
            rowheight=28,
            background="white",
            fieldbackground="white",
            borderwidth=0
        )
        style.configure(
            "Card.Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#eaf0f7",
            foreground="#24364b",
            padding=(6, 7)
        )

    def _make_card(self, parent, title, color="#1f5fae", pady=7):
        outer = tk.Frame(
            parent,
            bg="white",
            highlightthickness=1,
            highlightbackground="#d7e0ea"
        )
        head = tk.Frame(outer, bg=color, height=38)
        head.pack(fill="x")
        head.pack_propagate(False)
        tk.Label(
            head,
            text=title,
            bg=color,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
            padx=12
        ).pack(fill="both", expand=True)
        body = tk.Frame(outer, bg="white")
        body.pack(fill="both", expand=True, padx=10, pady=pady)
        return outer, body

    def _row_file(self, parent, row, label, var, browse_cmd):
        ttk.Label(parent, text=label, width=18).grid(row=row, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=6, pady=4)
        ttk.Button(parent, text="Chọn...", command=browse_cmd, width=12).grid(row=row, column=2, padx=6, pady=4)

    def _make_scrollable_page(self, parent, key):
        """
        V26: vùng nội dung tự co theo chiều rộng cửa sổ và có cuộn dọc.
        Footer chức năng nằm ngoài canvas nên luôn nhìn thấy.
        """
        shell = tk.Frame(parent, bg="#eef3f8")
        shell.pack(side="top", fill="both", expand=True)

        canvas = tk.Canvas(
            shell,
            bg="#eef3f8",
            highlightthickness=0,
            bd=0
        )
        vs = ttk.Scrollbar(
            shell,
            orient="vertical",
            command=canvas.yview
        )
        canvas.configure(yscrollcommand=vs.set)

        vs.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        body = tk.Frame(canvas, bg="#eef3f8")
        window_id = canvas.create_window(
            (0, 0),
            window=body,
            anchor="nw"
        )

        def _sync_scrollregion(event=None):
            try:
                canvas.configure(
                    scrollregion=canvas.bbox("all")
                )
            except:
                pass

        def _fit_width(event):
            try:
                # Nội dung luôn co theo đúng chiều rộng khung nhìn.
                canvas.itemconfigure(
                    window_id,
                    width=max(1, event.width)
                )
                _sync_scrollregion()
            except:
                pass

        body.bind("<Configure>", _sync_scrollregion)
        canvas.bind("<Configure>", _fit_width)

        setattr(self, key + "_page_canvas", canvas)
        setattr(self, key + "_page_body", body)
        return body

    def _on_page_mousewheel(self, event):
        """
        Cuộn trang bằng con lăn khi cửa sổ nhỏ.
        Treeview/Text vẫn giữ cuộn riêng của chúng.
        """
        try:
            wclass = event.widget.winfo_class()
            if wclass in (
                "Treeview", "Text", "Listbox",
                "TCombobox", "Spinbox"
            ):
                return

            selected = self.main_notebook.select()
            if selected == str(self.tab_create):
                canvas = self.create_page_canvas
            elif selected == str(self.tab_length):
                canvas = self.length_page_canvas
            else:
                return

            if getattr(event, "num", None) == 4:
                units = -3
            elif getattr(event, "num", None) == 5:
                units = 3
            else:
                delta = int(getattr(event, "delta", 0) or 0)
                if delta == 0:
                    return
                units = -1 * int(delta / 120)
                if units == 0:
                    units = -1 if delta > 0 else 1

            canvas.yview_scroll(units, "units")
            return "break"
        except:
            return

    def _build(self):
        # ===== 2 MENU CHÍNH =====
        self.main_notebook = ttk.Notebook(
            self.root,
            style="Main.TNotebook"
        )
        self.main_notebook.pack(
            fill="both", expand=True, padx=8, pady=8
        )

        self.tab_create = tk.Frame(
            self.main_notebook, bg="#eef3f8"
        )
        self.tab_length = tk.Frame(
            self.main_notebook, bg="#eef3f8"
        )

        self.main_notebook.add(
            self.tab_create,
            text="  1. TẠO SƠ ĐỒ  "
        )
        self.main_notebook.add(
            self.tab_length,
            text="  2. NHẬP CHIỀU DÀI SƠ ĐỒ  "
        )

        # Footer luôn cố định phía dưới, không bị mất khi thu nhỏ cửa sổ.
        self.create_footer_host = tk.Frame(
            self.tab_create, bg="#eef3f8"
        )
        self.create_footer_host.pack(
            side="bottom", fill="x", padx=2, pady=(4, 2)
        )
        create_body = self._make_scrollable_page(
            self.tab_create, "create"
        )

        self.length_footer_host = tk.Frame(
            self.tab_length, bg="#eef3f8"
        )
        self.length_footer_host.pack(
            side="bottom", fill="x", padx=2, pady=(4, 2)
        )
        length_body = self._make_scrollable_page(
            self.tab_length, "length"
        )

        self._build_create_marker_tab(
            create_body,
            self.create_footer_host
        )
        self._build_length_update_tab(
            length_body,
            self.length_footer_host
        )

        # Cuộn trang bằng con lăn ở bất kỳ vùng trống/Entry/Button nào.
        self.root.bind_all(
            "<MouseWheel>",
            self._on_page_mousewheel,
            add="+"
        )
        self.root.bind_all(
            "<Button-4>",
            self._on_page_mousewheel,
            add="+"
        )
        self.root.bind_all(
            "<Button-5>",
            self._on_page_mousewheel,
            add="+"
        )


    def _build_create_marker_tab(self, parent, footer_host):
        # Header
        header = tk.Frame(parent, bg="#173f6b", height=58)
        header.pack(fill="x", padx=2, pady=(2, 8))
        header.pack_propagate(False)
        tk.Label(
            header,
            text="TẠO SƠ ĐỒ OPTITEX TỪ BIỂU CẮT",
            bg="#173f6b",
            fg="white",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=18, fill="y")
        tk.Label(
            header,
            text="Excel → PDS → Marker (.MRK)",
            bg="#173f6b",
            fg="#d8e8f8",
            font=("Segoe UI", 10)
        ).pack(side="right", padx=18, fill="y")

        # Card 1 - data
        card1, top = self._make_card(
            parent,
            "1. DỮ LIỆU ĐẦU VÀO",
            "#1f5fae"
        )
        card1.pack(fill="x", padx=2, pady=(0, 8))
        top.columnconfigure(1, weight=1)

        self._row_file(
            top, 0, "Excel Biểu cắt",
            self.excel_var, self.pick_excel
        )
        self._row_file(
            top, 1, "File PDS",
            self.pds_file_var, self.pick_pds_file
        )
        self._row_file(
            top, 2, "Thư mục lưu Marker",
            self.output_var, self.pick_output
        )

        ttk.Button(
            top,
            text="PHÂN TÍCH BIỂU CẮT",
            command=self.analyze,
            width=24,
            style="Blue.TButton"
        ).grid(
            row=3, column=1, sticky="w",
            padx=6, pady=(7, 5)
        )
        ttk.Label(
            top,
            textvariable=self.pds_found_var,
            font=("Segoe UI", 9, "bold")
        ).grid(
            row=3, column=1, sticky="e",
            padx=6, pady=(7, 5)
        )

        opposite_note = tk.Frame(
            top,
            bg="#fff4d6",
            highlightthickness=1,
            highlightbackground="#f0c36d"
        )
        opposite_note.grid(
            row=4, column=0, columnspan=3,
            sticky="ew", padx=6, pady=(6, 4)
        )
        tk.Label(
            opposite_note,
            text=(
                "SẢN PHẨM ĐỐI THEO CỠ được chọn RIÊNG cho từng Loại vải ở bảng bên dưới."
            ),
            bg="#fff4d6",
            fg="#7a4b00",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            padx=10,
            pady=5
        ).pack(fill="x")
        tk.Label(
            opposite_note,
            text=(
                "Không tích Đối cỡ = toàn bộ 1 chiều.  "
                "Tích Đối cỡ: chia riêng từng cỡ; phần lẻ được phân để cân bằng tổng bó đối và bó thường. Cỡ chỉ có 1 bó giữ nguyên."
            ),
            bg="#fff4d6",
            fg="#6e5a32",
            font=("Segoe UI", 9),
            anchor="w",
            padx=12,
            pady=2
        ).pack(fill="x")

        # Cards 2 + 3
        mid = tk.Frame(parent, bg="#eef3f8")
        mid.pack(fill="both", expand=True, padx=2, pady=0)
        mid.columnconfigure(0, weight=3)
        mid.columnconfigure(1, weight=2)
        mid.rowconfigure(0, weight=1)

        left_card, left = self._make_card(
            mid,
            "2. DANH SÁCH SƠ ĐỒ ĐỌC TỪ EXCEL",
            "#267a69"
        )
        right_card, right = self._make_card(
            mid,
            "3. LOẠI VẢI + MATERIAL TRONG PDS",
            "#6d4bb8"
        )
        left_card.grid(
            row=0, column=0, sticky="nsew",
            padx=(0, 4)
        )
        right_card.grid(
            row=0, column=1, sticky="nsew",
            padx=(4, 0)
        )

        def _reflow_create_cards(event=None):
            try:
                width = self.create_page_canvas.winfo_width()
                if width < 980:
                    # Cửa sổ hẹp: xếp 2 khối theo chiều dọc.
                    mid.columnconfigure(0, weight=1)
                    mid.columnconfigure(1, weight=0)
                    mid.rowconfigure(0, weight=1)
                    mid.rowconfigure(1, weight=1)

                    left_card.grid(
                        row=0, column=0,
                        sticky="nsew",
                        padx=0, pady=(0, 6)
                    )
                    right_card.grid(
                        row=1, column=0,
                        sticky="nsew",
                        padx=0, pady=(0, 0)
                    )
                else:
                    # Cửa sổ rộng: 2 khối nằm cạnh nhau.
                    mid.columnconfigure(0, weight=3)
                    mid.columnconfigure(1, weight=2)
                    mid.rowconfigure(0, weight=1)
                    mid.rowconfigure(1, weight=0)

                    left_card.grid(
                        row=0, column=0,
                        sticky="nsew",
                        padx=(0, 4), pady=0
                    )
                    right_card.grid(
                        row=0, column=1,
                        sticky="nsew",
                        padx=(4, 0), pady=0
                    )
            except:
                pass

        self.create_page_canvas.bind(
            "<Configure>",
            _reflow_create_cards,
            add="+"
        )
        self.root.after(80, _reflow_create_cards)

        # Khung nền trắng riêng cho phần tích chọn bàn tạo Marker.
        select_box = tk.Frame(
            left,
            bg="white",
            highlightthickness=1,
            highlightbackground="#cfd8e3",
            bd=0
        )
        select_box.pack(fill="both", expand=True)

        select_hint = tk.Label(
            select_box,
            text="☑ TÍCH BÀN CẦN TẠO SƠ ĐỒ  •  Bấm ☑ trên tiêu đề để CHỌN/BỎ TẤT CẢ  •  Bấm ô ✓ từng dòng để chọn riêng",
            bg="white",
            fg="#35556f",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            padx=9,
            pady=6
        )
        select_hint.pack(fill="x")

        tree_host = tk.Frame(select_box, bg="white")
        tree_host.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        cols = ("pick","fabric","table","ratio","status")
        self.tree = ttk.Treeview(
            tree_host,
            columns=cols,
            show="headings",
            height=15,
            style="Card.Treeview"
        )
        self.tree.heading("pick", text="☑")
        self.tree.heading("fabric", text="Loại vải")
        self.tree.heading("table", text="Bàn")
        self.tree.heading("ratio", text="Tỉ lệ")
        self.tree.heading("status", text="Trạng thái")
        self.tree.column("pick", width=48, anchor="center", stretch=False)
        self.tree.column("fabric", width=200)
        self.tree.column("table", width=62, anchor="center", stretch=False)
        self.tree.column("ratio", width=225)
        self.tree.column("status", width=120)

        self.tree.tag_configure(
            "ok", background="#e9f8ef", foreground="#17643a"
        )
        self.tree.tag_configure(
            "error", background="#fdecec", foreground="#9f1d1d"
        )
        self.tree.tag_configure(
            "skip", background="#f2f4f6", foreground="#68737d"
        )

        ys = ttk.Scrollbar(
            tree_host, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=ys.set)
        self.tree.bind("<Button-1>", self._on_main_tree_click, add="+")
        self.tree.pack(side="left", fill="both", expand=True)
        ys.pack(side="right", fill="y")

        # Tích/bỏ tích trực tiếp tại danh sách sơ đồ đọc từ Excel.
        self.tree.bind("<Double-1>", self._on_main_tree_double_click, add="+")
        self.tree.bind("<space>", self._on_main_tree_space, add="+")

        self.config_canvas = tk.Canvas(
            right,
            bg="white",
            highlightthickness=0
        )
        cfg_scroll = ttk.Scrollbar(
            right,
            orient="vertical",
            command=self.config_canvas.yview
        )
        self.config_inner = ttk.Frame(self.config_canvas)
        self.config_inner.bind(
            "<Configure>",
            lambda e: self.config_canvas.configure(
                scrollregion=self.config_canvas.bbox("all")
            )
        )
        self.config_canvas.create_window(
            (0,0),
            window=self.config_inner,
            anchor="nw"
        )
        self.config_canvas.configure(
            yscrollcommand=cfg_scroll.set
        )
        self.config_canvas.pack(
            side="left", fill="both", expand=True
        )
        cfg_scroll.pack(side="right", fill="y")

        # Action card
        action_card, bottom = self._make_card(
            footer_host,
            "4. THỰC HIỆN",
            "#c76c08",
            pady=8
        )
        action_card.pack(fill="x", padx=0, pady=0)

        bottom.columnconfigure(2, weight=1)

        self.save_cfg_btn = ttk.Button(
            bottom,
            text="LƯU CẤU HÌNH",
            command=self.save_fabric_config,
            width=18,
            style="Soft.TButton"
        )
        self.save_cfg_btn.grid(
            row=0, column=0,
            sticky="w",
            padx=(0, 6), pady=1
        )

        self.create_btn = ttk.Button(
            bottom,
            text="TẠO SƠ ĐỒ ĐÃ CHỌN",
            command=self.start_create,
            width=24,
            style="Green.TButton"
        )
        self.create_btn.grid(
            row=0, column=1,
            sticky="w",
            padx=6, pady=1
        )

        self.progress = ttk.Progressbar(
            bottom,
            length=380,
            mode="determinate"
        )
        self.progress.grid(
            row=0, column=2,
            sticky="ew",
            padx=(12, 0), pady=4
        )

        def _reflow_create_footer(event=None):
            try:
                width = bottom.winfo_width()
                if width < 820:
                    self.save_cfg_btn.grid(
                        row=0, column=0,
                        sticky="ew",
                        padx=(0, 4), pady=(0, 4)
                    )
                    self.create_btn.grid(
                        row=0, column=1,
                        sticky="ew",
                        padx=(4, 0), pady=(0, 4)
                    )
                    self.progress.grid(
                        row=1, column=0,
                        columnspan=2,
                        sticky="ew",
                        padx=0, pady=(3, 0)
                    )
                    bottom.columnconfigure(0, weight=1)
                    bottom.columnconfigure(1, weight=1)
                    bottom.columnconfigure(2, weight=0)
                else:
                    self.save_cfg_btn.grid(
                        row=0, column=0,
                        sticky="w",
                        padx=(0, 6), pady=1
                    )
                    self.create_btn.grid(
                        row=0, column=1,
                        sticky="w",
                        padx=6, pady=1
                    )
                    self.progress.grid(
                        row=0, column=2,
                        columnspan=1,
                        sticky="ew",
                        padx=(12, 0), pady=4
                    )
                    bottom.columnconfigure(0, weight=0)
                    bottom.columnconfigure(1, weight=0)
                    bottom.columnconfigure(2, weight=1)
            except:
                pass

        bottom.bind(
            "<Configure>",
            _reflow_create_footer,
            add="+"
        )
        self.root.after(100, _reflow_create_footer)

        # Log card
        log_card, log_body = self._make_card(
            parent,
            "NHẬT KÝ",
            "#455a64",
            pady=5
        )
        log_card.pack(fill="both", padx=2, pady=(0, 2))
        self.log = tk.Text(
            log_body,
            height=7,
            wrap="word",
            bg="#fbfcfe",
            fg="#263238",
            relief="flat",
            font=("Consolas", 9)
        )
        self.log.pack(fill="both", expand=True)

    def _build_length_update_tab(self, parent, footer_host):
        # Header
        header = tk.Frame(parent, bg="#7a4d12", height=58)
        header.pack(fill="x", padx=2, pady=(2, 8))
        header.pack_propagate(False)
        tk.Label(
            header,
            text="NHẬP CHIỀU DÀI SƠ ĐỒ ĐÃ GIÁC VÀO BIỂU CẮT",
            bg="#7a4d12",
            fg="white",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=18, fill="y")
        tk.Label(
            header,
            text="Đọc UsedLength từ .MRK → ghi vào Excel gốc",
            bg="#7a4d12",
            fg="#f7e6cb",
            font=("Segoe UI", 10)
        ).pack(side="right", padx=18, fill="y")

        self.length_excel_var = tk.StringVar(
            value=self.excel_var.get().strip()
        )
        self.length_marker_var = tk.StringVar(
            value=self.output_var.get().strip()
        )
        self.length_status_var = tk.StringVar(
            value="Chọn Excel Biểu cắt + thư mục chứa Marker đã giác."
        )
        self.length_preview_rows = []

        # Card input
        card1, top = self._make_card(
            parent,
            "1. CHỌN FILE BIỂU CẮT VÀ THƯ MỤC MARKER ĐÃ GIÁC",
            "#b26908"
        )
        card1.pack(fill="x", padx=2, pady=(0, 8))
        top.columnconfigure(1, weight=1)

        ttk.Label(
            top,
            text="Excel Biểu cắt",
            width=22
        ).grid(
            row=0, column=0,
            sticky="w", padx=6, pady=5
        )
        ttk.Entry(
            top,
            textvariable=self.length_excel_var
        ).grid(
            row=0, column=1,
            sticky="ew", padx=6, pady=5
        )

        def choose_excel():
            p = filedialog.askopenfilename(
                parent=self.root,
                title="Chọn Excel Biểu cắt",
                filetypes=[
                    ("Excel (*.xlsx, *.xlsm)", "*.xlsx *.xlsm"),
                    ("Excel Workbook (*.xlsx)", "*.xlsx"),
                    ("Excel Macro-Enabled (*.xlsm)", "*.xlsm"),
                    ("All files", "*.*")
                ]
            )
            if p:
                self.length_excel_var.set(p)

        ttk.Button(
            top,
            text="Chọn...",
            command=choose_excel,
            width=12,
            style="Soft.TButton"
        ).grid(
            row=0, column=2,
            padx=6, pady=5
        )

        ttk.Label(
            top,
            text="Thư mục Marker đã giác",
            width=22
        ).grid(
            row=1, column=0,
            sticky="w", padx=6, pady=5
        )
        ttk.Entry(
            top,
            textvariable=self.length_marker_var
        ).grid(
            row=1, column=1,
            sticky="ew", padx=6, pady=5
        )

        def choose_marker_folder():
            p = filedialog.askdirectory(
                parent=self.root,
                title="Chọn thư mục chứa các file .MRK đã giác"
            )
            if p:
                self.length_marker_var.set(p)

        ttk.Button(
            top,
            text="Chọn...",
            command=choose_marker_folder,
            width=12,
            style="Soft.TButton"
        ).grid(
            row=1, column=2,
            padx=6, pady=5
        )

        # Result card
        card2, mid = self._make_card(
            parent,
            "2. CHIỀU DÀI ĐỌC TRỰC TIẾP TỪ MARKER",
            "#267a69"
        )
        card2.pack(
            fill="both", expand=True,
            padx=2, pady=(0, 8)
        )

        cols = (
            "fabric", "table", "marker",
            "usedcm", "meters", "status"
        )
        self.length_tree = ttk.Treeview(
            mid,
            columns=cols,
            show="headings",
            height=17,
            style="Card.Treeview"
        )
        headers = {
            "fabric": "Loại vải",
            "table": "Bàn",
            "marker": "File Marker",
            "usedcm": "UsedLength (cm)",
            "meters": "Ghi Excel (m)",
            "status": "Trạng thái",
        }
        widths = {
            "fabric": 175,
            "table": 55,
            "marker": 340,
            "usedcm": 115,
            "meters": 105,
            "status": 190,
        }
        for c in cols:
            self.length_tree.heading(
                c, text=headers[c]
            )
            self.length_tree.column(
                c,
                width=widths[c],
                anchor=(
                    "center"
                    if c in ("table","usedcm","meters")
                    else "w"
                )
            )

        self.length_tree.tag_configure(
            "ready",
            background="#e8f7ee",
            foreground="#146a3d"
        )
        self.length_tree.tag_configure(
            "missing",
            background="#fff5df",
            foreground="#8a5a00"
        )
        self.length_tree.tag_configure(
            "error",
            background="#fdeaea",
            foreground="#a51f1f"
        )

        ys = ttk.Scrollbar(
            mid,
            orient="vertical",
            command=self.length_tree.yview
        )
        xs = ttk.Scrollbar(
            mid,
            orient="horizontal",
            command=self.length_tree.xview
        )
        self.length_tree.configure(
            yscrollcommand=ys.set,
            xscrollcommand=xs.set
        )
        self.length_tree.grid(
            row=0, column=0, sticky="nsew"
        )
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        mid.rowconfigure(0, weight=1)
        mid.columnconfigure(0, weight=1)

        # Action card
        card3, action = self._make_card(
            footer_host,
            "3. ĐỌC VÀ GHI VÀO EXCEL",
            "#8e5a17"
        )
        card3.pack(fill="x", padx=0, pady=0)

        action.columnconfigure(0, weight=1)

        self.length_status_label = ttk.Label(
            action,
            textvariable=self.length_status_var,
            anchor="w",
            font=("Segoe UI", 9, "bold")
        )
        self.length_status_label.grid(
            row=0, column=0,
            sticky="ew",
            padx=(0, 8), pady=2
        )

        self.length_read_btn = ttk.Button(
            action,
            text="ĐỌC CHIỀU DÀI",
            width=18,
            style="Orange.TButton"
        )
        self.length_read_btn.grid(
            row=0, column=1,
            sticky="e",
            padx=6, pady=1
        )

        self.length_write_btn = ttk.Button(
            action,
            text="GHI VÀO EXCEL GỐC",
            width=23,
            state="disabled",
            style="Green.TButton"
        )
        self.length_write_btn.grid(
            row=0, column=2,
            sticky="e",
            padx=(6, 0), pady=1
        )

        def _reflow_length_footer(event=None):
            try:
                width = action.winfo_width()
                if width < 900:
                    self.length_status_label.grid(
                        row=0, column=0,
                        columnspan=2,
                        sticky="ew",
                        padx=0, pady=(0, 4)
                    )
                    self.length_read_btn.grid(
                        row=1, column=0,
                        sticky="ew",
                        padx=(0, 4), pady=(2, 0)
                    )
                    self.length_write_btn.grid(
                        row=1, column=1,
                        sticky="ew",
                        padx=(4, 0), pady=(2, 0)
                    )
                    action.columnconfigure(0, weight=1)
                    action.columnconfigure(1, weight=1)
                    action.columnconfigure(2, weight=0)
                else:
                    self.length_status_label.grid(
                        row=0, column=0,
                        columnspan=1,
                        sticky="ew",
                        padx=(0, 8), pady=2
                    )
                    self.length_read_btn.grid(
                        row=0, column=1,
                        sticky="e",
                        padx=6, pady=1
                    )
                    self.length_write_btn.grid(
                        row=0, column=2,
                        sticky="e",
                        padx=(6, 0), pady=1
                    )
                    action.columnconfigure(0, weight=1)
                    action.columnconfigure(1, weight=0)
                    action.columnconfigure(2, weight=0)
            except:
                pass

        action.bind(
            "<Configure>",
            _reflow_length_footer,
            add="+"
        )
        self.root.after(100, _reflow_length_footer)

        note_card, note_body = self._make_card(
            parent,
            "LƯU Ý",
            "#607d8b",
            pady=6
        )
        note_card.pack(fill="x", padx=2, pady=(0, 2))
        tk.Label(
            note_body,
            text=(
                "Phần mềm lấy UsedLength thực tế của sơ đồ đã giác. "
                "Đơn vị SDK là cm; khi ghi vào Biểu cắt sẽ chia 100 và làm tròn 2 số lẻ. "
                "V24/V25 ghi trực tiếp vào file Excel gốc bằng file tạm an toàn. "
                "Hãy đóng Excel trước khi ghi."
            ),
            bg="white",
            fg="#44515c",
            font=("Segoe UI", 9),
            wraplength=900,
            justify="left"
        ).pack(fill="x")

        def clear_preview():
            for x in self.length_tree.get_children():
                self.length_tree.delete(x)
            self.length_preview_rows[:] = []

        def do_read():
            clear_preview()
            self.length_write_btn.config(
                state="disabled"
            )

            excel_path = Path(
                self.length_excel_var.get().strip()
            )
            marker_root = Path(
                self.length_marker_var.get().strip()
            )

            if not excel_path.is_file():
                messagebox.showerror(
                    "Lỗi",
                    "Hãy chọn đúng file Excel Biểu cắt.",
                    parent=self.root
                )
                return
            if not marker_root.is_dir():
                messagebox.showerror(
                    "Lỗi",
                    "Hãy chọn đúng thư mục Marker đã giác.",
                    parent=self.root
                )
                return

            try:
                plan = analyze_cutplan(excel_path)
                all_markers = sorted(
                    [
                        p for p in marker_root.rglob("*")
                        if p.is_file()
                        and p.suffix.lower() == ".mrk"
                    ],
                    key=lambda p: str(p).upper()
                )
                if not all_markers:
                    raise ValueError(
                        "Không tìm thấy file .MRK trong thư mục đã chọn."
                    )

                self.length_status_var.set(
                    "Đang đọc %d bàn từ %d file Marker..."
                    % (
                        len(plan["markers"]),
                        len(all_markers)
                    )
                )
                self.root.update_idletasks()

                ok_count = 0
                with OptitexUsedLengthReader() as reader:
                    for idx, item in enumerate(
                        plan["markers"]
                    ):
                        marker_path, match_status = (
                            find_marker_for_cutplan_row(
                                all_markers,
                                marker_root,
                                item
                            )
                        )

                        used_cm = None
                        meters = None
                        result_status = match_status
                        tag = "missing"

                        if marker_path is not None:
                            try:
                                used_cm, table_cm = reader.read(
                                    marker_path
                                )
                                if used_cm > 0:
                                    meters = round(
                                        used_cm / 100.0, 2
                                    )
                                    result_status = "Sẵn sàng ghi"
                                    tag = "ready"
                                    ok_count += 1
                                else:
                                    result_status = (
                                        "Marker chưa có chiều dài đã giác"
                                    )
                                    tag = "missing"
                            except Exception as ex:
                                result_status = (
                                    "Lỗi đọc: " + str(ex)
                                )
                                tag = "error"

                        self.length_preview_rows.append({
                            "excel_row": int(item["row"]),
                            "fabric": item["fabric"],
                            "table": item["table"],
                            "marker": marker_path,
                            "used_cm": used_cm,
                            "meters": meters,
                            "status": result_status,
                        })

                        self.length_tree.insert(
                            "",
                            "end",
                            iid=str(idx),
                            values=(
                                item["fabric"],
                                item["table"],
                                (
                                    ""
                                    if marker_path is None
                                    else marker_path.name
                                ),
                                (
                                    ""
                                    if used_cm is None
                                    else "%.2f" % used_cm
                                ),
                                (
                                    ""
                                    if meters is None
                                    else "%.2f" % meters
                                ),
                                result_status,
                            ),
                            tags=(tag,)
                        )

                self.length_status_var.set(
                    "Đọc xong: %d/%d bàn có chiều dài để ghi."
                    % (
                        ok_count,
                        len(plan["markers"])
                    )
                )
                if ok_count:
                    self.length_write_btn.config(
                        state="normal"
                    )
            except Exception as ex:
                self.length_status_var.set("Lỗi")
                messagebox.showerror(
                    "Lỗi đọc chiều dài",
                    str(ex),
                    parent=self.root
                )

        def do_write():
            excel_path = Path(
                self.length_excel_var.get().strip()
            )
            updates = {
                r["excel_row"]: r["meters"]
                for r in self.length_preview_rows
                if r.get("meters") is not None
            }

            if not updates:
                messagebox.showwarning(
                    "Chưa có dữ liệu",
                    "Không có chiều dài hợp lệ để ghi.",
                    parent=self.root
                )
                return

            if not messagebox.askyesno(
                "Xác nhận",
                "Ghi %d chiều dài TRỰC TIẾP vào file Excel gốc?\n\n"
                "Phần mềm tạo file tạm, kiểm tra hợp lệ rồi mới thay file gốc."
                % len(updates),
                parent=self.root
            ):
                return

            try:
                length_col = find_marker_length_column(
                    excel_path
                )
                output_excel = update_excel_marker_lengths(
                    excel_path,
                    updates,
                    length_col
                )
                self.length_status_var.set(
                    "Đã cập nhật %d chiều dài vào Excel gốc."
                    % len(updates)
                )
                self.excel_var.set(
                    str(output_excel)
                )
                self.length_excel_var.set(
                    str(output_excel)
                )
                self.add_log(
                    "Đã ghi chiều dài đã giác vào Excel gốc: %s"
                    % output_excel
                )
                messagebox.showinfo(
                    "Hoàn tất",
                    "Đã ghi %d chiều dài vào file Biểu cắt gốc.\n\nFile:\n%s"
                    % (
                        len(updates),
                        output_excel
                    ),
                    parent=self.root
                )
            except PermissionError:
                messagebox.showerror(
                    "Excel đang mở",
                    "Không ghi được file. Hãy đóng file Excel đang mở rồi thử lại.",
                    parent=self.root
                )
            except Exception as ex:
                messagebox.showerror(
                    "Lỗi ghi Excel",
                    str(ex),
                    parent=self.root
                )

        self.length_read_btn.config(
            command=do_read
        )
        self.length_write_btn.config(
            command=do_write
        )

    def open_length_update_menu(self):
        # Giữ tương thích với lệnh cũ: chuyển thẳng sang menu 2.
        try:
            self.length_excel_var.set(
                self.excel_var.get().strip()
            )
            self.length_marker_var.set(
                self.output_var.get().strip()
            )
        except:
            pass
        try:
            self.main_notebook.select(
                self.tab_length
            )
        except:
            pass

    def pick_excel(self):
        p = filedialog.askopenfilename(filetypes=[
            ("Excel (*.xlsx, *.xlsm)", "*.xlsx *.xlsm"),
            ("Excel Workbook (*.xlsx)", "*.xlsx"),
            ("Excel Macro-Enabled (*.xlsm)", "*.xlsm"),
            ("All files", "*.*")
        ])
        if p: self.excel_var.set(p)

    def pick_pds_file(self):
        p = filedialog.askopenfilename(
            title="Chọn file PDS",
            filetypes=[("Optitex PDS","*.pds"),("All files","*.*")]
        )
        if p:
            self.pds_file_var.set(p)
            try:
                self.load_pds_material_catalog()
            except Exception as e:
                self.material_catalog = []
                self.pds_found_var.set("PDS: lỗi đọc Material")
                messagebox.showerror("Lỗi đọc PDS", str(e))

    def pick_output(self):
        p = filedialog.askdirectory()
        if p: self.output_var.set(p)

    def add_log(self, s):
        self.log.insert("end", str(s) + "\n")
        self.log.see("end")

    def read_materials_from_pds(self, pds_path):
        compile_engine()
        cmd = [str(ENGINE_EXE), "--list-materials", str(pds_path)]
        p = hidden_run(
            cmd,
            cwd=str(HERE),
            capture_output=True,
            text=True,
            errors="replace"
        )
        text = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
        mats = []
        for ln in text.splitlines():
            if ln.startswith("PDS_MATERIAL="):
                m = ln.split("=",1)[1].strip()
                if m and m not in mats:
                    mats.append(m)
        if p.returncode != 0 or not mats:
            tail = "\n".join(text.splitlines()[-30:])
            raise RuntimeError(
                "Không đọc được danh sách Material trực tiếp từ PDS.\n\n" + tail
            )
        return mats

    def load_pds_material_catalog(self):
        p = self.pds_file_var.get().strip()
        if not p or not Path(p).is_file():
            self.material_catalog = []
            self.pds_found_var.set("PDS: CHƯA CHỌN")
            return

        ensure_ascii_native_path(p, "Đường dẫn PDS")
        self.pds_found_var.set("Đang đọc Material từ PDS...")
        self.root.update_idletasks()

        mats = self.read_materials_from_pds(p)
        self.material_catalog = mats
        self.pds_found_var.set("PDS: %s | Material: %s" % (p, ", ".join(mats)))
        self.add_log("Material đọc trực tiếp từ PDS: " + ", ".join(mats))

        # Refresh existing dropdowns when user changes PDS.
        for fab, widget in self.material_widgets.items():
            old_selected = self.fabric_materials.get(fab, [])
            valid_selected = [m for m in old_selected if m in mats]
            widget.set_materials(mats, valid_selected)
            self.fabric_materials[fab] = valid_selected

    def analyze(self):
        try:
            p = self.excel_var.get().strip()
            if not p:
                raise ValueError("Hãy chọn file Excel Biểu cắt")
            self.plan = analyze_cutplan(p)

            pds_text = self.pds_file_var.get().strip()
            if pds_text and Path(pds_text).is_file():
                self.pds_found_var.set("PDS: " + pds_text)
            else:
                self.pds_found_var.set("PDS: CHƯA CHỌN")

            for x in self.tree.get_children():
                self.tree.delete(x)

            # Mặc định sau khi phân tích: chọn toàn bộ bàn.
            self.selected_marker_indices = set(range(len(self.plan["markers"])))

            for i,m in enumerate(self.plan["markers"]):
                self.tree.insert(
                    "", "end", iid=str(i),
                    values=("✓",m["fabric"],m["table"],m["ratio_text"],"Đã chọn")
                )

            for w in self.config_inner.winfo_children():
                w.destroy()
            self.fabric_vars.clear()
            self.fabric_materials.clear()
            self.material_widgets.clear()
            self.fabric_enabled.clear()
            self.fabric_opposite.clear()

            if self.pds_file_var.get().strip() and Path(self.pds_file_var.get().strip()).is_file():
                self.load_pds_material_catalog()

            fabrics = []
            for m in self.plan["markers"]:
                if m["fabric"] not in fabrics:
                    fabrics.append(m["fabric"])

            ttk.Label(self.config_inner, text="Tạo", font=("Segoe UI",9,"bold")).grid(row=0,column=0,padx=4,pady=4)
            ttk.Label(self.config_inner, text="Loại vải", font=("Segoe UI",9,"bold")).grid(row=0,column=1,sticky="w",padx=4,pady=4)
            ttk.Label(self.config_inner, text="Material trong PDS ▼", font=("Segoe UI",9,"bold")).grid(row=0,column=2,padx=4,pady=4)
            ttk.Label(self.config_inner, text="Đối cỡ", font=("Segoe UI",9,"bold")).grid(row=0,column=3,padx=4,pady=4)
            ttk.Label(self.config_inner, text="Khổ (cm)", font=("Segoe UI",9,"bold")).grid(row=0,column=4,padx=4,pady=4)

            saved = self.cfg.get("fabric", {})
            for r,fab in enumerate(fabrics, start=1):
                dat = saved.get(fab, {})
                mats = dat.get("materials", [])
                mats = [str(x).strip() for x in mats if str(x).strip() in self.material_catalog]
                width = dat.get("width","")
                enabled = bool(dat.get("enabled", True))
                opposite = bool(dat.get("opposite", False))

                ev = tk.BooleanVar(value=enabled)
                ov = tk.BooleanVar(value=opposite)
                wv = tk.StringVar(value=str(width))

                self.fabric_enabled[fab] = ev
                self.fabric_opposite[fab] = ov
                self.fabric_vars[fab] = wv
                self.fabric_materials[fab] = mats

                VCheckBox(self.config_inner, variable=ev).grid(row=r,column=0,padx=4,pady=5)
                ttk.Label(self.config_inner, text=fab, wraplength=200).grid(row=r,column=1,sticky="w",padx=4,pady=5)

                md = MultiMaterialDropdown(self.config_inner, self.material_catalog, mats, width=23)
                md.grid(row=r,column=2,sticky="w",padx=4,pady=5)
                self.material_widgets[fab] = md

                VCheckBox(
                    self.config_inner,
                    variable=ov
                ).grid(row=r,column=3,padx=8,pady=5)

                ttk.Entry(self.config_inner, textvariable=wv, width=10).grid(row=r,column=4,padx=4,pady=5)

            self.add_log("Mã hàng: %s" % self.plan["style"])
            self.add_log("Cỡ: " + ", ".join(self.plan["sizes"]))
            self.add_log("Số bàn Marker trong Excel: %d" % len(self.plan["markers"]))
            self.add_log("Mặc định tích TẤT CẢ bàn. Bấm trực tiếp vào ô ✓ trong danh sách để chọn/bỏ bàn cần tạo.")
            self.add_log("V33: ĐỐI THEO CỠ chia riêng từng cỡ và cân bằng tổng bó đối/thường; cỡ 1 bó giữ nguyên. Ô tích hiển thị dấu ✓.")
            self.add_log("Thư mục lưu: chỉ tạo thư mục từng Loại vải, không tạo thêm thư mục mã hàng.")
            self.add_log("Lưu ý: V30 chưa can thiệp SetScale của Marker vì SetScale có thể đổi kích thước thật; zoom/lăn chuột của Mark.exe sẽ xử lý riêng.")
            self.add_log("Material lấy trực tiếp từ PDS. Nếu tích nhiều Material, mỗi Bàn tạo 1 Marker chứa chung các Material đó.")
            if pds_text and Path(pds_text).is_file() and self.plan["markers"]:
                demo = self.plan["markers"][0]
                self.add_log(
                    "Ví dụ tên Marker: " +
                    build_marker_filename(pds_text, demo["fabric"], demo["table"], demo["ratio"])
                )
            if pds_text and Path(pds_text).is_file():
                self.add_log("PDS đã chọn: " + pds_text)
            else:
                self.add_log("PDS: chưa chọn file.")
            for fab in fabrics:
                n=sum(1 for m in self.plan["markers"] if m["fabric"]==fab)
                self.add_log("  %s: %d Bàn -> %d Marker" % (fab,n,n))

            self._refresh_main_table_selection_status()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _toggle_main_table_index(self, i):
        if not self.plan:
            return
        total = len(self.plan.get("markers", []))
        if i < 0 or i >= total:
            return
        if self.selected_marker_indices is None:
            self.selected_marker_indices = set(range(total))
        if i in self.selected_marker_indices:
            self.selected_marker_indices.remove(i)
        else:
            self.selected_marker_indices.add(i)
        self._refresh_main_table_selection_status()

    def _on_main_tree_click(self, event):
        # Chỉ đổi tích khi bấm đúng cột ✓.
        try:
            row = self.tree.identify_row(event.y)
            col = self.tree.identify_column(event.x)
            if row and col == "#1":
                self._toggle_main_table_index(int(row))
                return "break"
        except:
            pass

    def _on_main_tree_double_click(self, event):
        # Double-click ở bất kỳ cột nào cũng có thể tích/bỏ tích bàn đó.
        try:
            row = self.tree.identify_row(event.y)
            if row:
                self._toggle_main_table_index(int(row))
                return "break"
        except:
            pass

    def _on_main_tree_space(self, event):
        try:
            row = self.tree.focus()
            if row:
                self._toggle_main_table_index(int(row))
                return "break"
        except:
            pass

    def _refresh_main_table_selection_status(self):
        """Hiển thị trạng thái chọn bàn ở danh sách chính."""
        if not self.plan:
            return
        selected = self.selected_marker_indices
        if selected is None:
            selected = set(range(len(self.plan["markers"])))
            self.selected_marker_indices = selected

        for i, m in enumerate(self.plan["markers"]):
            iid = str(i)
            if not self.tree.exists(iid):
                continue
            vals = list(self.tree.item(iid, "values"))
            if not vals:
                continue
            # Cột 0 là ô tích, cột 4 là trạng thái.
            while len(vals) < 5:
                vals.append("")
            vals[0] = "✓" if i in selected else ""
            vals[4] = "Đã chọn" if i in selected else "Không chọn"
            self.tree.item(
                iid,
                values=vals,
                tags=(() if i in selected else ("skip",))
            )


        try:
            total = len(self.plan["markers"])
            self.tree.heading("pick", text=("☑" if total > 0 and len(selected) == total else "☐"))
        except:
            pass

    def toggle_all_marker_rows(self):
        """Click checkbox tiêu đề: chọn tất cả hoặc bỏ tất cả."""
        if not self.plan:
            return

        total = len(self.plan["markers"])
        if total <= 0:
            return

        if self.selected_marker_indices is None:
            self.selected_marker_indices = set(range(total))

        # Nếu hiện đang chọn đủ tất cả -> bỏ tất cả.
        # Nếu đang bỏ một phần hoặc bỏ hết -> chọn lại tất cả.
        if len(self.selected_marker_indices) == total:
            self.selected_marker_indices = set()
        else:
            self.selected_marker_indices = set(range(total))

        self._refresh_main_table_selection_status()

        if self.selected_marker_indices:
            self.add_log("Đã chọn TẤT CẢ %d bàn." % total)
        else:
            self.add_log("Đã BỎ CHỌN TẤT CẢ %d bàn." % total)

    def _on_main_tree_click(self, event):
        """Click checkbox tiêu đề hoặc checkbox từng dòng."""
        try:
            region = self.tree.identify_region(event.x, event.y)
            col = self.tree.identify_column(event.x)

            # Click ô checkbox trên TIÊU ĐỀ cột đầu tiên.
            if region == "heading" and col == "#1":
                self.toggle_all_marker_rows()
                return "break"

            # Click ô checkbox từng dòng.
            if region == "cell" and col == "#1":
                row = self.tree.identify_row(event.y)
                if row:
                    i = int(row)
                    if self.selected_marker_indices is None:
                        self.selected_marker_indices = set(range(len(self.plan["markers"])))
                    if i in self.selected_marker_indices:
                        self.selected_marker_indices.remove(i)
                    else:
                        self.selected_marker_indices.add(i)
                    self._refresh_main_table_selection_status()
                    return "break"
        except Exception:
            pass

    def save_fabric_config(self):
        try:
            fcfg = self.cfg.setdefault("fabric", {})
            for fab,wv in self.fabric_vars.items():
                mats = self.material_widgets[fab].get_selected()
                self.fabric_materials[fab] = mats
                fcfg[fab] = {
                    "materials": list(mats),
                    "width": wv.get().strip(),
                    "enabled": bool(self.fabric_enabled[fab].get()),
                    "opposite": bool(self.fabric_opposite[fab].get())
                }
            self.cfg["last_pds_file"] = self.pds_file_var.get().strip()
            self.cfg["last_output_folder"] = self.output_var.get().strip()
            save_config(self.cfg)

            doi_list = [
                fab for fab, var in self.fabric_opposite.items()
                if var.get()
            ]
            self.add_log(
                "Đã lưu cấu hình Material/Khổ. Loại vải cho phép Đối: %s"
                % (", ".join(doi_list) if doi_list else "Không có")
            )
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def validate_create(self):
        if not self.plan:
            raise ValueError("Hãy bấm PHÂN TÍCH BIỂU CẮT trước")
        pds_text = self.pds_file_var.get().strip()
        if not pds_text or not Path(pds_text).is_file():
            raise ValueError("Hãy chọn đúng file PDS")
        pds = Path(pds_text)

        # Native Optitex path handling in this build is narrow-string based.
        ensure_ascii_native_path(str(pds), "Đường dẫn PDS")

        out = self.output_var.get().strip()
        if not out:
            raise ValueError("Hãy chọn thư mục lưu Marker")
        ensure_ascii_native_path(out, "Thư mục lưu Marker")

        selected_types = 0
        for fab,wv in self.fabric_vars.items():
            if not self.fabric_enabled[fab].get():
                continue
            selected_types += 1
            mats = self.material_widgets[fab].get_selected()
            self.fabric_materials[fab] = mats
            if not mats:
                raise ValueError("Chưa tích Material trong PDS cho: " + fab)
            try:
                width=float(wv.get().strip().replace(",","."))
                if width <= 0: raise ValueError()
            except:
                raise ValueError("Khổ vải không hợp lệ cho: " + fab)

        if selected_types == 0:
            raise ValueError("Chưa tích loại vải nào cần tạo Marker")
        return pds, Path(out)

    def start_create(self):
        try:
            pds, out = self.validate_create()
            self.save_fabric_config()
            compile_engine()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))
            return

        fabric_cfg = {}
        for fab,wv in self.fabric_vars.items():
            mats = self.material_widgets[fab].get_selected()
            self.fabric_materials[fab] = mats
            fabric_cfg[fab] = {
                "enabled": bool(self.fabric_enabled[fab].get()),
                "materials": list(mats),
                "width": wv.get().strip().replace(",", "."),
                "opposite": bool(self.fabric_opposite[fab].get()),
            }

        selected = self.selected_marker_indices
        if selected is None:
            selected = set(range(len(self.plan["markers"])))
        else:
            selected = set(selected)

        total_jobs = sum(
            1
            for i, m in enumerate(self.plan["markers"])
            if i in selected and fabric_cfg[m["fabric"]]["enabled"]
        )

        if total_jobs <= 0:
            messagebox.showwarning(
                "Chưa chọn bàn",
                "Không có bàn hợp lệ nào được chọn để tạo Marker.\n\n"
                "Hãy tích ✓ ít nhất 1 bàn ngay trong DANH SÁCH SƠ ĐỒ ĐỌC TỪ EXCEL.",
                parent=self.root
            )
            return

        self.add_log(
            "Bắt đầu tạo %d bàn đã chọn (trên tổng %d bàn)."
            % (total_jobs, len(self.plan["markers"]))
        )

        self.create_btn.config(state="disabled")
        self.progress["maximum"] = total_jobs
        self.progress["value"] = 0
        t = threading.Thread(
            target=self.worker_create,
            args=(pds, out, fabric_cfg, selected),
            daemon=True
        )
        t.start()
        self.root.after(100, self.poll_queue)

    def worker_create(self, pds, out_root, fabric_cfg, selected_indices):
        selected_indices = set(selected_indices)
        total = sum(
            1
            for i, m in enumerate(self.plan["markers"])
            if i in selected_indices and fabric_cfg[m["fabric"]]["enabled"]
        )
        ok = 0
        done_count = 0
        log_lines = []
        # V20: save directly under the folder selected by the user.
        # selected_output / fabric_type / marker.mrk
        style_root = out_root

        # Track per Excel row status across multiple materials.
        row_results = {i: [] for i in range(len(self.plan["markers"]))}

        for i,m in enumerate(self.plan["markers"]):
            fab = m["fabric"]

            if i not in selected_indices:
                self.q.put(("row", i, "Không chọn"))
                continue

            if not fabric_cfg[fab]["enabled"]:
                self.q.put(("row",i,"Không tạo"))
                continue
            materials = fabric_cfg[fab]["materials"]
            width = fabric_cfg[fab]["width"]
            allow_opposite = bool(fabric_cfg[fab].get("opposite", False))
            folder = style_root / safe_name(fab)
            folder.mkdir(parents=True, exist_ok=True)
            ratio_arg = ";".join("%s=%d"%(k,v) for k,v in m["ratio"].items())

            # Exact Optitex MarkerCreationWizard behavior:
            # multiple selected materials are joined with ";" and passed as ONE
            # StyleSet material filter. Therefore each table creates ONE .mrk
            # containing all selected materials together.
            material_filter = ";".join(materials)
            marker_file_name = build_marker_filename(
                str(pds),
                fab,
                m["table"],
                m["ratio"]
            )
            output = folder / marker_file_name

            if output.exists():
                msg = "SKIP đã có: %s" % output
                row_results[i].append("Đã có")
                self.q.put(("log",msg))
                log_lines.append(msg)
                done_count += 1
                self.q.put(("progress",done_count))
                self.q.put(("row",i,"Đã có"))
                continue

            cmd = [
                str(ENGINE_EXE),
                str(pds),
                material_filter,
                width,
                m["table"],
                str(output),
                ratio_arg,
                "0",
                "1" if allow_opposite else "0"
            ]
            p = hidden_run(
                cmd,
                cwd=str(HERE),
                capture_output=True,
                text=True,
                errors="replace"
            )
            out_text = (p.stdout or "") + ("\n"+p.stderr if p.stderr else "")

            if p.returncode == 0 and output.exists():
                ok += 1
                row_results[i].append("OK")
                msg = "OK %s | %s | Đối=%s | Material=%s | %s" % (
                    fab,
                    m["table"],
                    "CÓ" if allow_opposite else "KHÔNG",
                    material_filter,
                    output
                )
            else:
                row_results[i].append("LỖI")
                tail = "\n".join(out_text.splitlines()[-18:])

                msg = "LỖI %s | %s | Material=%s | code=%s\n%s" % (
                    fab, m["table"], material_filter,
                    p.returncode, tail
                )

            self.q.put(("log",msg))
            log_lines.append(msg)
            done_count += 1
            self.q.put(("progress",done_count))
            self.q.put(("row",i,row_results[i][0]))

        self.q.put(("done",ok,total,str(style_root)))

    def poll_queue(self):
        try:
            while True:
                item=self.q.get_nowait()
                if item[0]=="row":
                    i,status=item[1],item[2]
                    vals=list(self.tree.item(str(i),"values"))
                    if vals:
                        vals[4]=status
                        tag = ""
                        st = str(status).upper()
                        if "OK" in st:
                            tag = "ok"
                        elif "LỖI" in st:
                            tag = "error"
                        elif "KHÔNG TẠO" in st or "KHÔNG CHỌN" in st:
                            tag = "skip"
                        self.tree.item(
                            str(i),
                            values=vals,
                            tags=((tag,) if tag else ())
                        )
                elif item[0]=="log":
                    self.add_log(item[1])
                elif item[0]=="progress":
                    self.progress["value"]=item[1]
                elif item[0]=="done":
                    self.create_btn.config(state="normal")
                    ok,total,folder=item[1],item[2],item[3]
                    self.add_log("HOÀN TẤT: %d/%d Marker tạo mới."%(ok,total))
                    self.add_log("Tên Marker: 5 ký tự cuối PDS_Loại vải_Bàn_Tỉ lệ; ví dụ 24479_VC_BLACK_B1_S-1+M-1.mrk.")
                    self.add_log("Tên thư mục Loại vải và tên file được chuyển KHÔNG DẤU để Optitex lưu .mrk ổn định.")
                    messagebox.showinfo(
                        "Hoàn tất",
                        "Đã tạo mới %d/%d Marker.\n\n"
                        "V20 không chạy bước Piece Display thử nghiệm.\n"
                        "Thư mục Loại vải được tự đổi sang KHÔNG DẤU.\n"
                        "Thư mục kết quả:\n%s" % (ok,total,folder)
                    )
                    return
        except queue.Empty:
            pass
        self.root.after(100,self.poll_queue)

if __name__ == "__main__":
    root=tk.Tk()
    app=App(root)
    if len(__import__("sys").argv)>1:
        p=__import__("sys").argv[1]
        if p.lower().endswith((".xlsx", ".xlsm")):
            app.excel_var.set(p)
    root.mainloop()
