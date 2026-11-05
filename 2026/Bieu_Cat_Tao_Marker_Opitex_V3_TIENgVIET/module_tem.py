import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import os
import subprocess
import tempfile
import base64
import zlib
import atexit
import re
import html


# ============================================================
# ĐỌC PDS OPTITEX: TÊN CHI TIẾT + MATERIAL
# Dùng bridge C# tương tự module Marker, nhưng chỉ đọc dữ liệu.
# ============================================================

CSC = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
_PDS_READER_TEMP_DIR = Path(tempfile.gettempdir()) / ("OptitexTemPdsReader_" + str(os.getpid()))
_PDS_READER_CS = _PDS_READER_TEMP_DIR / "OptitexTemPdsReader.cs"
_PDS_READER_EXE = _PDS_READER_TEMP_DIR / "OptitexTemPdsReader.exe"

_PDS_ENGINE_PAYLOAD = """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"""


def _cleanup_pds_reader():
    for p in (_PDS_READER_CS, _PDS_READER_EXE):
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass
    try:
        _PDS_READER_TEMP_DIR.rmdir()
    except Exception:
        pass


atexit.register(_cleanup_pds_reader)


def _hidden_run(cmd, **kwargs):
    if os.name == "nt":
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | getattr(
            subprocess, "CREATE_NO_WINDOW", 0x08000000
        )
    return subprocess.run(cmd, **kwargs)


def _compile_pds_reader():
    if _PDS_READER_EXE.exists():
        return

    if not Path(CSC).exists():
        raise FileNotFoundError(
            "Không tìm thấy bộ biên dịch .NET CSC:\n"
            + CSC
            + "\n\nMáy cần Windows .NET Framework 4.x để đọc PDS."
        )

    _PDS_READER_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        source = zlib.decompress(base64.b64decode(_PDS_ENGINE_PAYLOAD)).decode("utf-8")
        _PDS_READER_CS.write_text(source, encoding="utf-8")

        cmd = [
            CSC,
            "/nologo",
            "/unsafe",
            "/platform:x64",
            "/optimize+",
            "/out:" + str(_PDS_READER_EXE),
            str(_PDS_READER_CS),
        ]
        p = _hidden_run(
            cmd,
            cwd=str(_PDS_READER_TEMP_DIR),
            capture_output=True,
            text=True,
            errors="replace",
        )
        if p.returncode != 0 or not _PDS_READER_EXE.exists():
            raise RuntimeError(
                "Biên dịch bộ đọc PDS thất bại:\n"
                + (p.stdout or "")
                + "\n"
                + (p.stderr or "")
            )
    finally:
        try:
            if _PDS_READER_CS.exists():
                _PDS_READER_CS.unlink()
        except Exception:
            pass


def _decode_pds_xml_field(value):
    """Giải mã text trong vùng metadata của PDS."""
    value = str(value or "").strip()
    if not value:
        return ""

    raw = bytearray()
    pos = 0
    had_byte_entity = False

    for m in re.finditer(r"&#(\\d+);", value):
        raw.extend(value[pos:m.start()].encode("latin1", errors="replace"))
        try:
            n = int(m.group(1))
        except Exception:
            n = -1
        if 0 <= n <= 255:
            raw.append(n)
            had_byte_entity = True
        else:
            raw.extend(m.group(0).encode("latin1", errors="replace"))
        pos = m.end()

    raw.extend(value[pos:].encode("latin1", errors="replace"))

    if had_byte_entity:
        for enc in ("utf-8", "gb18030", "cp936", "latin1"):
            try:
                return html.unescape(raw.decode(enc)).strip()
            except Exception:
                pass

    try:
        return html.unescape(raw.decode("utf-8")).strip()
    except Exception:
        return html.unescape(raw.decode("latin1", errors="replace")).strip()


def _read_piece_materials_direct_from_pds(pds_path):
    """Đọc NAME + MATERIAL trực tiếp từ PDS, không cần cài Optitex."""
    data = Path(pds_path).read_bytes()
    blob = data.decode("latin1", errors="ignore")

    piece_blocks = re.findall(
        r"<PIECE>(.*?)</PIECE>",
        blob,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not piece_blocks:
        return []

    pairs = []
    seen = set()
    for block in piece_blocks:
        m_name = re.search(r"<NAME>(.*?)</NAME>", block, flags=re.IGNORECASE | re.DOTALL)
        m_material = re.search(r"<MATERIAL>(.*?)</MATERIAL>", block, flags=re.IGNORECASE | re.DOTALL)

        detail = _decode_pds_xml_field(m_name.group(1) if m_name else "")
        material = _decode_pds_xml_field(m_material.group(1) if m_material else "")

        key = (detail.casefold(), material.casefold())
        if (detail or material) and key not in seen:
            seen.add(key)
            pairs.append((detail, material))
    return pairs


def read_piece_materials_from_pds(pds_path):
    """Trả về danh sách (Tên chi tiết, Material) từ file PDS.

    Ưu tiên đọc trực tiếp nên máy không cần cài Optitex.
    Nếu gặp biến thể PDS khác thì mới thử bridge Optitex cũ.
    """
    pds = Path(pds_path)
    if not pds.is_file():
        raise FileNotFoundError("Không tìm thấy file PDS:\\n" + str(pds))

    try:
        direct_pairs = _read_piece_materials_direct_from_pds(pds)
        if direct_pairs:
            return direct_pairs
    except Exception:
        pass

    try:
        _compile_pds_reader()
    except Exception as exc:
        raise RuntimeError(
            "File PDS này không đọc trực tiếp được và máy cũng không có "
            "bộ đọc Optitex dự phòng.\\n\\n" + str(exc)
        )

    p = _hidden_run(
        [str(_PDS_READER_EXE), "--list-pieces-materials", str(pds)],
        capture_output=True,
        text=True,
        errors="replace",
    )
    output = (p.stdout or "") + ("\\n" + p.stderr if p.stderr else "")

    pairs = []
    seen = set()
    for line in output.splitlines():
        if not line.startswith("PDS_PAIR_B64="):
            continue
        raw = line.split("=", 1)[1].strip()
        if "|" not in raw:
            continue
        a, b = raw.split("|", 1)
        try:
            detail = base64.b64decode(a).decode("utf-8", errors="replace").strip()
            material = base64.b64decode(b).decode("utf-8", errors="replace").strip()
        except Exception:
            continue
        key = (detail.casefold(), material.casefold())
        if (detail or material) and key not in seen:
            seen.add(key)
            pairs.append((detail, material))

    if p.returncode != 0 or not pairs:
        tail = "\\n".join(output.splitlines()[-35:])
        raise RuntimeError(
            "Không đọc được Tên chi tiết / Material từ PDS.\\n\\n"
            "File này có thể là biến thể PDS khác với mẫu đã hỗ trợ.\\n\\n"
            + tail
        )
    return pairs


try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Side, PatternFill, Font
    from openpyxl.utils import get_column_letter
except ImportError:
    raise SystemExit("Thiếu thư viện openpyxl. Hãy chạy: pip install openpyxl")


class EditablePasteGrid(ttk.Frame):
    """
    Bảng nhập 2 cột gần giống Excel.
    - Dán riêng từng cột bằng Ctrl+V.
    - Có thể dán 2 cột cùng lúc nếu bắt đầu từ cột TÊN CHI TIẾT.
    - Double-click để sửa ô.
    - Hover một dòng: cả 2 cột sáng nhẹ.
    - Click vào ô nào: ô bên đó trở về nền trắng để biết cột đang dán.
    - Luôn duy trì đúng 1 dòng trống cuối bảng.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._counter = 0
        self._active_col = 0  # 0 = chi tiết, 1 = loại vải
        self._active_iid = None
        self._hover_iid = None
        self._editor = None
        self._editor_tree = None
        self._editor_iid = None
        self._selected_cells = set()  # {(col, iid), ...}
        self._drag_start = None
        self._drag_col = None

        style = ttk.Style(self)
        for name in ("DetailGrid.Treeview", "FabricGrid.Treeview"):
            style.configure(
                name,
                rowheight=28,
                borderwidth=0,
                relief="flat",
                background="#FFFFFF",
                fieldbackground="#FFFFFF",
            )
            # Khi click/selected không dùng màu xanh mặc định.
            style.map(
                name,
                background=[("selected", "#FFFFFF")],
                foreground=[("selected", "#000000")],
            )
        style.configure("GridHead.Treeview.Heading", relief="solid", borderwidth=1)

        body = ttk.Frame(self)
        body.grid(row=0, column=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Cho phép kéo thay đổi độ rộng giữa 2 cột.
        self.hpane = ttk.Panedwindow(body, orient="horizontal")
        self.hpane.grid(row=0, column=0, sticky="nsew")
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)

        left = tk.Frame(self.hpane, bd=0, highlightthickness=1, highlightbackground="#C7CDD4", background="#FFFFFF")
        right = tk.Frame(self.hpane, bd=0, highlightthickness=1, highlightbackground="#C7CDD4", background="#FFFFFF")
        self.hpane.add(left, weight=3)
        self.hpane.add(right, weight=2)

        self.detail_tree = ttk.Treeview(
            left,
            columns=("value",),
            show="headings",
            selectmode="extended",
            style="DetailGrid.Treeview",
        )
        self.fabric_tree = ttk.Treeview(
            right,
            columns=("value",),
            show="headings",
            selectmode="extended",
            style="FabricGrid.Treeview",
        )

        self.detail_tree.heading("value", text="TÊN CHI TIẾT")
        self.fabric_tree.heading("value", text="LOẠI VẢI")
        self.detail_tree.column("value", width=430, minwidth=140, anchor="w", stretch=True)
        self.fabric_tree.column("value", width=300, minwidth=140, anchor="w", stretch=True)

        self.detail_tree.pack(fill="both", expand=True)
        self.fabric_tree.pack(fill="both", expand=True)

        # Một scrollbar dọc dùng chung cho cả hai cột.
        ybar = ttk.Scrollbar(body, orient="vertical", command=self._scroll_both)
        ybar.grid(row=0, column=1, sticky="ns")
        self.detail_tree.configure(yscrollcommand=ybar.set)
        self.fabric_tree.configure(yscrollcommand=ybar.set)

        self._trees = (self.detail_tree, self.fabric_tree)
        self._grid_lines = {self.detail_tree: [], self.fabric_tree: []}
        for idx, tree in enumerate(self._trees):
            tree.tag_configure("normal", background="#FFFFFF")
            tree.tag_configure("hover", background="#EEF5FC")
            tree.tag_configure("peer", background="#E4EAF0")
            tree.tag_configure("active", background="#FFF2B2")
            tree.tag_configure("selected_cell", background="#B9DCF7")
            tree.bind("<Motion>", lambda e, c=idx: self._on_motion(e, c))
            tree.bind("<Leave>", self._on_leave)
            tree.bind("<Button-1>", lambda e, c=idx: self._on_click(e, c))
            tree.bind("<B1-Motion>", lambda e, c=idx: self._on_drag(e, c))
            tree.bind("<ButtonRelease-1>", lambda e, c=idx: self._on_release(e, c))
            tree.bind("<Double-1>", lambda e, c=idx: self._begin_edit(e, c))
            tree.bind("<Control-v>", self._paste)
            tree.bind("<Control-V>", self._paste)
            tree.bind("<<Paste>>", self._paste)
            tree.bind("<Shift-Insert>", self._paste)
            tree.bind("<Control-c>", self._copy)
            tree.bind("<Control-C>", self._copy)
            tree.bind("<Delete>", lambda e: self.delete_selected())
            tree.bind("<MouseWheel>", self._on_mousewheel)
            tree.bind("<Configure>", lambda e, t=tree: self._schedule_grid_lines(t))

        self._append_blank_row()
        self.after_idle(self._update_all_grid_lines)

    def _schedule_grid_lines(self, tree=None):
        # Vẽ đường kẻ mờ theo từng hàng để bảng trông giống Excel hơn.
        if tree is None:
            self.after_idle(self._update_all_grid_lines)
        else:
            self.after_idle(lambda t=tree: self._update_grid_lines(t))

    def _update_all_grid_lines(self):
        for tree in self._trees:
            self._update_grid_lines(tree)

    def _update_grid_lines(self, tree):
        # Treeview không có viền từng ô mặc định, nên dùng các đường ngang mờ phủ theo hàng.
        lines = self._grid_lines.setdefault(tree, [])
        visible = []
        for iid in tree.get_children():
            bbox = tree.bbox(iid, "#1")
            if bbox:
                visible.append(bbox)

        while len(lines) < len(visible):
            line = tk.Frame(tree, bg="#D7DDE4", height=1, bd=0, highlightthickness=0)
            line.bind("<Button-1>", lambda e: "break")
            lines.append(line)

        for i, bbox in enumerate(visible):
            x, y, w, h = bbox
            # Đường kẻ ngang ở đáy ô, mảnh và màu xám nhạt.
            lines[i].place(x=x, y=max(y + h - 1, 0), width=max(w, 1), height=1)
            lines[i].lift()

        for line in lines[len(visible):]:
            line.place_forget()

    def _new_iid(self):
        iid = f"r{self._counter}"
        self._counter += 1
        return iid

    def _append_blank_row(self):
        iid = self._new_iid()
        self.detail_tree.insert("", "end", iid=iid, values=("",), tags=("normal",))
        self.fabric_tree.insert("", "end", iid=iid, values=("",), tags=("normal",))
        self._schedule_grid_lines()
        return iid

    def _all_iids(self):
        return list(self.detail_tree.get_children())

    def _value(self, tree, iid):
        vals = tree.item(iid, "values")
        return str(vals[0]) if vals else ""

    def _set_value(self, col, iid, value):
        tree = self._trees[col]
        tree.item(iid, values=(value,))

    def _is_blank(self, iid):
        return not self._value(self.detail_tree, iid).strip() and not self._value(self.fabric_tree, iid).strip()

    def _ensure_single_blank_last_row(self):
        """Giữ dữ liệu nguyên vẹn và chỉ để 1 hàng trống cuối cùng."""
        iids = self._all_iids()
        if not iids:
            self._append_blank_row()
            return

        # Xóa các dòng trống dư thừa, trừ dòng trống cuối cần giữ.
        blank_iids = [iid for iid in iids if self._is_blank(iid)]
        for iid in blank_iids:
            if iid != iids[-1]:
                self.detail_tree.delete(iid)
                self.fabric_tree.delete(iid)

        iids = self._all_iids()
        if not iids or not self._is_blank(iids[-1]):
            self._append_blank_row()
        self._schedule_grid_lines()

    def _scroll_both(self, *args):
        self.detail_tree.yview(*args)
        self.fabric_tree.yview(*args)
        self._schedule_grid_lines()

    def _on_mousewheel(self, event):
        units = -1 if event.delta > 0 else 1
        self.detail_tree.yview_scroll(units, "units")
        self.fabric_tree.yview_scroll(units, "units")
        self._schedule_grid_lines()
        return "break"

    def _sync_see(self, iid):
        if iid:
            self.detail_tree.see(iid)
            self.fabric_tree.see(iid)

    def _apply_row_state(self, iid):
        if not iid or iid not in self._all_iids():
            return
        for col, tree in enumerate(self._trees):
            cell = (col, iid)
            if iid == self._active_iid and col == self._active_col:
                tag = "active"
            elif cell in self._selected_cells:
                tag = "selected_cell"
            elif iid == self._active_iid and col != self._active_col:
                tag = "peer"
            elif iid == self._hover_iid:
                tag = "hover"
            else:
                tag = "normal"
            tree.item(iid, tags=(tag,))

    def _refresh_states(self, extra_iids=None):
        targets = set(extra_iids or [])
        targets.update(iid for _, iid in self._selected_cells)
        if self._hover_iid:
            targets.add(self._hover_iid)
        if self._active_iid:
            targets.add(self._active_iid)
        for iid in targets:
            if iid in self._all_iids():
                self._apply_row_state(iid)

    def _on_motion(self, event, col):
        tree = self._trees[col]
        iid = tree.identify_row(event.y)
        if iid == self._hover_iid:
            return
        old = self._hover_iid
        self._hover_iid = iid or None
        self._refresh_states([old, self._hover_iid])

    def _on_leave(self, event=None):
        old = self._hover_iid
        self._hover_iid = None
        self._refresh_states([old])

    def _clear_native_selection(self):
        for tree in self._trees:
            tree.selection_remove(tree.selection())

    def _on_click(self, event, col):
        tree = self._trees[col]
        iid = tree.identify_row(event.y)
        if not iid:
            return "break"
        # Đảm bảo Treeview nhận bàn phím để Ctrl+V hoạt động sau khi click.
        tree.focus_set()
        old_active = self._active_iid
        old_selected = list(self._selected_cells)
        self._active_col = col
        self._active_iid = iid
        self._drag_start = iid
        self._drag_col = col
        self._selected_cells = {(col, iid)}
        self._clear_native_selection()
        self._refresh_states([old_active, iid] + [x[1] for x in old_selected])
        self._sync_see(iid)
        return "break"

    def _on_drag(self, event, col):
        if self._drag_start is None or self._drag_col != col:
            return "break"
        tree = self._trees[col]
        iid = tree.identify_row(event.y)
        if not iid:
            return "break"
        iids = self._all_iids()
        if self._drag_start not in iids or iid not in iids:
            return "break"
        a, b = iids.index(self._drag_start), iids.index(iid)
        lo, hi = sorted((a, b))
        old = list(self._selected_cells)
        self._selected_cells = {(col, rid) for rid in iids[lo:hi + 1]}
        self._active_iid = iid
        self._refresh_states([x[1] for x in old] + iids[lo:hi + 1])
        self._sync_see(iid)
        return "break"

    def _on_release(self, event, col):
        self._drag_start = None
        self._drag_col = None
        return "break"

    def _begin_edit(self, event, col):
        if self._editor is not None:
            self._finish_edit()

        tree = self._trees[col]
        iid = tree.identify_row(event.y)
        if not iid:
            return "break"
        old = list(self._selected_cells)
        self._active_col = col
        self._active_iid = iid
        self._selected_cells = {(col, iid)}
        self._refresh_states([iid] + [x[1] for x in old])

        bbox = tree.bbox(iid, "#1")
        if not bbox:
            return "break"
        x, y, w, h = bbox
        value = self._value(tree, iid)

        self._editor_tree = tree
        self._editor_iid = iid
        self._editor = ttk.Entry(tree)
        self._editor.insert(0, value)
        self._editor.select_range(0, "end")
        self._editor.place(x=x, y=y, width=w, height=h)
        self._editor.focus_set()
        self._editor.bind("<Return>", lambda e: self._finish_edit())
        self._editor.bind("<Escape>", lambda e: self._cancel_edit())
        self._editor.bind("<FocusOut>", lambda e: self._finish_edit())
        return "break"

    def _finish_edit(self):
        if self._editor is None:
            return
        try:
            value = self._editor.get()
            self._editor_tree.item(self._editor_iid, values=(value,))
        finally:
            self._editor.destroy()
            self._editor = None
            self._editor_tree = None
            self._editor_iid = None
            self._ensure_single_blank_last_row()

    def _cancel_edit(self):
        if self._editor is not None:
            self._editor.destroy()
        self._editor = None
        self._editor_tree = None
        self._editor_iid = None

    def _paste(self, event=None):
        # Nếu lệnh Paste phát sinh trực tiếp từ một trong hai bảng, xác định lại cột đích.
        if event is not None and getattr(event, "widget", None) in self._trees:
            self._active_col = 0 if event.widget is self.detail_tree else 1
            event.widget.focus_set()
        if self._editor is not None:
            self._finish_edit()
        try:
            data = self.clipboard_get()
        except tk.TclError:
            try:
                data = self.tk.call("clipboard", "get")
            except tk.TclError:
                return "break"

        lines = data.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        while lines and lines[-1] == "":
            lines.pop()
        if not lines:
            return "break"

        matrix = [line.split("\t") for line in lines]
        iids = self._all_iids()
        if not iids:
            self._append_blank_row()
            iids = self._all_iids()

        start_iid = self._active_iid if self._active_iid in iids else iids[-1]
        start_row = iids.index(start_iid)
        needed = start_row + len(matrix)
        while len(iids) < needed:
            iids.append(self._append_blank_row())

        for r, row_data in enumerate(matrix):
            iid = iids[start_row + r]
            # Nếu dán 1 cột, chỉ đi vào cột đang click.
            # Nếu dán 2 cột từ Excel và bắt đầu ở TÊN CHI TIẾT, tự đổ cả hai cột.
            if self._active_col == 0:
                if len(row_data) >= 1:
                    self._set_value(0, iid, row_data[0].strip())
                if len(row_data) >= 2:
                    self._set_value(1, iid, row_data[1].strip())
            else:
                self._set_value(1, iid, row_data[0].strip() if row_data else "")

        self._active_iid = iids[start_row]
        self._ensure_single_blank_last_row()
        self._sync_see(self._active_iid)
        self._refresh_states([self._active_iid])
        return "break"

    def _copy(self, event=None):
        iid = self._active_iid
        if not iid or iid not in self._all_iids():
            return "break"
        value = self._value(self._trees[self._active_col], iid)
        self.clipboard_clear()
        self.clipboard_append(value)
        return "break"

    def delete_selected(self):
        cells = set(self._selected_cells)
        if not cells and self._active_iid:
            cells = {(self._active_col, self._active_iid)}
        if not cells:
            return
        touched = set()
        for col, iid in cells:
            if iid in self._all_iids():
                self._set_value(col, iid, "")
                touched.add(iid)
        self._selected_cells.clear()
        self._active_iid = None
        self._hover_iid = None
        self._ensure_single_blank_last_row()
        self._refresh_states(touched)

    def clear(self):
        for iid in self._all_iids():
            self.detail_tree.delete(iid)
            self.fabric_tree.delete(iid)
        self._active_iid = None
        self._hover_iid = None
        self._selected_cells.clear()
        self._append_blank_row()
        self._schedule_grid_lines()

    def get_pairs(self):
        pairs = []
        for iid in self._all_iids():
            detail = self._value(self.detail_tree, iid).strip()
            fabric = self._value(self.fabric_tree, iid).strip()
            # Dòng trống cuối không bao giờ được đưa sang danh sách đề xuất.
            if detail or fabric:
                pairs.append((detail, fabric))
        return pairs


    def set_pairs(self, pairs, replace=True):
        """Đưa danh sách (Tên chi tiết, Loại vải) vào bảng nhập."""
        if self._editor is not None:
            self._finish_edit()

        if replace:
            self.clear()
        else:
            self._ensure_single_blank_last_row()

        for detail, fabric in pairs:
            detail = str(detail or "").strip()
            fabric = str(fabric or "").strip()
            if not detail and not fabric:
                continue

            iids = self._all_iids()
            if iids and self._is_blank(iids[-1]):
                iid = iids[-1]
            else:
                iid = self._append_blank_row()

            self._set_value(0, iid, detail)
            self._set_value(1, iid, fabric)
            self._append_blank_row()

        self._ensure_single_blank_last_row()
        self._active_iid = None
        self._selected_cells.clear()
        self._schedule_grid_lines()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tạo danh sách bàn - Đọc PDS - Xuất Excel")
        self.geometry("1280x860")
        self.minsize(1000, 650)
        self.rows = []

        # Dữ liệu đọc từ PDS: [(tên chi tiết, material gốc), ...]
        self.pds_pairs = []
        self.pds_path_var = tk.StringVar()
        self.pds_status_var = tk.StringVar(value="PDS: chưa chọn file")
        self.material_name_vars = {}

        # V2.0.4: mỗi Material có thể tích/bỏ tích để chọn có cập nhật
        # xuống vùng TÊN CHI TIẾT / LOẠI VẢI hay không.
        self.material_update_vars = {}
        self.material_select_all_var = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Toolbar.TFrame", background="#EAF0F6")
        style.configure("Primary.TButton", background="#4D86C6", foreground="#FFFFFF", font=("Segoe UI", 10, "bold"), padding=(12, 7))
        style.configure("Add.TButton", background="#57A66A", foreground="#FFFFFF", font=("Segoe UI", 10, "bold"), padding=(12, 7))
        style.configure("Delete.TButton", background="#D96B6B", foreground="#FFFFFF", padding=(10, 5))
        style.configure("Clear.TButton", background="#D69445", foreground="#FFFFFF", padding=(10, 5))
        style.map("Primary.TButton", background=[("active", "#D7E8F8")])
        style.map("Add.TButton", background=[("active", "#DDF2E3")])
        style.map("Delete.TButton", background=[("active", "#F8DEDE")])
        style.map("Clear.TButton", background=[("active", "#F7E8D2")])

        self.vars = {
            "total": tk.StringVar(),
            "round_qty": tk.StringVar(value="50"),
            "start_no": tk.StringVar(value="3101"),
        }

        # Danh sách đề xuất chuyển thành cửa sổ xem trước riêng.
        self.preview_window = None
        self.tree = None
        self.preview_button_text = tk.StringVar(value="XEM DANH SÁCH ĐỀ XUẤT (0)")

        # Thanh dưới cố định.
        bottom = ttk.Frame(self, padding=(12, 7, 12, 10), style="Toolbar.TFrame")
        bottom.pack(side="bottom", fill="x")
        ttk.Label(
            bottom,
            text="Ctrl+V dán riêng từng cột • Kéo chuột để chọn nhiều ô • Delete để xóa nội dung",
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(
            bottom,
            textvariable=self.preview_button_text,
            command=self.show_preview_window,
        ).pack(side="right", padx=(8, 0))
        ttk.Button(
            bottom,
            text="XUẤT SANG EXCEL",
            command=self.export_excel,
            style="Primary.TButton",
        ).pack(side="right", padx=(10, 0))

        # Bố cục chính: trái = PDS/đổi tên + số lượng, phải = bảng chi tiết/loại vải.
        workspace = ttk.Panedwindow(self, orient="horizontal")
        workspace.pack(side="top", fill="both", expand=True, padx=12, pady=(12, 6))

        left = ttk.Frame(workspace, padding=(0, 0, 8, 0))
        right = ttk.Frame(workspace, padding=(8, 0, 0, 0))
        workspace.add(left, weight=2)
        workspace.add(right, weight=5)

        # ------------------------------------------------------------
        # TRÁI TRÊN: ĐỌC PDS + ĐỔI TÊN LOẠI VẢI
        # ------------------------------------------------------------
        pds_box = ttk.LabelFrame(left, text="ĐỌC PDS / ĐỔI TÊN LOẠI VẢI", padding=8)
        pds_box.pack(fill="x")

        file_line = ttk.Frame(pds_box)
        file_line.pack(fill="x")
        ttk.Label(file_line, text="FILE PDS").pack(side="left")
        ttk.Entry(file_line, textvariable=self.pds_path_var, width=28).pack(
            side="left", fill="x", expand=True, padx=(7, 0)
        )

        pds_buttons = ttk.Frame(pds_box)
        pds_buttons.pack(fill="x", pady=(6, 0))
        ttk.Button(
            pds_buttons,
            text="CHỌN PDS",
            command=self.pick_pds_file,
            style="Primary.TButton",
        ).pack(side="left")
        ttk.Button(
            pds_buttons,
            text="ĐỌC LẠI",
            command=self.load_pds_file,
        ).pack(side="left", padx=(6, 0))

        ttk.Label(
            pds_box,
            textvariable=self.pds_status_var,
            wraplength=450,
        ).pack(anchor="w", pady=(6, 3))

        map_outer = ttk.Frame(pds_box)
        map_outer.pack(fill="x")
        map_outer.columnconfigure(0, weight=1)
        map_outer.rowconfigure(1, weight=1)

        self.material_header = ttk.Frame(map_outer)
        self.material_header.grid(row=0, column=0, sticky="ew")
        self._configure_material_columns(self.material_header)

        ttk.Checkbutton(
            self.material_header,
            text="CHỌN",
            variable=self.material_select_all_var,
            command=self._toggle_all_materials,
        ).grid(row=0, column=0, sticky="w", padx=3, pady=(2, 4))
        ttk.Label(
            self.material_header,
            text="MATERIAL",
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=1, sticky="w", padx=4, pady=(2, 4))
        ttk.Label(
            self.material_header,
            text="→",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=2, padx=2)
        ttk.Label(
            self.material_header,
            text="ĐỔI TÊN LOẠI VẢI",
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=3, sticky="w", padx=4, pady=(2, 4))
        ttk.Label(
            self.material_header,
            text="SỐ CT",
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=4, sticky="w", padx=4, pady=(2, 4))

        self.material_canvas = tk.Canvas(
            map_outer,
            height=220,
            bd=0,
            highlightthickness=1,
            highlightbackground="#C7CDD4",
            background="#FFFFFF",
        )
        self.material_scroll = ttk.Scrollbar(
            map_outer,
            orient="vertical",
            command=self.material_canvas.yview,
        )
        self.material_canvas.configure(yscrollcommand=self.material_scroll.set)
        self.material_canvas.grid(row=1, column=0, sticky="ew")
        self.material_scroll.grid(row=1, column=1, sticky="ns")
        ttk.Frame(map_outer, width=16).grid(row=0, column=1, sticky="ns")

        self.material_map_inner = ttk.Frame(self.material_canvas)
        self._configure_material_columns(self.material_map_inner)
        self._material_window = self.material_canvas.create_window(
            (0, 0), window=self.material_map_inner, anchor="nw"
        )

        self.material_map_inner.bind(
            "<Configure>",
            lambda e: self.material_canvas.configure(
                scrollregion=self.material_canvas.bbox("all")
            ),
        )
        self.material_canvas.bind(
            "<Configure>",
            lambda e: self.material_canvas.itemconfigure(
                self._material_window, width=e.width
            ),
        )
        self.material_canvas.bind("<MouseWheel>", self._on_material_mousewheel)
        self.material_canvas.bind("<Button-4>", self._on_material_mousewheel)
        self.material_canvas.bind("<Button-5>", self._on_material_mousewheel)

        self._render_material_mapping()

        ttk.Label(
            pds_box,
            text="Tích loại vải cần lấy • Có thể đổi tên trước khi cập nhật.",
            wraplength=450,
        ).pack(anchor="w", pady=(6, 3))
        ttk.Button(
            pds_box,
            text="CẬP NHẬT XUỐNG TÊN CHI TIẾT / LOẠI VẢI",
            command=self.apply_pds_to_input_grid,
            style="Add.TButton",
        ).pack(fill="x", pady=(2, 0))

        # ------------------------------------------------------------
        # TRÁI DƯỚI: THÔNG TIN SỐ LƯỢNG
        # ------------------------------------------------------------
        info_box = ttk.LabelFrame(left, text="THÔNG TIN SỐ LƯỢNG", padding=10)
        info_box.pack(fill="x", pady=(8, 0))

        ttk.Label(info_box, text="TỔNG SỐ LƯỢNG").pack(anchor="w")
        ttk.Entry(info_box, textvariable=self.vars["total"], width=18).pack(
            fill="x", pady=(2, 8)
        )
        ttk.Label(info_box, text="SỐ LƯỢNG LÀM TRÒN").pack(anchor="w")
        ttk.Entry(info_box, textvariable=self.vars["round_qty"], width=18).pack(
            fill="x", pady=(2, 8)
        )
        ttk.Label(info_box, text="SỐ THỨ TỰ BẮT ĐẦU").pack(anchor="w")
        ttk.Entry(info_box, textvariable=self.vars["start_no"], width=18).pack(
            fill="x", pady=(2, 10)
        )

        ttk.Button(
            info_box,
            text="THÊM VÀO DANH SÁCH ĐỀ XUẤT",
            command=self.add_item,
            style="Add.TButton",
        ).pack(fill="x", pady=(0, 6))

        ttk.Button(
            info_box,
            textvariable=self.preview_button_text,
            command=self.show_preview_window,
        ).pack(fill="x")

        # ------------------------------------------------------------
        # PHẢI: TÊN CHI TIẾT / LOẠI VẢI - CAO TỪ TRÊN XUỐNG DƯỚI
        # ------------------------------------------------------------
        grid_box = ttk.LabelFrame(right, text="TÊN CHI TIẾT / LOẠI VẢI", padding=6)
        grid_box.pack(fill="both", expand=True)

        self.input_grid = EditablePasteGrid(grid_box)
        self.input_grid.pack(fill="both", expand=True)

        grid_tools = ttk.Frame(right, style="Toolbar.TFrame")
        grid_tools.pack(fill="x", pady=(5, 0))
        ttk.Button(
            grid_tools,
            text="Xóa ô đã chọn",
            command=self.input_grid.delete_selected,
            style="Delete.TButton",
        ).pack(side="left")
        ttk.Button(
            grid_tools,
            text="Xóa bảng nhập",
            command=self.input_grid.clear,
            style="Clear.TButton",
        ).pack(side="left", padx=6)
        ttk.Label(
            grid_tools,
            text="Click: ô chọn vàng • Double-click: sửa • Ctrl+V: dán dữ liệu",
        ).pack(side="left", padx=8)

    def show_preview_window(self):
        """Mở cửa sổ riêng để xem/chỉnh danh sách đề xuất."""
        if self.preview_window is not None:
            try:
                if self.preview_window.winfo_exists():
                    self.preview_window.deiconify()
                    self.preview_window.lift()
                    self.preview_window.focus_force()
                    self._refresh_preview_tree()
                    return
            except Exception:
                pass

        win = tk.Toplevel(self)
        self.preview_window = win
        win.title("Danh sách đề xuất trước khi xuất")
        win.geometry("1120x620")
        win.minsize(850, 450)

        toolbar = ttk.Frame(win, padding=(10, 8), style="Toolbar.TFrame")
        toolbar.pack(fill="x")

        ttk.Button(
            toolbar,
            text="Xóa dòng chọn",
            command=self.delete_selected,
            style="Delete.TButton",
        ).pack(side="left")
        ttk.Button(
            toolbar,
            text="Xóa tất cả",
            command=self.clear_all,
            style="Clear.TButton",
        ).pack(side="left", padx=6)

        self.preview_count_label = ttk.Label(toolbar, text="")
        self.preview_count_label.pack(side="left", padx=10)

        ttk.Button(
            toolbar,
            text="ĐÓNG",
            command=self._close_preview_window,
        ).pack(side="right")

        tree_frame = ttk.Frame(win, padding=(10, 0, 10, 10))
        tree_frame.pack(fill="both", expand=True)
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        columns = ("ban", "from_no", "to_no", "qty", "detail", "fabric")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="extended",
        )

        headings = {
            "ban": "SỐ BÀN",
            "from_no": "SỐ THỨ TỰ 1",
            "to_no": "SỐ THỨ TỰ 2",
            "qty": "SỐ LƯỢNG",
            "detail": "TÊN CHI TIẾT",
            "fabric": "LOẠI VẢI",
        }
        widths = {
            "ban": 80,
            "from_no": 115,
            "to_no": 115,
            "qty": 100,
            "detail": 330,
            "fabric": 240,
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            anchor = "w" if col in ("detail", "fabric") else "center"
            self.tree.column(
                col,
                width=widths[col],
                minwidth=70,
                anchor=anchor,
                stretch=(col in ("detail", "fabric")),
            )

        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        self.tree.bind("<Delete>", lambda e: self.delete_selected())

        win.protocol("WM_DELETE_WINDOW", self._close_preview_window)
        self._refresh_preview_tree()

    def _close_preview_window(self):
        if self.preview_window is not None:
            try:
                self.preview_window.destroy()
            except Exception:
                pass
        self.preview_window = None
        self.tree = None

    def _refresh_preview_tree(self):
        """Đồng bộ nút đếm và cửa sổ xem trước nếu đang mở."""
        if hasattr(self, "preview_button_text"):
            self.preview_button_text.set(
                f"XEM DANH SÁCH ĐỀ XUẤT ({len(self.rows)})"
            )

        tree = getattr(self, "tree", None)
        if tree is None:
            return

        try:
            if not tree.winfo_exists():
                self.tree = None
                return
        except Exception:
            self.tree = None
            return

        for item in tree.get_children():
            tree.delete(item)

        for row in self.rows:
            tree.insert(
                "",
                "end",
                values=(
                    row["ban"],
                    row["from_no"],
                    row["to_no"],
                    row["qty"],
                    row["detail"],
                    row["fabric"],
                ),
            )

        if hasattr(self, "preview_count_label"):
            try:
                self.preview_count_label.config(
                    text=f"Tổng số dòng: {len(self.rows)}"
                )
            except Exception:
                pass

    def pick_pds_file(self):
        p = filedialog.askopenfilename(
            title="Chọn file Optitex PDS",
            filetypes=[
                ("Optitex PDS", "*.pds"),
                ("Tất cả file", "*.*"),
            ],
        )
        if not p:
            return
        self.pds_path_var.set(p)
        self.load_pds_file()

    def load_pds_file(self):
        path = self.pds_path_var.get().strip().strip('"')
        if not path:
            messagebox.showwarning("Chưa chọn PDS", "Hãy chọn file PDS trước.")
            return

        if not Path(path).is_file():
            messagebox.showerror("Không tìm thấy PDS", "Không tìm thấy file:\n" + path)
            return

        self.pds_status_var.set("PDS: đang đọc Tên chi tiết / Material...")
        self.update_idletasks()

        try:
            pairs = read_piece_materials_from_pds(path)
        except Exception as e:
            self.pds_pairs = []
            self.material_name_vars.clear()
            self.material_update_vars.clear()
            self.material_select_all_var.set(True)
            self._render_material_mapping()
            self.pds_status_var.set("PDS: lỗi đọc dữ liệu")
            messagebox.showerror("Lỗi đọc PDS", str(e))
            return

        self.pds_pairs = pairs

        # Tạo danh sách Material theo thứ tự xuất hiện trong PDS.
        materials = []
        for _, material in pairs:
            material = str(material or "").strip()
            if material not in materials:
                materials.append(material)

        # Giữ tên đã đổi và trạng thái tích nếu user bấm ĐỌC LẠI cùng PDS.
        old_values = {
            key: var.get()
            for key, var in self.material_name_vars.items()
        }
        old_checks = {
            key: bool(var.get())
            for key, var in self.material_update_vars.items()
        }

        self.material_name_vars = {}
        self.material_update_vars = {}
        for material in materials:
            default_name = old_values.get(material, material)
            self.material_name_vars[material] = tk.StringVar(value=default_name)
            self.material_update_vars[material] = tk.BooleanVar(
                value=old_checks.get(material, True)
            )

        self._sync_material_select_all_state()
        self._render_material_mapping()

        missing_names = sum(
            1 for detail, _ in pairs
            if str(detail).upper().startswith("CHI TIET ")
        )
        status = (
            f"PDS: đã đọc {len(pairs)} chi tiết | "
            f"{len(materials)} Material"
        )
        if missing_names:
            status += f" | {missing_names} tên cần kiểm tra"
        self.pds_status_var.set(status)

    def _configure_material_columns(self, frame):
        """Giữ cột tiêu đề và dữ liệu thẳng hàng trong vùng bên trái."""
        frame.columnconfigure(0, weight=0, minsize=48)
        frame.columnconfigure(1, weight=2, minsize=125)
        frame.columnconfigure(2, weight=0, minsize=22)
        frame.columnconfigure(3, weight=3, minsize=165)
        frame.columnconfigure(4, weight=0, minsize=58)

    def _on_material_mousewheel(self, event):
        """Cuộn danh sách Material bằng con lăn chuột."""
        if not hasattr(self, "material_canvas"):
            return "break"

        # Windows/macOS dùng event.delta; Linux thường dùng Button-4/Button-5.
        if getattr(event, "num", None) == 4:
            units = -1
        elif getattr(event, "num", None) == 5:
            units = 1
        else:
            delta = getattr(event, "delta", 0)
            if delta == 0:
                return "break"
            # Windows thường trả +/-120 mỗi nấc.
            units = -1 if delta > 0 else 1

        self.material_canvas.yview_scroll(units, "units")
        return "break"

    def _bind_material_mousewheel_recursive(self, widget):
        """Cho phép lăn chuột ngay cả khi con trỏ đang ở Entry/Label/Checkbutton."""
        try:
            widget.bind("<MouseWheel>", self._on_material_mousewheel, add="+")
            widget.bind("<Button-4>", self._on_material_mousewheel, add="+")
            widget.bind("<Button-5>", self._on_material_mousewheel, add="+")
        except Exception:
            pass

        try:
            children = widget.winfo_children()
        except Exception:
            children = []

        for child in children:
            self._bind_material_mousewheel_recursive(child)

    def _toggle_all_materials(self):
        """Tích/bỏ tích tất cả Material theo ô ở tiêu đề."""
        value = bool(self.material_select_all_var.get())
        for var in self.material_update_vars.values():
            var.set(value)

    def _sync_material_select_all_state(self):
        """Đồng bộ ô tích tất cả theo trạng thái các Material hiện có."""
        if not self.material_update_vars:
            self.material_select_all_var.set(True)
            return
        self.material_select_all_var.set(
            all(bool(var.get()) for var in self.material_update_vars.values())
        )

    def _on_material_check_changed(self):
        self._sync_material_select_all_state()

    def _render_material_mapping(self):
        if not hasattr(self, "material_map_inner"):
            return

        for w in self.material_map_inner.winfo_children():
            w.destroy()

        if not self.material_name_vars:
            ttk.Label(
                self.material_map_inner,
                text="Chọn file PDS để hiện tất cả Material tại đây.",
            ).grid(
                row=0,
                column=0,
                columnspan=5,
                sticky="w",
                padx=5,
                pady=10,
            )
            self._bind_material_mousewheel_recursive(self.material_map_inner)
            return

        counts = {}
        for _, material in self.pds_pairs:
            material = str(material or "").strip()
            counts[material] = counts.get(material, 0) + 1

        for row, (material, var) in enumerate(
            self.material_name_vars.items(),
            start=0,
        ):
            check_var = self.material_update_vars.setdefault(
                material, tk.BooleanVar(value=True)
            )

            ttk.Checkbutton(
                self.material_map_inner,
                variable=check_var,
                command=self._on_material_check_changed,
            ).grid(row=row, column=0, sticky="w", padx=7, pady=2)

            shown = material if material else "(KHÔNG CÓ MATERIAL)"
            ttk.Label(
                self.material_map_inner,
                text=shown,
            ).grid(row=row, column=1, sticky="ew", padx=5, pady=2)

            ttk.Label(
                self.material_map_inner,
                text="→",
            ).grid(row=row, column=2, padx=4, pady=2)

            ttk.Entry(
                self.material_map_inner,
                textvariable=var,
            ).grid(row=row, column=3, sticky="ew", padx=5, pady=2)

            ttk.Label(
                self.material_map_inner,
                text=str(counts.get(material, 0)),
            ).grid(row=row, column=4, sticky="w", padx=8, pady=2)

        # Sau mỗi lần đọc lại PDS, các Entry/Checkbutton được tạo lại.
        # Gắn lại MouseWheel cho toàn bộ vùng dữ liệu.
        self._bind_material_mousewheel_recursive(self.material_map_inner)

    def apply_pds_to_input_grid(self):
        if not self.pds_pairs:
            messagebox.showwarning(
                "Chưa có dữ liệu PDS",
                "Hãy chọn và đọc file PDS trước.",
            )
            return

        rename_map = {}
        selected_materials = set()

        for material, var in self.material_name_vars.items():
            new_name = var.get().strip()
            # Nếu user xóa trắng ô đổi tên thì giữ lại tên Material gốc.
            rename_map[material] = new_name if new_name else material

            check_var = self.material_update_vars.get(material)
            if check_var is None or bool(check_var.get()):
                selected_materials.add(material)

        if not selected_materials:
            messagebox.showwarning(
                "Chưa chọn loại vải",
                "Hãy tích ít nhất 1 Material / Loại vải cần cập nhật xuống.",
            )
            return

        mapped = []
        seen = set()
        for detail, material in self.pds_pairs:
            detail = str(detail or "").strip()
            material = str(material or "").strip()

            # V2.0.4: Material không được tích sẽ không đưa xuống bảng nhập.
            if material not in selected_materials:
                continue

            fabric = rename_map.get(material, material).strip()

            if not detail:
                continue

            key = (detail.casefold(), fabric.casefold())
            if key in seen:
                continue
            seen.add(key)
            mapped.append((detail, fabric))

        if not mapped:
            messagebox.showwarning(
                "Không có dữ liệu",
                "Không có Tên chi tiết / Loại vải hợp lệ để cập nhật.",
            )
            return

        existing = self.input_grid.get_pairs()
        replace = True
        if existing:
            choice = messagebox.askyesnocancel(
                "Bảng nhập đang có dữ liệu",
                "Bảng TÊN CHI TIẾT / LOẠI VẢI đang có dữ liệu.\n\n"
                "YES  = Xóa dữ liệu cũ và thay bằng PDS\n"
                "NO   = Giữ dữ liệu cũ và thêm PDS xuống dưới\n"
                "CANCEL = Không làm gì",
            )
            if choice is None:
                return
            replace = bool(choice)

        self.input_grid.set_pairs(mapped, replace=replace)

        messagebox.showinfo(
            "Đã cập nhật từ PDS",
            f"Đã chọn {len(selected_materials)} loại vải và đưa "
            f"{len(mapped)} dòng xuống bảng TÊN CHI TIẾT / LOẠI VẢI.\n\n"
            "Các Material bỏ tích không được đưa xuống.\n"
            "Bạn vẫn có thể double-click để sửa trực tiếp từng ô.",
        )

    @staticmethod
    def split_quantities(total, round_qty):
        """
        Chia bàn theo số làm tròn nhưng tránh bàn cuối quá lớn.
        Ví dụ round_qty=50: bàn cuối tối đa 75. Nếu đang là 85 -> tách thành 50 + 35.
        Ngưỡng được tính bằng 1.5 lần số lượng làm tròn.
        """
        if total <= 0 or round_qty <= 0:
            return []
        if total <= round_qty:
            return [total]

        n = total // round_qty
        if n <= 1:
            # Nếu tổng lớn hơn số làm tròn thì vẫn phải tách ít nhất 2 bàn.
            # Ví dụ: 92 với làm tròn 50 -> 50 + 42.
            return [round_qty, total - round_qty]

        result = [round_qty] * (n - 1)
        last = total - round_qty * (n - 1)
        limit = round_qty * 1.5
        if last > limit:
            result.extend([round_qty, last - round_qty])
        else:
            result.append(last)
        return result

    def _read_inputs(self):
        try:
            total = int(self.vars["total"].get().strip())
            round_qty = int(self.vars["round_qty"].get().strip())
            start_no = int(self.vars["start_no"].get().strip())
        except ValueError:
            raise ValueError("Tổng số lượng, số lượng làm tròn và số thứ tự bắt đầu phải là số nguyên.")

        if total <= 0:
            raise ValueError("Tổng số lượng phải lớn hơn 0.")
        if round_qty <= 0:
            raise ValueError("Số lượng làm tròn phải lớn hơn 0.")
        if start_no <= 0:
            raise ValueError("Số thứ tự bắt đầu phải lớn hơn 0.")

        pairs = self.input_grid.get_pairs()
        if not pairs:
            raise ValueError("Vui lòng nhập hoặc dán Tên chi tiết / Loại vải.")

        for i, (detail, fabric) in enumerate(pairs, start=1):
            if not detail:
                raise ValueError(f"Dòng {i}: chưa có Tên chi tiết.")
            if not fabric:
                raise ValueError(f"Dòng {i}: chưa có Loại vải.")

        return total, round_qty, start_no, pairs

    def add_item(self):
        try:
            total, round_qty, start_no, pairs = self._read_inputs()
        except ValueError as e:
            messagebox.showwarning("Thiếu / sai dữ liệu", str(e))
            return

        quantities = self.split_quantities(total, round_qty)
        for detail, fabric in pairs:
            current = start_no
            for i, qty in enumerate(quantities, start=1):
                end_no = current + qty - 1
                row = {
                    "ban": i,
                    "from_no": current,
                    "to_no": end_no,
                    "qty": qty,
                    "detail": detail,
                    "fabric": fabric,
                }
                self.rows.append(row)
                current = end_no + 1

        # Bảng nhập vẫn giữ nguyên dữ liệu và luôn còn 1 hàng trống cuối để dán tiếp.
        self.input_grid._ensure_single_blank_last_row()
        self._refresh_preview_tree()

    def delete_selected(self):
        tree = getattr(self, "tree", None)
        if tree is None:
            return
        try:
            selected = tree.selection()
        except Exception:
            return
        if not selected:
            return

        indices = sorted(
            (tree.index(item) for item in selected),
            reverse=True,
        )
        for idx in indices:
            if 0 <= idx < len(self.rows):
                self.rows.pop(idx)

        self._refresh_preview_tree()

    def clear_all(self):
        if not self.rows:
            return
        parent = self.preview_window if self.preview_window is not None else self
        if messagebox.askyesno(
            "Xác nhận",
            "Xóa toàn bộ danh sách đề xuất?",
            parent=parent,
        ):
            self.rows.clear()
            self._refresh_preview_tree()

    def export_excel(self):
        if not self.rows:
            messagebox.showwarning("Chưa có dữ liệu", "Hãy thêm dữ liệu vào danh sách đề xuất trước khi xuất Excel.")
            return

        path = filedialog.asksaveasfilename(
            title="Lưu file Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")],
            initialfile="danh_sach_ban.xlsx",
        )
        if not path:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "1"

        headers = ["SO BAN", "SO THU TU 1", "SO THU TU 2", "SO LUONG", "TEN CHI TIET", "LOAI VAI"]
        ws.append(headers)
        for row in self.rows:
            ws.append([row["ban"], row["from_no"], row["to_no"], row["qty"], row["detail"], row["fabric"]])

        # Định dạng theo đúng file mẫu M.xlsx để phần mềm barcode nhận tiêu đề.
        # Không tô nền, không in đậm, không viền, không AutoFilter, không Freeze Panes.
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=6):
            for cell in row:
                cell.font = Font(name="Times New Roman", size=11, bold=False)
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.number_format = "General"

        # Độ rộng gần giống file mẫu.
        ws.column_dimensions["A"].width = 16
        ws.column_dimensions["B"].width = 16
        ws.column_dimensions["C"].width = 16
        ws.column_dimensions["D"].width = 16
        ws.column_dimensions["E"].width = 21.14
        ws.column_dimensions["F"].width = 16

        ws.freeze_panes = None
        ws.auto_filter.ref = None
        ws.sheet_view.showGridLines = True

        try:
            wb.save(path)
        except PermissionError:
            messagebox.showerror("Không thể lưu", "File đang mở trong Excel. Hãy đóng file rồi thử lại.")
            return
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất file:\n{e}")
            return

        # Chỉ xóa danh sách đề xuất sau khi file đã được lưu thành công.
        self.rows.clear()
        self._refresh_preview_tree()

        messagebox.showinfo(
            "Hoàn tất",
            f"Đã xuất file:\n{path}\n\nDanh sách đề xuất trên phần mềm đã được xóa."
        )


if __name__ == "__main__":
    App().mainloop()
