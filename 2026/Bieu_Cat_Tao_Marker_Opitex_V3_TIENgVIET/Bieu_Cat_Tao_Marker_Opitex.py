# -*- coding: utf-8 -*-
"""
PHẦN MỀM TỔNG HỢP V2
- Tác nghiệp cắt / Cutting Plan
- Tạo Marker Optitex
- Phân số tem
- Tự kiểm tra/cập nhật phiên bản

Kiến trúc: 1 file EXE. Khi mở từng chức năng, EXE tự gọi lại chính nó
với tham số --module để mỗi ứng dụng Tkinter chạy trong một tiến trình riêng.
"""
from __future__ import annotations

import os
import sys
import re
import json
import time
import types
import base64
import zlib
import hashlib
import math
import hmac
import tempfile
import threading
import subprocess
import traceback
import urllib.request
import urllib.error
import urllib.parse
try:
    import requests as _requests
except Exception:
    _requests = None
try:
    import certifi as _certifi
except Exception:
    _certifi = None
from pathlib import Path
from datetime import datetime, timezone
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

# Để PyInstaller nhận diện các thư viện bên trong payload nén.
try:
    import openpyxl  # noqa: F401
except Exception:
    openpyxl = None
try:
    from PIL import Image as _PIL_Image  # noqa: F401
except Exception:
    _PIL_Image = None

APP_NAME = "Bieu_Cat_Tao_Marker_Opitex"
APP_VERSION = "3.0.28"
APP_TITLE = "Biểu Cắt - Tạo Marker Optitex"

# Nếu muốn đóng cứng URL update vào EXE, điền HTTPS URL manifest ở đây.
# Nếu để trống, có thể nhập URL từ màn hình CẬP NHẬT; URL được lưu trong AppData.
DEFAULT_UPDATE_MANIFEST_URL = "https://update.quanglan.io.vn/update/cutting/version.json"

# Khi khách chọn NO ở thông báo cập nhật lúc khởi động,
# không hỏi lại trong cùng phiên chạy. Vẫn có thể bấm nút CẬP NHẬT thủ công sau.
_SKIP_AUTO_UPDATE_THIS_RUN = False

# ============================================================
# BẢN QUYỀN / LICENSE - V2.0.6
# ============================================================
LICENSE_PRODUCT_CODE = "CUTTING"
LICENSE_API_BASE = "https://quanglan.io.vn/api/license"
LICENSE_POLICY_URL = "https://quanglan.io.vn/api/license/policy"
TRIAL_API_URL = "https://quanglan.io.vn/api/trial/check"
LICENSE_OFFLINE_GRACE_DAYS = 7
# Chính sách dự phòng khi API bản quyền không truy cập được.
# Đặt False khi website đang tắt yêu cầu key để ứng dụng vẫn mở được lúc mất mạng.
LICENSE_OFFLINE_KEY_REQUIRED = False
TRIAL_HOURS = 24

# Chữ ký cục bộ chỉ nhằm ngăn sửa file license bằng tay một cách đơn giản.
# Việc xác minh thật vẫn do server quyết định.
_LICENSE_LOCAL_SIGN_KEY = b"QL-CUTTING-SUITE-LOCAL-STATE-2026-V1"
# V2 MARKER FIX:
# Ba chương trình được import như module Python thật để PyInstaller có thể
# phân tích toàn bộ dependency (đặc biệt tkinter.filedialog của Marker).
# Khi build --onefile, người dùng vẫn chỉ nhận MỘT file EXE.
import module_cut
import module_marker
import module_tem

_MODULE_CACHE = {
    "cut": module_cut,
    "serial": module_cut,
    "marker": module_marker,
    "tem": module_tem,
}



def _is_frozen():
    return bool(getattr(sys, "frozen", False))


def _runtime_path():
    return Path(sys.executable if _is_frozen() else __file__).resolve()


def _runtime_dir():
    return _runtime_path().parent


def _appdata_dir():
    root = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or str(Path.home())
    p = Path(root) / "CuttingPlanSuite"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _update_config_path():
    return _appdata_dir() / "update_config.json"


def _load_update_config():
    data = {"manifest_url": DEFAULT_UPDATE_MANIFEST_URL, "auto_check": True}
    p = _update_config_path()
    try:
        if p.exists():
            saved = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                data.update(saved)

        # V2.0.3: tự chuyển cấu hình cũ sang kho update riêng của Cutting.
        old_url = "https://update.quanglan.io.vn/update/version.json"
        if str(data.get("manifest_url") or "").strip() == old_url:
            data["manifest_url"] = DEFAULT_UPDATE_MANIFEST_URL
    except Exception:
        pass
    return data


def _save_update_config(data):
    p = _update_config_path()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)



def _license_dir():
    root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
    p = Path(root) / "QuanLan"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _license_path():
    return _license_dir() / "license_cutting.json"


def _utc_now():
    return datetime.now(timezone.utc)


def _dt_to_iso(dt):
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _parse_dt(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _date_is_expired(value):
    """Kiểm tra hết hạn chính xác tới giờ/phút/giây."""
    if not value:
        return False
    try:
        raw = str(value).strip()
        if len(raw) == 10:
            expiry = datetime.fromisoformat(raw + " 23:59:59")
        else:
            expiry = datetime.fromisoformat(raw.replace("Z", "+00:00"))

        if expiry.tzinfo is not None:
            return datetime.now(expiry.tzinfo) >= expiry
        return datetime.now() >= expiry
    except Exception:
        return False


def _machine_id():
    """
    Lấy mã máy ổn định trên Windows.
    Ưu tiên Windows MachineGuid, sau đó mới fallback.
    Giá trị gửi lên server là SHA256 chứ không gửi MachineGuid thô.
    """
    raw_parts = []
    if os.name == "nt":
        try:
            import winreg
            flags = winreg.KEY_READ
            try:
                flags |= winreg.KEY_WOW64_64KEY
            except Exception:
                pass
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
                0,
                flags,
            ) as k:
                guid, _ = winreg.QueryValueEx(k, "MachineGuid")
                if guid:
                    raw_parts.append("MG:" + str(guid))
        except Exception:
            pass

    if not raw_parts:
        try:
            import uuid
            raw_parts.append("MAC:" + str(uuid.getnode()))
        except Exception:
            pass
        raw_parts.append("PC:" + str(os.environ.get("COMPUTERNAME") or "UNKNOWN"))

    raw = "|".join(raw_parts).encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest().upper()


def _machine_code_short():
    mid = _machine_id()
    return "-".join([mid[0:6], mid[6:12], mid[12:18]])


def _trial_machine_id():
    """
    Mã dùng riêng để xác định "mỗi máy chỉ được dùng thử 1 lần".
    Ưu tiên UUID/serial phần cứng để việc gỡ/cài lại phần mềm hoặc xóa AppData
    không tạo lại trial mới. Chỉ SHA256 được gửi lên server.
    """
    parts = []
    if os.name == "nt":
        ps = (
            "$u=(Get-CimInstance Win32_ComputerSystemProduct -ErrorAction SilentlyContinue).UUID;"
            "$b=(Get-CimInstance Win32_BIOS -ErrorAction SilentlyContinue).SerialNumber;"
            "$m=(Get-CimInstance Win32_BaseBoard -ErrorAction SilentlyContinue).SerialNumber;"
            "Write-Output ($u+'|'+$b+'|'+$m)"
        )
        try:
            raw = subprocess.check_output(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                text=True,
                stderr=subprocess.DEVNULL,
                creationflags=_hidden_creationflags(),
                timeout=7,
            ).strip()
            if raw and raw.replace("|", "").strip():
                parts.append("HW:" + raw)
        except Exception:
            pass

    # Fallback để vẫn hoạt động trên máy không đọc được CIM.
    if not parts:
        parts.append("MID:" + _machine_id())

    return hashlib.sha256("|".join(parts).encode("utf-8", errors="ignore")).hexdigest().upper()


def _trial_machine_code_short():
    mid = _trial_machine_id()
    return "-".join([mid[0:6], mid[6:12], mid[12:18]])


def _decode_json_response(raw):
    try:
        data = json.loads(raw.decode("utf-8-sig")) if raw else {}
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return data


def _post_json_robust(url, payload, timeout=10):
    """
    Một số máy mở website bình thường bằng trình duyệt nhưng urllib trong EXE
    không gọi được HTTPS API. Vì vậy thử lần lượt:
      1. urllib
      2. requests + certifi
      3. curl.exe của Windows
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 QUANGLAN-SOFTWARE/%s" % APP_VERSION,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    errors = []

    # 1) urllib
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = _decode_json_response(resp.read(1024 * 1024))
            data["_server_reached"] = True
            data["_transport"] = "urllib"
            return data
    except urllib.error.HTTPError as exc:
        raw = b""
        try:
            raw = exc.read(1024 * 1024)
        except Exception:
            pass
        data = _decode_json_response(raw)
        data.setdefault("ok", False)
        data.setdefault("error", "http_%s" % getattr(exc, "code", "error"))
        data["_server_reached"] = True
        data["_http_status"] = getattr(exc, "code", None)
        data["_transport"] = "urllib"
        return data
    except Exception as exc:
        errors.append("urllib: %s" % exc)

    # 2) requests + certifi
    if _requests is not None:
        try:
            verify_arg = _certifi.where() if _certifi is not None else True
            resp = _requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout,
                verify=verify_arg,
            )
            try:
                data = resp.json()
            except Exception:
                data = {}
            if not isinstance(data, dict):
                data = {}
            data.setdefault("ok", 200 <= resp.status_code < 300)
            if resp.status_code >= 400:
                data.setdefault("error", "http_%s" % resp.status_code)
            data["_server_reached"] = True
            data["_http_status"] = resp.status_code
            data["_transport"] = "requests"
            return data
        except Exception as exc:
            errors.append("requests: %s" % exc)

    # 3) curl.exe (Windows 10/11 thường có sẵn)
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(prefix="ql_api_", suffix=".json")
        os.close(fd)
        Path(tmp_path).write_bytes(body)
        cmd = [
            "curl.exe",
            "-sS",
            "--connect-timeout", str(max(3, min(timeout, 10))),
            "--max-time", str(max(6, timeout + 4)),
            "-X", "POST",
            "-H", "Content-Type: application/json",
            "-H", "Accept: application/json",
            "-H", "User-Agent: Mozilla/5.0 QUANGLAN-SOFTWARE",
            "--data-binary", "@%s" % tmp_path,
            "-w", "\\n__QL_HTTP__:%{http_code}",
            url,
        ]
        cp = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=_hidden_creationflags(),
            timeout=timeout + 8,
        )
        out = cp.stdout or ""
        marker = "\n__QL_HTTP__:"
        if marker in out:
            content, status_text = out.rsplit(marker, 1)
            try:
                status = int(status_text.strip())
            except Exception:
                status = 0
            try:
                data = json.loads(content.strip()) if content.strip() else {}
            except Exception:
                data = {}
            if not isinstance(data, dict):
                data = {}
            if status > 0:
                data.setdefault("ok", 200 <= status < 300)
                if status >= 400:
                    data.setdefault("error", "http_%s" % status)
                data["_server_reached"] = True
                data["_http_status"] = status
                data["_transport"] = "curl"
                return data
        if cp.stderr:
            errors.append("curl: %s" % cp.stderr.strip())
    except Exception as exc:
        errors.append("curl: %s" % exc)
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    raise ConnectionError(" | ".join(errors[-3:]) or "Không kết nối được API")



def _license_policy_check():
    """
    Đọc cấu hình bật/tắt key từ website.
    Khi mất mạng, dùng chính sách dự phòng cục bộ đã cấu hình bên trên.
    """
    payload = {
        "product_code": LICENSE_PRODUCT_CODE,
        "app_version": APP_VERSION,
        "machine_id": _machine_id(),
    }
    try:
        result = _post_json_robust(LICENSE_POLICY_URL, payload, timeout=10)
        if result.get("ok"):
            return {
                "ok": True,
                "server_reached": True,
                "key_required": bool(result.get("key_required", True)),
                "trial_enabled": bool(result.get("trial_enabled", True)),
                "updated_at": result.get("updated_at"),
            }
        return {
            "ok": False,
            "server_reached": bool(result.get("_server_reached")),
            "key_required": True,
            "trial_enabled": True,
            "error": result.get("error"),
        }
    except Exception as exc:
        return {
            "ok": True,
            "server_reached": False,
            "offline_fallback": True,
            "key_required": bool(LICENSE_OFFLINE_KEY_REQUIRED),
            "trial_enabled": False,
            "error": str(exc),
        }



def _trial_check():
    payload = {
        "product_code": LICENSE_PRODUCT_CODE,
        "machine_id": _trial_machine_id(),
        "app_version": APP_VERSION,
    }
    try:
        return _post_json_robust(TRIAL_API_URL, payload, timeout=12)
    except Exception as exc:
        return {
            "ok": False,
            "error": "trial_server_unreachable",
            "message": str(exc),
        }


def _license_signature(data):
    payload = "|".join([
        str(data.get("key", "")).strip().upper(),
        str(data.get("product_code", "")).strip().upper(),
        str(data.get("machine_id", "")).strip().upper(),
        str(data.get("last_verified", "")),
        str(data.get("expires_at", "")),
    ]).encode("utf-8")
    return hmac.new(_LICENSE_LOCAL_SIGN_KEY, payload, hashlib.sha256).hexdigest()


def _save_license_state(data):
    data = dict(data or {})
    data["key"] = str(data.get("key", "")).strip().upper()
    data["product_code"] = LICENSE_PRODUCT_CODE
    data["machine_id"] = _machine_id()
    data["signature"] = _license_signature(data)

    p = _license_path()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def _load_license_state():
    p = _license_path()
    try:
        if not p.exists():
            return {}
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            return {}
        sig = str(data.get("signature", ""))
        expected = _license_signature(data)
        data["_signature_ok"] = bool(sig and hmac.compare_digest(sig, expected))
        return data
    except Exception:
        return {}


def _delete_local_license():
    try:
        _license_path().unlink(missing_ok=True)
    except Exception:
        pass


def _mask_key(key):
    key = str(key or "").strip().upper()
    if len(key) <= 8:
        return key
    return key[:5] + "••••••••" + key[-5:]


def _license_post(endpoint, payload, timeout=10):
    url = LICENSE_API_BASE.rstrip("/") + "/" + endpoint.lstrip("/")
    try:
        return _post_json_robust(url, payload, timeout=max(10, timeout))
    except Exception as exc:
        raise ConnectionError(str(exc))


def _license_error_vi(code):
    mapping = {
        "invalid_key": "Key không tồn tại hoặc không đúng sản phẩm.",
        "blocked": "Key này đã bị khóa. Hãy liên hệ người bán.",
        "expired": "Key đã hết hạn sử dụng.",
        "bound_to_other_machine": "Key này đã được kích hoạt trên một máy khác.",
        "missing_fields": "Thiếu thông tin kích hoạt.",
        "http_403": "Server từ chối key này.",
        "http_404": "Không tìm thấy key trên server.",
    }
    return mapping.get(str(code or ""), "Key không hợp lệ hoặc không thể xác minh.")


def _verify_saved_license():
    """
    Return:
      ok=True  -> được phép chạy.
      ok=False -> phải hiện màn hình nhập key.
    Chỉ cho offline khi trước đó server đã xác minh thành công
    và chưa vượt LICENSE_OFFLINE_GRACE_DAYS.
    """
    state = _load_license_state()
    key = str(state.get("key", "")).strip().upper()
    if not key:
        return {"ok": False, "reason": "not_activated"}

    if not state.get("_signature_ok"):
        return {"ok": False, "reason": "local_state_modified"}

    if str(state.get("machine_id", "")).upper() != _machine_id():
        return {"ok": False, "reason": "machine_changed"}

    if _date_is_expired(state.get("expires_at")):
        return {"ok": False, "reason": "expired", "error": "Key đã hết hạn sử dụng."}

    payload = {
        "key": key,
        "product_code": LICENSE_PRODUCT_CODE,
        "machine_id": _machine_id(),
    }

    try:
        result = _license_post("check", payload, timeout=8)
        if result.get("ok"):
            expires = result.get("expires_at") or state.get("expires_at")
            if _date_is_expired(expires):
                return {"ok": False, "reason": "expired", "error": "Key đã hết hạn sử dụng."}

            state["expires_at"] = expires
            state["last_verified"] = _dt_to_iso(_utc_now())
            _save_license_state(state)
            return {
                "ok": True,
                "mode": "online",
                "key": key,
                "expires_at": expires,
            }

        # Server đã trả lời nhưng không chấp nhận -> không dùng grace offline.
        return {
            "ok": False,
            "reason": str(result.get("error") or "server_rejected"),
            "error": _license_error_vi(result.get("error")),
        }

    except ConnectionError:
        last = _parse_dt(state.get("last_verified"))
        if last:
            age = _utc_now() - last
            if age.total_seconds() <= LICENSE_OFFLINE_GRACE_DAYS * 86400:
                return {
                    "ok": True,
                    "mode": "offline_grace",
                    "key": key,
                    "expires_at": state.get("expires_at"),
                    "offline_days_left": max(
                        0,
                        LICENSE_OFFLINE_GRACE_DAYS - int(age.total_seconds() // 86400),
                    ),
                }

        return {
            "ok": False,
            "reason": "need_internet",
            "error": (
                "Không kết nối được máy chủ bản quyền.\n\n"
                "Máy này chưa được xác minh gần đây. "
                "Hãy kết nối Internet rồi mở lại phần mềm."
            ),
        }


def _activate_license_key(key):
    key = str(key or "").strip().upper().replace(" ", "")
    if not key:
        return {"ok": False, "error": "Vui lòng nhập key."}

    payload = {
        "key": key,
        "product_code": LICENSE_PRODUCT_CODE,
        "machine_id": _machine_id(),
    }

    try:
        result = _license_post("activate", payload, timeout=12)
    except ConnectionError as exc:
        return {
            "ok": False,
            "error": (
                "Không kết nối được API kích hoạt. Máy vẫn có thể vào website bình thường.\n\n"
                "Chi tiết: %s" % str(exc)
            ),
        }

    if not result.get("ok"):
        return {
            "ok": False,
            "error": _license_error_vi(result.get("error")),
            "code": result.get("error"),
        }

    # Check ngay sau khi bind để lấy hạn dùng mới nhất.
    expires_at = None
    try:
        checked = _license_post("check", payload, timeout=10)
        if checked.get("ok"):
            expires_at = checked.get("expires_at")
    except Exception:
        pass

    if _date_is_expired(expires_at):
        return {"ok": False, "error": "Key đã hết hạn sử dụng."}

    state = {
        "key": key,
        "product_code": LICENSE_PRODUCT_CODE,
        "machine_id": _machine_id(),
        "activated_at": _dt_to_iso(_utc_now()),
        "last_verified": _dt_to_iso(_utc_now()),
        "expires_at": expires_at,
    }
    _save_license_state(state)
    return {"ok": True, "key": key, "expires_at": expires_at}



class TrialOrKeyWindow:
    """
    Cửa sổ xuất hiện ở lần mở đầu tiên:
    - BẮT ĐẦU DÙNG THỬ
    - NHẬP KEY NGAY

    Lưu ý: _trial_check() đã chạy trước cửa sổ này, nên máy đã được ghi nhận
    trial trên server. Nếu khách chọn nhập key ngay, sau này không thể quay lại
    lấy thêm 1 ngày trial bằng cách cài lại phần mềm.
    """
    def __init__(self, trial_info=None):
        self.trial_info = dict(trial_info or {})
        self.choice = None

        self.root = tk.Tk()
        self.root.title("QUANGLAN SOFTWARE - Bắt đầu sử dụng")
        self.root.geometry("610x450")
        self.root.resizable(False, False)
        self.root.configure(bg="#eef3f8")

        try:
            self.root.iconname("QUANGLAN")
        except Exception:
            pass

        header = tk.Frame(self.root, bg="#0b4f83", height=78)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="QUANGLAN SOFTWARE",
            font=("Segoe UI", 17, "bold"),
            fg="white",
            bg="#0b4f83",
        ).pack(anchor="w", padx=24, pady=(14, 0))

        tk.Label(
            header,
            text="Biểu Cắt - Tạo Marker Optitex • LỰA CHỌN CÁCH SỬ DỤNG",
            font=("Segoe UI", 8),
            fg="#d8efff",
            bg="#0b4f83",
        ).pack(anchor="w", padx=25)

        body = tk.Frame(
            self.root,
            bg="white",
            highlightthickness=1,
            highlightbackground="#d6e0e9",
        )
        body.pack(fill="both", expand=True, padx=24, pady=22)

        tk.Label(
            body,
            text="Bạn muốn bắt đầu như thế nào?",
            font=("Segoe UI", 16, "bold"),
            fg="#183449",
            bg="white",
        ).pack(anchor="w", padx=22, pady=(20, 4))

        tk.Label(
            body,
            text=(
                "Máy này được dùng thử miễn phí 1 ngày duy nhất.\n"
                "Nếu đã có key, bạn có thể kích hoạt ngay và bỏ qua thời gian dùng thử."
            ),
            font=("Segoe UI", 9),
            fg="#63788a",
            bg="white",
            justify="left",
        ).pack(anchor="w", padx=22, pady=(0, 16))

        cards = tk.Frame(body, bg="white")
        cards.pack(fill="x", padx=22, pady=2)
        cards.grid_columnconfigure(0, weight=1)
        cards.grid_columnconfigure(1, weight=1)

        trial_card = tk.Frame(
            cards,
            bg="#f5fbff",
            highlightthickness=1,
            highlightbackground="#b9d8ee",
        )
        trial_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))

        tk.Label(
            trial_card,
            text="DÙNG THỬ MIỄN PHÍ",
            font=("Segoe UI", 11, "bold"),
            fg="#176da6",
            bg="#f5fbff",
        ).pack(pady=(16, 4))

        tk.Label(
            trial_card,
            text="1 ngày / mỗi máy 1 lần",
            font=("Segoe UI", 9),
            fg="#52687a",
            bg="#f5fbff",
        ).pack()

        tk.Button(
            trial_card,
            text="BẮT ĐẦU DÙNG THỬ",
            command=self.use_trial,
            font=("Segoe UI", 9, "bold"),
            bg="#2375c6",
            fg="white",
            activebackground="#176da6",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=10,
            cursor="hand2",
        ).pack(fill="x", padx=14, pady=(14, 16))

        key_card = tk.Frame(
            cards,
            bg="#f6fff9",
            highlightthickness=1,
            highlightbackground="#b8dec9",
        )
        key_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))

        tk.Label(
            key_card,
            text="ĐÃ CÓ KEY",
            font=("Segoe UI", 11, "bold"),
            fg="#14734a",
            bg="#f6fff9",
        ).pack(pady=(16, 4))

        tk.Label(
            key_card,
            text="Kích hoạt và dùng ngay",
            font=("Segoe UI", 9),
            fg="#52687a",
            bg="#f6fff9",
        ).pack()

        tk.Button(
            key_card,
            text="NHẬP KEY NGAY",
            command=self.enter_key,
            font=("Segoe UI", 9, "bold"),
            bg="#15945b",
            fg="white",
            activebackground="#117847",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=10,
            cursor="hand2",
        ).pack(fill="x", padx=14, pady=(14, 16))

        remaining = int(self.trial_info.get("remaining_seconds", 0) or 0)
        if remaining > 0:
            hours = max(1, int(math.ceil(remaining / 3600.0)))
            info = "Thời gian dùng thử hiện có: khoảng %s giờ." % hours
        else:
            info = "Dùng thử sẽ được tính theo thời gian của máy chủ."

        tk.Label(
            body,
            text=info,
            font=("Segoe UI", 8),
            fg="#7890a4",
            bg="white",
        ).pack(anchor="w", padx=22, pady=(14, 0))

        tk.Label(
            body,
            text="Mã thiết bị: " + _trial_machine_code_short(),
            font=("Segoe UI", 8),
            fg="#7890a4",
            bg="white",
        ).pack(anchor="w", padx=22, pady=(4, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def use_trial(self):
        self.choice = "trial"
        self.root.destroy()

    def enter_key(self):
        self.choice = "key"
        self.root.destroy()

    def close(self):
        self.choice = None
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        self.root.mainloop()
        return self.choice



class LicenseActivationWindow:
    def __init__(self, initial_error=""):
        self.root = tk.Tk()
        self.root.title("Kích hoạt bản quyền - QUANGLAN SOFTWARE")
        self.root.geometry("560x410")
        self.root.resizable(False, False)
        self.root.configure(bg="#eef3f8")
        self.success = False
        self._busy = False

        try:
            self.root.iconname("QUANGLAN")
        except Exception:
            pass

        header = tk.Frame(self.root, bg="#0b4f83", height=72)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="🔑  KÍCH HOẠT PHẦN MỀM",
            font=("Segoe UI", 16, "bold"),
            fg="white",
            bg="#0b4f83",
        ).pack(anchor="w", padx=22, pady=(13, 0))
        tk.Label(
            header,
            text="QUANGLAN SOFTWARE  •  Biểu Cắt - Tạo Marker Optitex",
            font=("Segoe UI", 8),
            fg="#d8efff",
            bg="#0b4f83",
        ).pack(anchor="w", padx=54)

        body = tk.Frame(self.root, bg="white", highlightthickness=1, highlightbackground="#d6e0e9")
        body.pack(fill="both", expand=True, padx=22, pady=20)

        tk.Label(
            body,
            text="Nhập key để sử dụng phần mềm",
            font=("Segoe UI", 14, "bold"),
            fg="#183449",
            bg="white",
        ).pack(anchor="w", padx=20, pady=(20, 4))
        tk.Label(
            body,
            text=(
                "Key sẽ tự động gắn với máy này khi kích hoạt lần đầu.\n"
                "Không cần gửi mã máy cho người bán."
            ),
            font=("Segoe UI", 9),
            fg="#63788a",
            bg="white",
            justify="left",
        ).pack(anchor="w", padx=20)

        self.key_var = tk.StringVar()
        entry = tk.Entry(
            body,
            textvariable=self.key_var,
            font=("Consolas", 13, "bold"),
            relief="solid",
            bd=1,
            justify="center",
        )
        entry.pack(fill="x", padx=20, pady=(18, 5), ipady=9)
        entry.focus_set()
        entry.bind("<Return>", lambda e: self.activate())

        tk.Label(
            body,
            text="Mã thiết bị: " + _machine_code_short(),
            font=("Segoe UI", 8),
            fg="#7890a4",
            bg="white",
        ).pack(anchor="w", padx=20)

        self.status_var = tk.StringVar(
            value=initial_error or "Cần Internet trong lần kích hoạt đầu tiên."
        )
        self.status_label = tk.Label(
            body,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            fg="#b5473c" if initial_error else "#52687a",
            bg="white",
            justify="left",
            wraplength=470,
        )
        self.status_label.pack(fill="x", padx=20, pady=(12, 8))

        row = tk.Frame(body, bg="white")
        row.pack(fill="x", padx=20, pady=(5, 18))
        tk.Button(
            row,
            text="THOÁT",
            command=self.close,
            font=("Segoe UI", 9, "bold"),
            bg="#64748b",
            fg="white",
            relief="flat",
            padx=18,
            pady=9,
        ).pack(side="left")

        tk.Button(
            row,
            text="THỬ KẾT NỐI API",
            command=self.test_api,
            font=("Segoe UI", 9, "bold"),
            bg="#2375c6",
            fg="white",
            relief="flat",
            padx=14,
            pady=9,
        ).pack(side="left", padx=(8, 0))

        self.activate_btn = tk.Button(
            row,
            text="KÍCH HOẠT",
            command=self.activate,
            font=("Segoe UI", 10, "bold"),
            bg="#15945b",
            fg="white",
            relief="flat",
            padx=24,
            pady=9,
        )
        self.activate_btn.pack(side="right")

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def test_api(self):
        if self._busy:
            return
        self._busy = True
        self.activate_btn.config(state="disabled")
        self.status_var.set("Đang thử kết nối API...")
        self.status_label.config(fg="#52687a")

        def worker():
            result = _trial_check()

            def finish():
                self._busy = False
                self.activate_btn.config(state="normal")
                if result.get("_server_reached") or result.get("trial_active") or result.get("error") == "trial_expired":
                    via = result.get("_transport") or "server"
                    self.status_var.set("Kết nối API thành công qua %s. Có thể nhập key." % via)
                    self.status_label.config(fg="#15945b")
                else:
                    detail = str(result.get("message") or result.get("error") or "Không rõ lỗi")
                    self.status_var.set("Không kết nối được API.\\n" + detail)
                    self.status_label.config(fg="#b5473c")

            try:
                self.root.after(0, finish)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def activate(self):
        if self._busy:
            return
        key = self.key_var.get().strip()
        if not key:
            self.status_var.set("Vui lòng nhập key.")
            self.status_label.config(fg="#b5473c")
            return

        self._busy = True
        self.activate_btn.config(state="disabled")
        self.status_var.set("Đang kiểm tra key với máy chủ...")
        self.status_label.config(fg="#52687a")

        def worker():
            result = _activate_license_key(key)

            def finish():
                self._busy = False
                self.activate_btn.config(state="normal")
                if result.get("ok"):
                    self.success = True
                    expires = result.get("expires_at") or "Không giới hạn"
                    messagebox.showinfo(
                        "Kích hoạt thành công",
                        "Đã kích hoạt phần mềm trên máy này.\n\nHạn sử dụng: %s" % expires,
                        parent=self.root,
                    )
                    self.root.destroy()
                else:
                    self.status_var.set(str(result.get("error") or "Kích hoạt thất bại."))
                    self.status_label.config(fg="#b5473c")

            try:
                self.root.after(0, finish)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def close(self):
        self.success = False
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        self.root.mainloop()
        return self.success


def _ensure_license_or_prompt():
    """Bản phát hành miễn phí: bỏ hoàn toàn key và trial ở máy khách."""
    return {
        "ok": True,
        "access_type": "free",
        "policy": {"key_required": False, "trial_enabled": False},
    }


    # Mở miễn phí khi server xác nhận đã tắt key, hoặc khi mất mạng và
    # chính sách dự phòng cục bộ cũng đang đặt key_required=False.
    policy_allows_free = (
        policy.get("ok")
        and not policy.get("key_required", True)
        and (policy.get("server_reached") or policy.get("offline_fallback"))
    )
    if policy_allows_free:
        return {
            "ok": True,
            "access_type": "free",
            "policy": policy,
        }

    trial_enabled = bool(policy.get("trial_enabled", True))

    state = _load_license_state()
    has_saved_key = bool(str(state.get("key", "") or "").strip())

    # Đã có key -> luôn ưu tiên xác minh key khi website đang bật chế độ key.
    if has_saved_key:
        check = _verify_saved_license()
        if check.get("ok"):
            check["access_type"] = "license"
            check["policy"] = policy
            return check

        message = str(check.get("error") or "")
        if check.get("reason") == "local_state_modified":
            message = "Thông tin kích hoạt trên máy đã bị thay đổi. Vui lòng nhập lại key."
        elif check.get("reason") == "machine_changed":
            message = "Thông tin máy đã thay đổi. Vui lòng kích hoạt lại bằng key hợp lệ."
        elif check.get("reason") == "expired":
            message = "Key đã hết hạn sử dụng."

        win = LicenseActivationWindow(initial_error=message)
        if not win.run():
            return {"ok": False}

        result = _verify_saved_license()
        if result.get("ok"):
            result["access_type"] = "license"
            result["policy"] = policy
        return result

    # Website đang BẬT KEY nhưng TẮT TRIAL -> hỏi key ngay.
    if not trial_enabled:
        message = "Phần mềm hiện đang yêu cầu bản quyền. Vui lòng nhập key để sử dụng."
        if not policy.get("server_reached"):
            message += (
                "\n\nKhông đọc được cấu hình máy chủ, nên phần mềm đang dùng chế độ an toàn: "
                "yêu cầu key."
            )

        win = LicenseActivationWindow(initial_error=message)
        if not win.run():
            return {"ok": False}

        result = _verify_saved_license()
        if result.get("ok"):
            result["access_type"] = "license"
            result["policy"] = policy
        return result

    # KEY BẬT + TRIAL BẬT: logic trial cũ.
    trial = _trial_check()

    if trial.get("ok") and trial.get("trial_active"):
        chooser = TrialOrKeyWindow(trial_info=trial)
        choice = chooser.run()

        if choice == "trial":
            trial["access_type"] = "trial"
            trial["policy"] = policy
            return trial

        if choice == "key":
            win = LicenseActivationWindow(
                initial_error="Nhập key để kích hoạt ngay và bỏ qua dùng thử."
            )
            if not win.run():
                return {"ok": False}

            result = _verify_saved_license()
            if result.get("ok"):
                result["access_type"] = "license"
                result["policy"] = policy
            return result

        return {"ok": False}

    if str(trial.get("error") or "") == "trial_server_unreachable":
        message = (
            "Không kết nối được máy chủ dùng thử.\n\n"
            "Hãy thử lại hoặc nhập key bản quyền."
        )
    elif str(trial.get("error") or "") == "trial_expired":
        message = (
            "Thời gian dùng thử miễn phí 1 ngày của máy này đã kết thúc.\n\n"
            "Vui lòng nhập key để tiếp tục sử dụng."
        )
    else:
        message = str(
            trial.get("message")
            or "Máy này không còn thời gian dùng thử. Vui lòng nhập key."
        )

    win = LicenseActivationWindow(initial_error=message)
    if not win.run():
        return {"ok": False}

    result = _verify_saved_license()
    if result.get("ok"):
        result["access_type"] = "license"
        result["policy"] = policy
    return result



def _version_tuple(value):
    nums = re.findall(r"\d+", str(value or ""))
    return tuple(int(x) for x in nums[:4]) or (0,)


def _is_newer(remote, current=APP_VERSION):
    a = list(_version_tuple(remote))
    b = list(_version_tuple(current))
    n = max(len(a), len(b))
    return tuple(a + [0] * (n-len(a))) > tuple(b + [0] * (n-len(b)))



def _public_get_json(url, timeout=8):
    errors = []
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "%s/%s" % (APP_NAME, APP_VERSION), "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(1024 * 1024)
        data = json.loads(raw.decode("utf-8-sig"))
        if isinstance(data, dict):
            return data
    except Exception as exc:
        errors.append("urllib: %s" % exc)

    try:
        cp = subprocess.run(
            ["curl.exe", "-fsSL", "--connect-timeout", "5", "--max-time", str(max(8, timeout + 2)), url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=_hidden_creationflags(),
            timeout=max(10, timeout + 4),
        )
        if cp.returncode == 0 and cp.stdout:
            data = json.loads(cp.stdout.decode("utf-8-sig", errors="replace"))
            if isinstance(data, dict):
                return data
        if cp.stderr:
            errors.append("curl: " + cp.stderr.decode("utf-8", errors="replace").strip())
    except Exception as exc:
        errors.append("curl: %s" % exc)

    raise ConnectionError(" | ".join(errors[-2:]) or "Không tải được version.json")


def _public_download(url, dest, timeout=60):
    errors = []
    dest = Path(dest)

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "%s/%s" % (APP_NAME, APP_VERSION)},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp, open(dest, "wb") as f:
            while True:
                chunk = resp.read(1024 * 512)
                if not chunk:
                    break
                f.write(chunk)
        if dest.exists() and dest.stat().st_size > 0:
            return
    except Exception as exc:
        errors.append("urllib: %s" % exc)
        try:
            dest.unlink(missing_ok=True)
        except Exception:
            pass

    try:
        cp = subprocess.run(
            [
                "curl.exe", "-fL",
                "--connect-timeout", "8",
                "--max-time", str(max(90, timeout + 30)),
                "-o", str(dest),
                url,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            creationflags=_hidden_creationflags(),
            timeout=max(120, timeout + 45),
        )
        if cp.returncode == 0 and dest.exists() and dest.stat().st_size > 0:
            return
        if cp.stderr:
            errors.append("curl: " + cp.stderr.decode("utf-8", errors="replace").strip())
    except Exception as exc:
        errors.append("curl: %s" % exc)

    raise ConnectionError(" | ".join(errors[-2:]) or "Không tải được file cập nhật")


def _schedule_prelicense_replace(new_exe, remote_version):
    current = Path(sys.executable).resolve()
    backup = current.with_suffix(current.suffix + ".bak")
    ps1 = Path(tempfile.gettempdir()) / ("CuttingPlan_PreLicense_Update_%d.ps1" % os.getpid())

    # Updater riêng có cửa sổ hiển thị trong lúc thay EXE.
    script = r'''param([int]$PidToWait,[string]$Current,[string]$New,[string]$Backup,[string]$SelfScript,[string]$RemoteVersion)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "QUANGLAN - Dang cap nhat"
$form.StartPosition = "CenterScreen"
$form.Size = New-Object System.Drawing.Size(520,190)
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.ControlBox = $false
$form.TopMost = $true
$form.ShowInTaskbar = $true

$title = New-Object System.Windows.Forms.Label
$title.Text = "DANG CAP NHAT PHAN MEM"
$title.Font = New-Object System.Drawing.Font("Segoe UI",14,[System.Drawing.FontStyle]::Bold)
$title.AutoSize = $true
$title.Location = New-Object System.Drawing.Point(28,22)
$form.Controls.Add($title)

$status = New-Object System.Windows.Forms.Label
$status.Text = "Dang chuan bi cai dat V$RemoteVersion..."
$status.Font = New-Object System.Drawing.Font("Segoe UI",10)
$status.AutoSize = $false
$status.Location = New-Object System.Drawing.Point(30,62)
$status.Size = New-Object System.Drawing.Size(450,28)
$form.Controls.Add($status)

$bar = New-Object System.Windows.Forms.ProgressBar
$bar.Style = "Marquee"
$bar.MarqueeAnimationSpeed = 25
$bar.Location = New-Object System.Drawing.Point(30,100)
$bar.Size = New-Object System.Drawing.Size(450,24)
$form.Controls.Add($bar)

$form.Show()
[System.Windows.Forms.Application]::DoEvents()

try {
  $status.Text = "Dang dong phien ban cu..."
  [System.Windows.Forms.Application]::DoEvents()
  try { Wait-Process -Id $PidToWait -ErrorAction SilentlyContinue } catch {}
  Start-Sleep -Seconds 7

  $status.Text = "Dang thay file phien ban moi V$RemoteVersion..."
  [System.Windows.Forms.Application]::DoEvents()

  if (Test-Path $Backup) { Remove-Item -Force $Backup -ErrorAction SilentlyContinue }
  if (Test-Path $Current) { Move-Item -Force $Current $Backup }
  Copy-Item -Force $New $Current

  if (-not (Test-Path $Current)) { throw "Khong thay file EXE moi sau khi copy." }

  Start-Sleep -Seconds 3
  Remove-Item -Force $New -ErrorAction SilentlyContinue
  Remove-Item -Force $Backup -ErrorAction SilentlyContinue

  $bar.Style = "Blocks"
  $bar.Value = 100
  $status.Text = "Cap nhat V$RemoteVersion hoan tat."
  [System.Windows.Forms.Application]::DoEvents()
  Start-Sleep -Milliseconds 700
  $form.Close()

  [System.Windows.Forms.MessageBox]::Show(
    "Cap nhat V$RemoteVersion da hoan tat.`n`nHay mo lai QUANGLAN SOFTWARE tu icon Desktop.",
    "QUANGLAN - Cap nhat xong",
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Information
  ) | Out-Null
}
catch {
  try {
    if (Test-Path $Current) { Remove-Item -Force $Current -ErrorAction SilentlyContinue }
    if (Test-Path $Backup) { Move-Item -Force $Backup $Current }
  } catch {}
  try { Remove-Item -Force $New -ErrorAction SilentlyContinue } catch {}
  try { $form.Close() } catch {}
  [System.Windows.Forms.MessageBox]::Show(
    "Cap nhat khong thanh cong.`n`nDa phuc hoi ban cu neu co.`n`n" + $_.Exception.Message,
    "QUANGLAN - Loi cap nhat",
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Error
  ) | Out-Null
}
try { Remove-Item -Force $SelfScript -ErrorAction SilentlyContinue } catch {}
'''
    ps1.write_text(script, encoding="utf-8-sig")
    args = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden",
        "-File", str(ps1),
        "-PidToWait", str(os.getpid()),
        "-Current", str(current),
        "-New", str(new_exe),
        "-Backup", str(backup),
        "-SelfScript", str(ps1),
        "-RemoteVersion", str(remote_version),
    ]
    subprocess.Popen(args, creationflags=_hidden_creationflags(), close_fds=True)


def _prelicense_update_check():
    # STARTUP UPDATE - tránh hoàn toàn lỗi Tkinter thread.
    # Tkinter chỉ hỏi YES/NO.
    # Nếu YES, updater PowerShell riêng sẽ hiện cửa sổ tiến trình,
    # tải file, kiểm tra SHA256 và thay EXE.
    global _SKIP_AUTO_UPDATE_THIS_RUN

    if not _is_frozen():
        return False

    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "--module":
        return False

    try:
        cfg = _load_update_config()
        manifest_url = str(
            cfg.get("manifest_url") or DEFAULT_UPDATE_MANIFEST_URL or ""
        ).strip()
        if not manifest_url:
            return False

        manifest = _public_get_json(manifest_url, timeout=8)
        remote_version = str(manifest.get("version") or "").strip()

        if not remote_version or not _is_newer(remote_version, APP_VERSION):
            return False

        download_url = str(manifest.get("download_url") or "").strip()
        if not download_url:
            return False

        notes = str(manifest.get("notes") or "").strip()
        expected_sha = str(manifest.get("sha256") or "").strip().lower()

        ask_root = tk.Tk()
        ask_root.withdraw()
        try:
            msg = (
                "Có phiên bản mới %s.\\n\\n"
                "Phiên bản hiện tại: %s\\n\\n"
                "Bạn có muốn cập nhật ngay không?\\n\\n"
                "YES: mở cửa sổ cập nhật và cài ngay.\\n"
                "NO: vào phần mềm và cập nhật sau."
            ) % (remote_version, APP_VERSION)

            if notes:
                msg += "\\n\\nNội dung:\\n" + notes[:1000]

            accepted = messagebox.askyesno(
                "Có bản cập nhật",
                msg,
                parent=ask_root,
            )
        finally:
            try:
                ask_root.destroy()
            except Exception:
                pass

        if not accepted:
            _SKIP_AUTO_UPDATE_THIS_RUN = True
            return False

        current_exe = str(Path(sys.executable).resolve())
        backup_exe = current_exe + ".bak"
        tmp_exe = str(
            Path(tempfile.gettempdir())
            / ("Bieu_Cat_Tao_Marker_Opitex_UPDATE_%d.exe" % os.getpid())
        )
        ps1_path = str(
            Path(tempfile.gettempdir())
            / ("QUANGLAN_VISIBLE_UPDATE_%d.ps1" % os.getpid())
        )

        ps_script = r'''param(
  [int]$PidToWait,
  [string]$Current,
  [string]$Backup,
  [string]$TempExe,
  [string]$DownloadUrl,
  [string]$ExpectedSha,
  [string]$RemoteVersion,
  [string]$SelfScript
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Net.Http

$form = New-Object System.Windows.Forms.Form
$form.Text = "QUANGLAN - Cập nhật phần mềm"
$form.StartPosition = "CenterScreen"
$form.Size = New-Object System.Drawing.Size(610,260)
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $true
$form.ShowInTaskbar = $true
$form.TopMost = $true
$form.ControlBox = $false
$form.BackColor = [System.Drawing.Color]::White

$header = New-Object System.Windows.Forms.Panel
$header.Dock = "Top"
$header.Height = 62
$header.BackColor = [System.Drawing.Color]::FromArgb(11,79,131)
$form.Controls.Add($header)

$title = New-Object System.Windows.Forms.Label
$title.Text = "ĐANG CẬP NHẬT PHẦN MỀM"
$title.Font = New-Object System.Drawing.Font("Segoe UI",14,[System.Drawing.FontStyle]::Bold)
$title.ForeColor = [System.Drawing.Color]::White
$title.AutoSize = $true
$title.Location = New-Object System.Drawing.Point(18,17)
$header.Controls.Add($title)

$status = New-Object System.Windows.Forms.Label
$status.Text = "BƯỚC 1/2 - Đang kết nối máy chủ..."
$status.Font = New-Object System.Drawing.Font("Segoe UI",10,[System.Drawing.FontStyle]::Bold)
$status.ForeColor = [System.Drawing.Color]::FromArgb(24,52,73)
$status.Location = New-Object System.Drawing.Point(28,84)
$status.Size = New-Object System.Drawing.Size(540,24)
$form.Controls.Add($status)

$detail = New-Object System.Windows.Forms.Label
$detail.Text = "Đang cập nhật lên V" + $RemoteVersion
$detail.Font = New-Object System.Drawing.Font("Segoe UI",9)
$detail.ForeColor = [System.Drawing.Color]::DimGray
$detail.Location = New-Object System.Drawing.Point(28,111)
$detail.Size = New-Object System.Drawing.Size(540,22)
$form.Controls.Add($detail)

$bar = New-Object System.Windows.Forms.ProgressBar
$bar.Location = New-Object System.Drawing.Point(28,143)
$bar.Size = New-Object System.Drawing.Size(540,25)
$bar.Minimum = 0
$bar.Maximum = 100
$bar.Value = 0
$form.Controls.Add($bar)

$pct = New-Object System.Windows.Forms.Label
$pct.Text = "0%"
$pct.Font = New-Object System.Drawing.Font("Segoe UI",9)
$pct.ForeColor = [System.Drawing.Color]::DimGray
$pct.Location = New-Object System.Drawing.Point(28,174)
$pct.Size = New-Object System.Drawing.Size(250,22)
$form.Controls.Add($pct)

$closeBtn = New-Object System.Windows.Forms.Button
$closeBtn.Text = "ĐÓNG"
$closeBtn.Enabled = $false
$closeBtn.Size = New-Object System.Drawing.Size(100,34)
$closeBtn.Location = New-Object System.Drawing.Point(468,185)
$closeBtn.Add_Click({ $form.Close() })
$form.Controls.Add($closeBtn)

$form.Show()
[System.Windows.Forms.Application]::DoEvents()

$client = $null
$response = $null
$stream = $null
$file = $null

try {
  $status.Text = "BƯỚC 1/2 - Đang tải phiên bản V" + $RemoteVersion + "..."
  [System.Windows.Forms.Application]::DoEvents()

  $client = New-Object System.Net.Http.HttpClient
  $client.Timeout = [TimeSpan]::FromMinutes(5)

  $response = $client.GetAsync(
      $DownloadUrl,
      [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead
  ).Result

  $response.EnsureSuccessStatusCode()

  [int64]$total = 0
  if ($response.Content.Headers.ContentLength) {
    $total = [int64]$response.Content.Headers.ContentLength
  }

  $stream = $response.Content.ReadAsStreamAsync().Result
  $file = [System.IO.File]::Open(
      $TempExe,
      [System.IO.FileMode]::Create,
      [System.IO.FileAccess]::Write,
      [System.IO.FileShare]::None
  )

  $buffer = New-Object byte[] (256KB)
  [int64]$readTotal = 0

  while (($read = $stream.Read($buffer,0,$buffer.Length)) -gt 0) {
    $file.Write($buffer,0,$read)
    $readTotal += $read

    if ($total -gt 0) {
      $percent = [int][Math]::Floor(($readTotal * 100.0) / $total)
      if ($percent -lt 0) { $percent = 0 }
      if ($percent -gt 100) { $percent = 100 }
      $bar.Value = $percent
      $pct.Text = "Đang tải... " + $percent + "%"
    } else {
      $mb = [Math]::Round($readTotal / 1MB, 1)
      $pct.Text = "Đã tải " + $mb + " MB"
    }

    [System.Windows.Forms.Application]::DoEvents()
  }

  $file.Close()
  $file = $null
  $stream.Close()
  $stream = $null
  $response.Dispose()
  $response = $null
  $client.Dispose()
  $client = $null

  $bar.Value = 100
  $pct.Text = "Tải hoàn tất - 100%"
  $status.Text = "BƯỚC 1/2 - Đang kiểm tra file cập nhật..."
  [System.Windows.Forms.Application]::DoEvents()

  if ($ExpectedSha) {
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $TempExe).Hash.ToLower()
    if ($actual -ne $ExpectedSha.ToLower()) {
      throw "SHA256 không khớp. Không cài bản cập nhật."
    }
  }

  $status.Text = "BƯỚC 2/2 - Đang cài đặt phiên bản mới..."
  $detail.Text = "Đang chờ phần mềm cũ đóng hoàn toàn..."
  $pct.Text = "Vui lòng chờ, không tắt máy."
  [System.Windows.Forms.Application]::DoEvents()

  try {
    Wait-Process -Id $PidToWait -ErrorAction SilentlyContinue
  } catch {}

  Start-Sleep -Seconds 5

  if (Test-Path -LiteralPath $Backup) {
    Remove-Item -Force -LiteralPath $Backup -ErrorAction SilentlyContinue
  }

  if (Test-Path -LiteralPath $Current) {
    Move-Item -Force -LiteralPath $Current -Destination $Backup
  }

  Copy-Item -Force -LiteralPath $TempExe -Destination $Current

  if (-not (Test-Path -LiteralPath $Current)) {
    throw "Không tìm thấy EXE mới sau khi thay file."
  }

  Start-Sleep -Seconds 2

  Remove-Item -Force -LiteralPath $TempExe -ErrorAction SilentlyContinue
  Remove-Item -Force -LiteralPath $Backup -ErrorAction SilentlyContinue

  $status.Text = "CẬP NHẬT HOÀN TẤT - V" + $RemoteVersion
  $detail.Text = "Đã cài xong. Hãy đóng cửa sổ này rồi mở lại phần mềm từ Desktop."
  $pct.Text = "Hoàn tất 100%"
  $bar.Value = 100
  $closeBtn.Enabled = $true
  $form.ControlBox = $true

  [System.Media.SystemSounds]::Asterisk.Play()
  [System.Windows.Forms.Application]::DoEvents()

  while ($form.Visible) {
    [System.Windows.Forms.Application]::DoEvents()
    Start-Sleep -Milliseconds 50
  }
}
catch {
  try { if ($file) { $file.Close() } } catch {}
  try { if ($stream) { $stream.Close() } } catch {}
  try { if ($response) { $response.Dispose() } } catch {}
  try { if ($client) { $client.Dispose() } } catch {}

  try {
    if ((Test-Path -LiteralPath $Backup) -and -not (Test-Path -LiteralPath $Current)) {
      Move-Item -Force -LiteralPath $Backup -Destination $Current
    }
  } catch {}

  try {
    Remove-Item -Force -LiteralPath $TempExe -ErrorAction SilentlyContinue
  } catch {}

  $status.Text = "CẬP NHẬT KHÔNG THÀNH CÔNG"
  $detail.Text = [string]$_.Exception.Message
  $pct.Text = "Bạn có thể đóng cửa sổ và mở lại phần mềm cũ."
  $closeBtn.Enabled = $true
  $form.ControlBox = $true

  [System.Media.SystemSounds]::Hand.Play()
  [System.Windows.Forms.Application]::DoEvents()

  while ($form.Visible) {
    [System.Windows.Forms.Application]::DoEvents()
    Start-Sleep -Milliseconds 50
  }
}

try {
  Remove-Item -Force -LiteralPath $SelfScript -ErrorAction SilentlyContinue
} catch {}
'''

        Path(ps1_path).write_text(ps_script, encoding="utf-8-sig")

        updater_args = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-WindowStyle",
            "Hidden",
            "-File",
            ps1_path,
            "-PidToWait",
            str(os.getpid()),
            "-Current",
            current_exe,
            "-Backup",
            backup_exe,
            "-TempExe",
            tmp_exe,
            "-DownloadUrl",
            download_url,
            "-ExpectedSha",
            expected_sha,
            "-RemoteVersion",
            remote_version,
            "-SelfScript",
            ps1_path,
        ]

        subprocess.Popen(
            updater_args,
            creationflags=_hidden_creationflags(),
            close_fds=True,
        )

        time.sleep(0.5)
        os._exit(0)

    except Exception:
        return False

    return False

def _load_embedded_module(key):
    try:
        return _MODULE_CACHE[key]
    except KeyError:
        raise KeyError("Module không hợp lệ: %s" % key)


def _hidden_creationflags():
    if os.name == "nt":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    return 0


def _self_command(*args):
    if _is_frozen():
        return [str(sys.executable), *args]
    # Dùng pythonw nếu đang chạy pythonw; nếu python thường thì giữ nguyên executable.
    return [str(sys.executable), str(Path(__file__).resolve()), *args]


def _run_embedded_module(key, passthrough=None):
    passthrough = list(passthrough or [])
    mod = _load_embedded_module(key)
    sys.argv = [str(_runtime_path()), *passthrough]

    if key == "serial":
        root = tk.Tk()
        root.title("In số thứ tự")
        root.geometry("900x620")
        root.minsize(760, 540)
        panel = mod.SerialNumberPanel(root)
        panel.pack(fill="both", expand=True)
        root._merged_app = panel
        root.mainloop()
        return

    if key == "cut":
        root = tk.Tk()
        app = mod.CuttingPlanApp(root)
        root._merged_app = app
        root.mainloop()
        return

    if key == "marker":
        root = tk.Tk()
        app = mod.App(root)
        root._merged_app = app
        if passthrough:
            p = passthrough[0]
            if str(p).lower().endswith(".xlsx") and hasattr(app, "excel_var"):
                try:
                    app.excel_var.set(p)
                except Exception:
                    pass
        root.mainloop()
        return

    if key == "tem":
        app = mod.App()
        app.mainloop()
        return

    raise ValueError("Module không hợp lệ: %s" % key)


class UpdateWindow(tk.Toplevel):
    def __init__(self, parent_app):
        super().__init__(parent_app.root)
        self.app = parent_app
        self.title("Cập nhật phần mềm")
        self.geometry("660x430")
        self.minsize(600, 390)
        self.configure(bg="white")
        self.transient(parent_app.root)
        self.grab_set()
        self._build()
        self.after(150, lambda: self.app.check_updates(manual=True, dialog=self))

    def _build(self):
        top = tk.Frame(self, bg="#0b4f83", height=62)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="↻  CẬP NHẬT PHẦN MỀM", font=("Segoe UI", 15, "bold"), fg="white", bg="#0b4f83").pack(side="left", padx=18, pady=15)
        tk.Label(top, text="V" + APP_VERSION, font=("Segoe UI", 9, "bold"), fg="white", bg="#2375c6", padx=9, pady=5).pack(side="right", padx=16)

        frm = tk.Frame(self, bg="white")
        frm.pack(fill="both", expand=True, padx=20, pady=15)

        self.state_var = tk.StringVar(value="Đang kiểm tra...")
        tk.Label(frm, textvariable=self.state_var, font=("Segoe UI", 11, "bold"), fg="#183449", bg="white", anchor="w").pack(fill="x")

        self.info = tk.Text(frm, height=10, wrap="word", font=("Segoe UI", 9), bd=1, relief="solid")
        self.info.pack(fill="both", expand=True, pady=(10, 12))
        self.info.insert("1.0", "Phiên bản hiện tại: %s\n" % APP_VERSION)
        self.info.configure(state="disabled")

        cfg = self.app.update_config
        self.auto_var = tk.BooleanVar(value=bool(cfg.get("auto_check", True)))
        auto = tk.Checkbutton(frm, text="Tự động kiểm tra cập nhật khi mở phần mềm", variable=self.auto_var, bg="white", command=self._save_auto)
        auto.pack(anchor="w")

        row = tk.Frame(frm, bg="white")
        row.pack(fill="x", pady=(10, 0))
        tk.Button(row, text="CẤU HÌNH MÁY CHỦ", command=self._configure_url, bg="#64748b", fg="white", relief="flat", padx=12, pady=7).pack(side="left")
        self.update_btn = tk.Button(row, text="CẬP NHẬT NGAY", command=self._do_update, state="disabled", bg="#15945b", fg="white", disabledforeground="#d7e4dc", relief="flat", padx=16, pady=7)
        self.update_btn.pack(side="right")
        tk.Button(row, text="KIỂM TRA LẠI", command=lambda: self.app.check_updates(manual=True, dialog=self), bg="#2375c6", fg="white", relief="flat", padx=14, pady=7).pack(side="right", padx=8)

    def _save_auto(self):
        self.app.update_config["auto_check"] = bool(self.auto_var.get())
        _save_update_config(self.app.update_config)

    def _configure_url(self):
        old = str(self.app.update_config.get("manifest_url", "") or "")
        value = simpledialog.askstring(
            "Máy chủ cập nhật",
            "Nhập URL file version.json / update.json trên VPS:\n\nVí dụ: https://tenmien.vn/update/version.json",
            initialvalue=old,
            parent=self,
        )
        if value is None:
            return
        value = value.strip()
        self.app.update_config["manifest_url"] = value
        _save_update_config(self.app.update_config)
        self.state_var.set("Đã lưu máy chủ cập nhật.")
        self.app.check_updates(manual=True, dialog=self)

    def set_result(self, result):
        self.info.configure(state="normal")
        self.info.delete("1.0", "end")
        if result.get("error"):
            self.state_var.set("Không kiểm tra được cập nhật")
            self.info.insert("1.0", "Phiên bản hiện tại: %s\n\n%s" % (APP_VERSION, result["error"]))
            self.update_btn.config(state="disabled")
        elif not result.get("configured"):
            self.state_var.set("Chưa cấu hình máy chủ cập nhật")
            self.info.insert("1.0", "Phiên bản hiện tại: %s\n\nHãy bấm CẤU HÌNH MÁY CHỦ và nhập URL version.json trên VPS." % APP_VERSION)
            self.update_btn.config(state="disabled")
        elif result.get("newer"):
            self.state_var.set("Có phiên bản mới: %s" % result.get("version"))
            notes = result.get("notes") or "Không có ghi chú phiên bản."
            self.info.insert("1.0", "Phiên bản hiện tại: %s\nPhiên bản mới: %s\n\nNỘI DUNG:\n%s" % (APP_VERSION, result.get("version"), notes))
            self.update_btn.config(state="normal")
        else:
            self.state_var.set("Bạn đang dùng phiên bản mới nhất")
            self.info.insert("1.0", "Phiên bản hiện tại: %s\n\nKhông có bản cập nhật mới." % APP_VERSION)
            self.update_btn.config(state="disabled")
        self.info.configure(state="disabled")

    def _do_update(self):
        manifest = self.app.last_manifest or {}
        if not manifest.get("download_url"):
            messagebox.showerror("Thiếu link", "Máy chủ chưa cung cấp download_url.", parent=self)
            return
        self.update_btn.config(state="disabled")
        self.state_var.set("Đang tải phiên bản mới...")
        self.app.download_and_apply_update(manifest, dialog=self)


class CombinedApp:
    def __init__(self, root, license_context=None):
        self.root = root
        self.license_context = dict(license_context or {})
        self.root.title(APP_TITLE)
        self.root.geometry("1180x720")
        self.root.minsize(920, 580)
        self.root.configure(bg="#eef3f8")
        self.update_config = _load_update_config()
        self.last_manifest = None
        self.child_processes = []
        self.license_state = _load_license_state()
        if self.license_context.get("access_type") == "trial":
            remaining = int(self.license_context.get("remaining_seconds", 0) or 0)
            hours = max(1, int(math.ceil(remaining / 3600.0))) if remaining > 0 else 0
            status_text = "Sẵn sàng | DÙNG THỬ: còn khoảng %s giờ | V%s" % (hours, APP_VERSION)
        elif self.license_context.get("access_type") == "free":
            status_text = "Sẵn sàng | CHẾ ĐỘ MIỄN PHÍ (Key đang tắt trên Web) | V%s" % APP_VERSION
        else:
            status_text = "Sẵn sàng | Bản quyền: ACTIVE | V%s" % APP_VERSION
        self.status_var = tk.StringVar(value=status_text)
        self._build_styles()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        # Kiểm tra phiên bản chỉ chạy khi người dùng mở menu CẬP NHẬT.

    def _build_styles(self):
        style = ttk.Style()
        try: style.theme_use("clam")
        except Exception: pass
        style.configure("Top.TButton", font=("Segoe UI", 9, "bold"), padding=(13, 10))

    def _build_ui(self):
        header = tk.Frame(self.root, bg="#0b4f83", height=62)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        brand = tk.Frame(header, bg="#176da6", width=230)
        brand.pack(side="left", fill="y")
        brand.pack_propagate(False)
        tk.Label(brand, text="✂  TÁC NGHIỆP CẮT", font=("Segoe UI", 13, "bold"), fg="white", bg="#176da6").pack(anchor="w", padx=12, pady=(10,0))
        tk.Label(brand, text="CUTTING PLAN SUITE", font=("Segoe UI", 7), fg="#d8efff", bg="#176da6").pack(anchor="w", padx=35)

        nav = tk.Frame(header, bg="#0b4f83")
        nav.pack(side="left", fill="both", expand=True)
        items = [
            ("TÁC NGHIỆP CẮT", "cut", "#2375c6"),
            ("TẠO MARKER", "marker", "#15945b"),
            ("PHÂN SỐ TEM", "tem", "#6f42c1"),
            ("IN SỐ TT", "serial", "#d17b22"),
        ]
        for text, key, color in items:
            tk.Button(nav, text=text, command=lambda k=key: self.open_module(k), font=("Segoe UI", 9, "bold"), bg="#0b4f83", fg="white", activebackground=color, activeforeground="white", relief="flat", bd=0, padx=16, cursor="hand2").pack(side="left", fill="y")

        tk.Button(header, text="↻  CẬP NHẬT", command=self.open_update_window, font=("Segoe UI", 9, "bold"), bg="#073f6c", fg="white", activebackground="#2375c6", activeforeground="white", relief="flat", bd=0, padx=15, cursor="hand2").pack(side="right", fill="y")

        license_btn_text = (
            "DÙNG THỬ" if self.license_context.get("access_type") == "trial"
            else ("MIỄN PHÍ" if self.license_context.get("access_type") == "free" else "BẢN QUYỀN")
        )
        self.license_btn = tk.Button(
            header,
            text=license_btn_text,
            command=self.open_license_info,
            font=("Segoe UI", 9, "bold"),
            bg="#0a5d52",
            fg="white",
            activebackground="#15945b",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=13,
            cursor="hand2",
        )
        self.license_btn.pack(side="right", fill="y")

        # V2.0.11: nút NHẬP KEY luôn hiện để khách có thể kích hoạt/đổi key bất cứ lúc nào.
        self.enter_key_btn = tk.Button(
            header,
            text="NHẬP KEY",
            command=self.enter_license_key,
            font=("Segoe UI", 9, "bold"),
            bg="#15945b",
            fg="white",
            activebackground="#117847",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=15,
            cursor="hand2",
        )
        if self.license_context.get("access_type") != "free":
            self.enter_key_btn.pack(side="right", fill="y")

        tk.Label(header, text="V"+APP_VERSION, font=("Segoe UI", 8, "bold"), bg="#5b8ff9", fg="white", padx=7, pady=4).pack(side="right", padx=6)

        body = tk.Frame(self.root, bg="#eef3f8")
        body.pack(fill="both", expand=True, padx=30, pady=25)
        tk.Label(body, text="HỆ THỐNG TỔNG HỢP", font=("Segoe UI", 20, "bold"), fg="#183449", bg="#eef3f8").pack(anchor="w")
        tk.Label(body, text="Một EXE • Bốn chức năng • Có cơ chế cập nhật phiên bản", font=("Segoe UI", 10), fg="#63788a", bg="#eef3f8").pack(anchor="w", pady=(2,18))

        cards = tk.Frame(body, bg="#eef3f8")
        cards.pack(fill="both", expand=True)
        for i in range(4): cards.grid_columnconfigure(i, weight=1, uniform="card")
        cards.grid_rowconfigure(0, weight=1)
        self._card(cards, 0, "①", "TÁC NGHIỆP CẮT", "PO • Loại vải • LOT/Cây • Biểu cắt • Form 10 • Excel", "#2375c6", lambda:self.open_module("cut"))
        self._card(cards, 1, "②", "TẠO MARKER OPTITEX", "Đọc Excel • Chọn bàn • Tạo marker bằng Optitex", "#15945b", lambda:self.open_module("marker"))
        self._card(cards, 2, "③", "PHÂN SỐ TEM", "Tên chi tiết • Loại vải • Dải số bàn • Xuất Excel tem", "#6f42c1", lambda:self.open_module("tem"))
        self._card(cards, 3, "④", "IN SỐ TT", "Đánh số tem nhiều cỡ • Xuất Excel A4 ngang", "#d17b22", lambda:self.open_module("serial"))

        bottom = tk.Frame(self.root, bg="#dfe8f0", height=32)
        bottom.pack(fill="x", side="bottom")
        bottom.pack_propagate(False)
        tk.Label(bottom, textvariable=self.status_var, bg="#dfe8f0", fg="#52687a", font=("Segoe UI", 8), anchor="w", padx=10).pack(fill="both", expand=True)

    def _card(self, parent, col, icon, title, desc, color, cmd):
        card = tk.Frame(parent, bg="white", highlightthickness=1, highlightbackground="#d5e0ea")
        card.grid(row=0, column=col, sticky="nsew", padx=8, pady=4)
        bar = tk.Frame(card, bg=color, height=7); bar.pack(fill="x"); bar.pack_propagate(False)
        inner = tk.Frame(card, bg="white"); inner.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(inner, text=icon, font=("Segoe UI", 32, "bold"), fg=color, bg="white").pack(anchor="w")
        tk.Label(inner, text=title, font=("Segoe UI", 13, "bold"), fg="#183449", bg="white").pack(anchor="w", pady=(12,8))
        tk.Label(inner, text=desc, font=("Segoe UI", 9), fg="#516574", bg="white", justify="left", wraplength=290).pack(anchor="w", fill="x")
        tk.Button(inner, text="MỞ CHỨC NĂNG", command=cmd, font=("Segoe UI", 10, "bold"), bg=color, fg="white", activebackground=color, activeforeground="white", relief="flat", bd=0, pady=10, cursor="hand2").pack(side="bottom", fill="x")

    def open_module(self, key):
        labels = {"cut":"Tác nghiệp cắt", "marker":"Tạo Marker Optitex", "tem":"Phân số tem", "serial":"In số TT"}
        try:
            cmd = _self_command("--module", key)
            p = subprocess.Popen(cmd, cwd=str(_runtime_dir()), creationflags=_hidden_creationflags())

            self.child_processes = [x for x in self.child_processes if x.poll() is None]
            self.child_processes.append(p)

            self.status_var.set("Đã mở: %s | V%s" % (labels.get(key,key), APP_VERSION))

            # Khi mở một chức năng, tự hạ cửa sổ tổng hợp xuống Taskbar.
            try:
                self.root.after(150, self.root.iconify)
            except Exception:
                pass

            # Theo dõi tiến trình chức năng. Khi tắt chức năng cuối cùng,
            # cửa sổ tổng hợp sẽ tự mở trở lại.
            self._watch_module_process(p, labels.get(key, key))

        except Exception as exc:
            messagebox.showerror(
                "Không mở được",
                "%s\n\n%s" % (labels.get(key,key), exc),
                parent=self.root
            )

    def _watch_module_process(self, process, label):
        try:
            if process.poll() is None:
                self.root.after(
                    400,
                    lambda p=process, name=label: self._watch_module_process(p, name)
                )
                return
        except Exception:
            pass

        # Loại các tiến trình đã đóng khỏi danh sách.
        try:
            self.child_processes = [
                x for x in self.child_processes
                if x.poll() is None
            ]
        except Exception:
            self.child_processes = []

        # Chỉ mở lại cửa sổ tổng hợp khi không còn chức năng nào đang chạy.
        if not self.child_processes:
            try:
                self.root.deiconify()
                self.root.state("normal")
                self.root.lift()
                self.root.after(100, self.root.focus_force)
            except Exception:
                pass

            try:
                self.status_var.set(
                    "Đã đóng: %s | Sẵn sàng | V%s" % (label, APP_VERSION)
                )
            except Exception:
                pass

    def enter_license_key(self):
        """Nhập key bất cứ lúc nào: trial hoặc đã có bản quyền."""
        if self.license_context.get("access_type") == "trial":
            message = "Bạn đang dùng thử. Nhập key để chuyển sang bản quyền ngay."
        else:
            message = (
                "Nhập key bản quyền.\n"
                "Nếu nhập key khác, key mới phải hợp lệ và sẽ được gắn với máy này."
            )

        win = LicenseActivationWindow(initial_error=message)
        if not win.run():
            return

        result = _verify_saved_license()
        if not result.get("ok"):
            messagebox.showerror(
                "Chưa kích hoạt",
                str(result.get("error") or "Không xác minh được key."),
                parent=self.root,
            )
            return

        result["access_type"] = "license"
        self.license_context = result
        self.license_state = _load_license_state()
        self.status_var.set("Sẵn sàng | Bản quyền: ACTIVE | V%s" % APP_VERSION)

        try:
            self.license_btn.config(text="BẢN QUYỀN")
        except Exception:
            pass

        state = _load_license_state()
        expires = state.get("expires_at") or "Không giới hạn"
        messagebox.showinfo(
            "Kích hoạt thành công",
            "Key đã được kích hoạt trên máy này.\n\nHạn sử dụng: %s" % expires,
            parent=self.root,
        )


    def open_license_info(self):
        if self.license_context.get("access_type") == "free":
            policy = self.license_context.get("policy") or {}
            msg = (
                "Trạng thái: MIỄN PHÍ\n"
                "Yêu cầu Key: ĐANG TẮT trên website\n"
                "Sản phẩm: %s\n"
                "Cập nhật cấu hình: %s\n\n"
                "Phần mềm sẽ đọc lại cấu hình bản quyền ở lần mở tiếp theo."
            ) % (
                LICENSE_PRODUCT_CODE,
                policy.get("updated_at") or "—",
            )
            messagebox.showinfo("Trạng thái sử dụng", msg, parent=self.root)
            return

        if self.license_context.get("access_type") == "trial":
            remaining = int(self.license_context.get("remaining_seconds", 0) or 0)
            hours = max(0, int(math.ceil(remaining / 3600.0)))
            expires = self.license_context.get("expires_at") or "—"
            msg = (
                "Trạng thái: DÙNG THỬ MIỄN PHÍ\n"
                "Thời gian: 1 ngày / mỗi máy 1 lần\n"
                "Còn khoảng: %s giờ\n"
                "Kết thúc: %s\n"
                "Mã thiết bị trial: %s\n\n"
                "Bạn có thể bấm NHẬP KEY trên thanh trên cùng để kích hoạt ngay."
            ) % (hours, expires, _trial_machine_code_short())
            messagebox.showinfo("Dùng thử phần mềm", msg, parent=self.root)
            return

        state = _load_license_state()
        key = str(state.get("key", "") or "")
        expires = state.get("expires_at") or "Không giới hạn"
        last_verified = state.get("last_verified") or "Chưa có"
        msg = (
            "Trạng thái: ACTIVE\n"
            "Key: %s\n"
            "Mã thiết bị: %s\n"
            "Hạn sử dụng: %s\n"
            "Xác minh gần nhất: %s\n\n"
            "Key đã tự gắn với máy này trên server."
        ) % (_mask_key(key), _machine_code_short(), expires, last_verified)
        messagebox.showinfo("Bản quyền phần mềm", msg, parent=self.root)


    def open_update_window(self):
        UpdateWindow(self)

    def _fetch_manifest(self):
        url = str(self.update_config.get("manifest_url") or DEFAULT_UPDATE_MANIFEST_URL or "").strip()
        if not url:
            return {"configured": False}
        req = urllib.request.Request(url, headers={"User-Agent": "%s/%s" % (APP_NAME, APP_VERSION)})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read(1024 * 1024)
        data = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError("version.json không đúng định dạng JSON object")
        version = str(data.get("version") or "").strip()
        if not version:
            raise ValueError("version.json thiếu trường version")
        download_url = str(data.get("download_url") or data.get("url") or "").strip()
        result = {
            "configured": True,
            "version": version,
            "download_url": download_url,
            "sha256": str(data.get("sha256") or "").strip().lower(),
            "required": bool(data.get("required", False)),
            "notes": str(data.get("notes") or data.get("note") or ""),
            "newer": _is_newer(version),
        }
        self.last_manifest = result
        return result

    def check_updates(self, manual=False, dialog=None):
        if manual:
            self.status_var.set("Đang kiểm tra cập nhật...")
        def worker():
            try:
                result = self._fetch_manifest()
            except Exception as exc:
                result = {"error": str(exc), "configured": True}
            def finish():
                if dialog is not None and dialog.winfo_exists():
                    dialog.set_result(result)
                if result.get("newer"):
                    self.status_var.set("Có phiên bản mới: %s" % result.get("version"))
                    if dialog is None:
                        required = bool(result.get("required"))
                        msg = "Có phiên bản mới %s.\n\n%s" % (result.get("version"), result.get("notes") or "")
                        if messagebox.askyesno("Có bản cập nhật", msg + "\n\nMở màn hình cập nhật?", parent=self.root):
                            self.open_update_window()
                        elif required:
                            messagebox.showwarning("Cập nhật bắt buộc", "Phiên bản này được đánh dấu bắt buộc cập nhật.", parent=self.root)
                elif result.get("error") and manual:
                    self.status_var.set("Lỗi kiểm tra cập nhật")
                elif manual:
                    self.status_var.set("Đã kiểm tra cập nhật | V%s" % APP_VERSION)
            self.root.after(0, finish)
        threading.Thread(target=worker, daemon=True).start()

    def _alive_children(self):
        alive = []
        for proc in self.child_processes:
            try:
                if proc.poll() is None:
                    alive.append(proc)
            except Exception:
                pass
        self.child_processes = alive
        return alive

    def download_and_apply_update(self, manifest, dialog=None):
        if self._alive_children():
            messagebox.showwarning(
                "Hãy đóng các chức năng đang mở",
                "Trước khi cập nhật, hãy LƯU dữ liệu rồi đóng các cửa sổ:\n"
                "- Tác nghiệp cắt\n- Tạo Marker\n- Phân số tem\n\n"
                "Sau đó bấm CẬP NHẬT NGAY lại. Điều này tránh Windows khóa file EXE.",
                parent=dialog or self.root
            )
            if dialog is not None and dialog.winfo_exists():
                dialog.update_btn.config(state="normal")
                dialog.state_var.set("Đang chờ đóng các chức năng")
            return

        def worker():
            tmp_path = None
            try:
                url = str(manifest.get("download_url") or "").strip()
                if not url:
                    raise ValueError("Thiếu download_url")
                suffix = ".exe" if url.lower().split("?")[0].endswith(".exe") else ".bin"
                fd, name = tempfile.mkstemp(prefix="CuttingPlan_Update_", suffix=suffix)
                os.close(fd)
                tmp_path = Path(name)
                req = urllib.request.Request(url, headers={"User-Agent":"%s/%s"%(APP_NAME,APP_VERSION)})
                with urllib.request.urlopen(req, timeout=60) as resp, open(tmp_path, "wb") as f:
                    total = int(resp.headers.get("Content-Length") or 0)
                    got = 0
                    while True:
                        chunk = resp.read(1024*512)
                        if not chunk: break
                        f.write(chunk); got += len(chunk)
                        if dialog is not None and total > 0:
                            pct = int(got*100/total)
                            self.root.after(0, lambda p=pct: dialog.state_var.set("Đang tải... %d%%"%p) if dialog.winfo_exists() else None)
                expected = str(manifest.get("sha256") or "").lower().strip()
                if expected:
                    h=hashlib.sha256()
                    with open(tmp_path,"rb") as f:
                        for chunk in iter(lambda:f.read(1024*1024), b""): h.update(chunk)
                    actual=h.hexdigest().lower()
                    if actual != expected:
                        raise ValueError("SHA256 không khớp. File cập nhật có thể bị lỗi hoặc không đúng phiên bản.")
                if not _is_frozen():
                    raise RuntimeError("Chế độ chạy .pyw chỉ kiểm tra/tải được. Hãy build EXE trước để dùng tự cập nhật.")
                self.root.after(0, lambda: self._schedule_replace_exe(tmp_path, manifest, dialog))
            except Exception as exc:
                if tmp_path:
                    try: tmp_path.unlink(missing_ok=True)
                    except Exception: pass
                def showerr():
                    if dialog is not None and dialog.winfo_exists():
                        dialog.state_var.set("Cập nhật thất bại")
                        dialog.update_btn.config(state="normal")
                    messagebox.showerror("Lỗi cập nhật", str(exc), parent=dialog or self.root)
                self.root.after(0, showerr)
        threading.Thread(target=worker, daemon=True).start()

    def _schedule_replace_exe(self, new_exe, manifest, dialog=None):
        if not _is_frozen():
            return
        if self._alive_children():
            try:
                Path(new_exe).unlink(missing_ok=True)
            except Exception:
                pass
            if dialog is not None and dialog.winfo_exists():
                dialog.update_btn.config(state="normal")
                dialog.state_var.set("Cần đóng các chức năng đang mở")
            messagebox.showwarning(
                "Chưa thể thay EXE",
                "Một chức năng vẫn đang mở. Hãy lưu dữ liệu, đóng tất cả cửa sổ chức năng rồi cập nhật lại.",
                parent=dialog or self.root
            )
            return

        current = Path(sys.executable).resolve()
        backup = current.with_suffix(current.suffix + ".bak")
        ps1 = Path(tempfile.gettempdir()) / ("CuttingPlan_Update_%d.ps1" % os.getpid())
        remote_version = str(manifest.get("version") or "").strip()

        script = r'''param([int]$PidToWait,[string]$Current,[string]$New,[string]$Backup,[string]$SelfScript,[string]$RemoteVersion)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms

try { Wait-Process -Id $PidToWait -ErrorAction SilentlyContinue } catch {}
Start-Sleep -Seconds 10

try {
  if (Test-Path $Backup) {
    Remove-Item -Force $Backup -ErrorAction SilentlyContinue
  }

  if (Test-Path $Current) {
    Move-Item -Force $Current $Backup
  }

  Copy-Item -Force $New $Current

  if (-not (Test-Path $Current)) {
    throw "Khong thay file EXE moi sau khi copy."
  }

  Start-Sleep -Seconds 5

  Remove-Item -Force $New -ErrorAction SilentlyContinue
  Remove-Item -Force $Backup -ErrorAction SilentlyContinue

  [System.Windows.Forms.MessageBox]::Show(
    "Cap nhat V$RemoteVersion da hoan tat.`n`nHay mo lai QUANGLAN SOFTWARE tu icon Desktop.",
    "QUANGLAN - Cap nhat xong",
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Information
  ) | Out-Null
}
catch {
  try {
    if (Test-Path $Current) {
      Remove-Item -Force $Current -ErrorAction SilentlyContinue
    }
    if (Test-Path $Backup) {
      Move-Item -Force $Backup $Current
    }
  } catch {}

  try { Remove-Item -Force $New -ErrorAction SilentlyContinue } catch {}

  [System.Windows.Forms.MessageBox]::Show(
    "Cap nhat khong thanh cong.`n`nDa phuc hoi ban cu neu co.`n`n" + $_.Exception.Message,
    "QUANGLAN - Loi cap nhat",
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Error
  ) | Out-Null
}

try { Remove-Item -Force $SelfScript -ErrorAction SilentlyContinue } catch {}
'''
        ps1.write_text(script, encoding="utf-8-sig")
        args = [
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden",
            "-File", str(ps1),
            "-PidToWait", str(os.getpid()),
            "-Current", str(current),
            "-New", str(new_exe),
            "-Backup", str(backup),
            "-SelfScript", str(ps1),
            "-RemoteVersion", remote_version,
        ]
        subprocess.Popen(args, creationflags=_hidden_creationflags(), close_fds=True)

        messagebox.showinfo(
            "Cập nhật",
            "Đã tải xong phiên bản %s.\\n\\n"
            "Phần mềm sẽ đóng để thay EXE.\\n"
            "Hãy CHỜ thông báo 'CẬP NHẬT XONG', sau đó mở lại phần mềm từ icon Desktop.\\n\\n"
            "Bản này không tự mở lại EXE để tránh lỗi python315.dll."
            % remote_version,
            parent=dialog or self.root
        )
        self.root.after(200, self._close_for_update)

    def _close_for_update(self):
        try: self.root.destroy()
        finally: os._exit(0)

    def _close(self):
        try: self.root.destroy()
        except Exception: pass


def main():
    args = sys.argv[1:]

    # Không gọi máy chủ khi khởi động. Chỉ kết nối máy chủ khi người dùng
    # mở chức năng CẬP NHẬT để kiểm tra/tải phiên bản mới.

    # Sau đó mới kiểm tra bản quyền.
    license_result = _ensure_license_or_prompt()
    if not license_result.get("ok"):
        return

    if len(args) >= 2 and args[0] == "--module":
        key = args[1]
        try:
            _run_embedded_module(key, args[2:])
        except Exception as exc:
            try:
                root = tk.Tk(); root.withdraw()
                messagebox.showerror("Lỗi module", "%s\n\n%s" % (exc, traceback.format_exc()[-5000:]))
                root.destroy()
            except Exception:
                pass
        return

    root = tk.Tk()
    CombinedApp(root, license_context=license_result)
    root.mainloop()


if __name__ == "__main__":
    main()
