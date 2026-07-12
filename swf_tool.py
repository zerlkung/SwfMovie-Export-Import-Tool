import sys
import os
import json
import struct
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QLabel, QFileDialog,
    QGroupBox, QRadioButton, QMessageBox, QProgressBar, QButtonGroup,
    QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

GFX_SIGNATURE = b'GFX'
FOOTER_TAIL = b'\xC1\x83\x2A\x9E'
FOOTER_SIZE = 16


def find_gfx_offset(data: bytes) -> int:
    pos = data.find(GFX_SIGNATURE)
    if pos == -1:
        raise ValueError("GFX signature not found in file")
    if pos < 4:
        raise ValueError("GFX signature found at position < 4, missing size prefix")
    return pos


def validate_footer(data: bytes) -> bool:
    if len(data) < FOOTER_SIZE:
        return False
    return data[-16:] == data[-16:-12] + FOOTER_TAIL or data[-4:] == FOOTER_TAIL


def has_valid_footer_tail(data: bytes) -> bool:
    return len(data) >= 4 and data[-4:] == FOOTER_TAIL


def export_uexp(input_path: str, output_path: str) -> tuple:
    with open(input_path, 'rb') as f:
        data = f.read()

    gfx_offset = find_gfx_offset(data)
    header = data[:gfx_offset]

    if not has_valid_footer_tail(data):
        raise ValueError("Footer tail (C1 83 2A 9E) not found at end of file")

    footer = data[-FOOTER_SIZE:]
    gfx_data = data[gfx_offset:-FOOTER_SIZE]

    with open(output_path, 'wb') as f:
        f.write(gfx_data)

    header_path = output_path + '.hdr'
    with open(header_path, 'wb') as f:
        f.write(header)

    footer_path = output_path + '.ftr'
    with open(footer_path, 'wb') as f:
        f.write(footer)

    return header, footer, gfx_data


def import_gfx_from_bytes(gfx_path: str, header: bytes, footer: bytes, output_path: str):
    with open(gfx_path, 'rb') as f:
        gfx_data = bytearray(f.read())

    header = bytearray(header)
    new_size = len(gfx_data)

    if len(header) >= 4:
        struct.pack_into('<I', header, len(header) - 4, new_size)
    if len(gfx_data) >= 8:
        struct.pack_into('<I', gfx_data, 4, new_size)

    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(gfx_data)
        f.write(footer)


class SwfToolGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FontMod SWF/UEXP Tool — Python Edition")
        self.setMinimumSize(680, 520)
        self.last_header_path = None
        self.last_footer_path = None
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)

        # --- Mode (large toggle buttons) ---
        mode_group = QGroupBox("Mode")
        mode_layout = QHBoxLayout(mode_group)
        mode_layout.setSpacing(8)

        btn_font = QFont()
        btn_font.setPointSize(12)
        btn_font.setBold(True)

        self.btn_export = QPushButton("📤  EXPORT\n.uexp / .swfmovie  →  .gfx")
        self.btn_export.setCheckable(True)
        self.btn_export.setChecked(True)
        self.btn_export.setMinimumHeight(60)
        self.btn_export.setFont(btn_font)
        self.btn_export.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.btn_import = QPushButton("📥  IMPORT\n.gfx  →  .uexp / .swfmovie")
        self.btn_import.setCheckable(True)
        self.btn_import.setMinimumHeight(60)
        self.btn_import.setFont(btn_font)
        self.btn_import.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.mode_group_btns = QButtonGroup(self)
        self.mode_group_btns.addButton(self.btn_export, 0)
        self.mode_group_btns.addButton(self.btn_import, 1)
        self.mode_group_btns.buttonClicked.connect(self._mode_changed)

        mode_layout.addWidget(self.btn_export)
        mode_layout.addWidget(self.btn_import)
        layout.addWidget(mode_group)

        self.setStyleSheet("""
            QPushButton[checkable="true"] {
                border: 2px solid #888;
                border-radius: 8px;
                padding: 10px 16px;
                background-color: #3a3a3a;
                color: #ccc;
            }
            QPushButton[checkable="true"]:checked {
                border: 3px solid #4a9eff;
                background-color: #1e3a5f;
                color: #fff;
            }
            QPushButton[checkable="true"]:hover {
                border-color: #4a9eff;
            }
            QGroupBox {
                font-weight: bold;
                margin-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 6px;
            }
        """)

        # --- Input ---
        in_group = QGroupBox("Input File")
        in_layout = QHBoxLayout(in_group)
        self.in_edit = QLineEdit()
        self.in_edit.setPlaceholderText("Select input file...")
        self.in_btn = QPushButton("Browse...")
        self.in_btn.clicked.connect(self._browse_input)
        in_layout.addWidget(self.in_edit)
        in_layout.addWidget(self.in_btn)
        layout.addWidget(in_group)

        # --- Reference (import only) ---
        self.ref_group = QGroupBox("Reference Header/Footer  (import only)")
        ref_layout = QHBoxLayout(self.ref_group)
        self.ref_edit = QLineEdit()
        self.ref_edit.setPlaceholderText("Auto-detected from .hdr/.ftr sidecar files, or select .uexp...")
        self.ref_btn = QPushButton("Browse...")
        self.ref_btn.clicked.connect(self._browse_ref)
        ref_layout.addWidget(self.ref_edit)
        ref_layout.addWidget(self.ref_btn)
        self.ref_group.setVisible(False)
        layout.addWidget(self.ref_group)

        # --- Output ---
        out_group = QGroupBox("Output File")
        out_layout = QHBoxLayout(out_group)
        self.out_edit = QLineEdit()
        self.out_edit.setPlaceholderText("Auto-generated, or select output file...")
        self.out_btn = QPushButton("Browse...")
        self.out_btn.clicked.connect(self._browse_output)
        out_layout.addWidget(self.out_edit)
        out_layout.addWidget(self.out_btn)
        layout.addWidget(out_group)

        # --- Convert ---
        self.convert_btn = QPushButton("▶  Convert")
        self.convert_btn.setMinimumHeight(44)
        convert_font = QFont()
        convert_font.setPointSize(11)
        convert_font.setBold(True)
        self.convert_btn.setFont(convert_font)
        self.convert_btn.clicked.connect(self._convert)
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d6a2d;
                color: #fff;
                border: 2px solid #3a8a3a;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #3a8a3a;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
                border-color: #555;
            }
        """)
        layout.addWidget(self.convert_btn)

        # --- Progress ---
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # --- Log ---
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(180)
        log_layout.addWidget(self.log)
        layout.addWidget(log_group)

    def _mode_changed(self, btn):
        is_import = (btn is self.btn_import)
        self.ref_group.setVisible(is_import)
        if self.in_edit.text():
            self._auto_output(self.in_edit.text())
            if is_import:
                self._auto_ref(self.in_edit.text())

    def _browse_input(self):
        if self.btn_export.isChecked():
            filt = "UEXP/SWFMovie files (*.uexp *.swfmovie);;All files (*.*)"
        else:
            filt = "GFX files (*.gfx);;All files (*.*)"
        path, _ = QFileDialog.getOpenFileName(self, "Select Input", "", filt)
        if path:
            self.in_edit.setText(path)
            self._auto_output(path)
            if self.btn_import.isChecked():
                self._auto_ref(path)

    def _browse_ref(self):
        filt = "UEXP/SWFMovie files (*.uexp *.swfmovie);;All files (*.*)"
        path, _ = QFileDialog.getOpenFileName(self, "Select Original UEXP for Header", "", filt)
        if path:
            self.ref_edit.setText(path)

    def _browse_output(self):
        if self.btn_export.isChecked():
            filt = "GFX files (*.gfx);;All files (*.*)"
        else:
            filt = "UEXP files (*.uexp);;SWFMovie files (*.swfmovie);;All files (*.*)"
        path, _ = QFileDialog.getSaveFileName(self, "Select Output", "", filt)
        if path:
            path = self._safe_output_path(path)
            self.out_edit.setText(path)

    def _auto_ref(self, input_path: str):
        p = Path(input_path)
        uexp_candidate = str(p.with_suffix('.uexp'))
        if os.path.exists(uexp_candidate):
            self.ref_edit.setText(uexp_candidate)
            return
        swf_candidate = str(p.with_suffix('.swfmovie'))
        if os.path.exists(swf_candidate):
            self.ref_edit.setText(swf_candidate)

    def _auto_output(self, input_path: str):
        p = Path(input_path)
        if self.btn_export.isChecked():
            base = str(p.with_suffix('.gfx'))
        else:
            base = str(p.with_suffix('.uexp'))
        output = self._safe_output_path(base)
        self.out_edit.setText(output)

    def _safe_output_path(self, path: str) -> str:
        if not os.path.exists(path):
            return path
        p = Path(path)
        stem = p.stem
        suffix = p.suffix
        parent = p.parent
        counter = 1
        while True:
            candidate = str(parent / f"{stem}_{counter}{suffix}")
            if not os.path.exists(candidate):
                return candidate
            counter += 1

    def _log(self, text: str):
        self.log.append(text)

    def _convert(self):
        input_path = self.in_edit.text().strip()
        output_path = self.out_edit.text().strip()
        ref_path = self.ref_edit.text().strip()

        if not input_path:
            QMessageBox.warning(self, "Warning", "Please select an input file.")
            return
        if not output_path:
            QMessageBox.warning(self, "Warning", "Please choose an output file.")
            return

        self.convert_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.log.clear()

        try:
            if self.btn_export.isChecked():
                self._do_export(input_path, output_path)
            else:
                self._do_import(input_path, ref_path, output_path)
        except Exception as e:
            self._log(f"[ERROR] {e}")
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self.convert_btn.setEnabled(True)
            self.progress.setVisible(False)

    def _do_export(self, input_path: str, output_path: str):
        self._log(f"Export: {input_path}  →  {output_path}")
        self.progress.setValue(10)

        header, footer, gfx_data = export_uexp(input_path, output_path)

        self.progress.setValue(80)

        hdr_path = output_path + '.hdr'
        ftr_path = output_path + '.ftr'

        self._log(f"  GFX signature found at offset {len(header)}")
        self._log(f"  Header saved: {hdr_path}  ({len(header)} bytes)")
        self._log(f"  Footer saved: {ftr_path}  ({len(footer)} bytes)")
        self._log(f"  GFX  data size: {len(gfx_data)} bytes")
        self._log(f"  Output written: {output_path}")
        self._log("[OK] Export successful!")

        self.last_header_path = hdr_path
        self.last_footer_path = ftr_path

        self.progress.setValue(100)

    def _do_import(self, input_path: str, ref_path: str, output_path: str):
        self._log(f"Import: {input_path}  →  {output_path}")

        if ref_path and os.path.isfile(ref_path):
            self._log(f"  Extracting header/footer from: {ref_path}")
            with open(ref_path, 'rb') as f:
                ref_data = f.read()
            gfx_offset = find_gfx_offset(ref_data)
            if not has_valid_footer_tail(ref_data):
                raise ValueError("Reference file: footer tail not found")
            header = ref_data[:gfx_offset]
            footer = ref_data[-FOOTER_SIZE:]
            self._log(f"  Header: {len(header)} bytes  Footer: {len(footer)} bytes")
            self.progress.setValue(30)
            import_gfx_from_bytes(input_path, header, footer, output_path)
        else:
            base = ref_path if ref_path else input_path
            hdr_path = base + '.hdr'
            ftr_path = base + '.ftr'
            if os.path.exists(hdr_path) and os.path.exists(ftr_path):
                self._log(f"  Using sidecar: {hdr_path} / {ftr_path}")
                with open(hdr_path, 'rb') as f:
                    header = f.read()
                with open(ftr_path, 'rb') as f:
                    footer = f.read()
                self.progress.setValue(30)
                import_gfx_from_bytes(input_path, header, footer, output_path)
            else:
                raise ValueError(
                    "Header/footer not found.\n"
                    "Export from the original .uexp first to create .hdr/.ftr sidecar files,\n"
                    "or select the original .uexp as a reference file."
                )

        self.progress.setValue(90)
        in_size = os.path.getsize(input_path)
        out_size = os.path.getsize(output_path)
        self._log(f"  Input  GFX size: {in_size} bytes")
        self._log(f"  Output UXP size: {out_size} bytes")
        self._log("[OK] Import successful!")

        self.progress.setValue(100)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = SwfToolGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
