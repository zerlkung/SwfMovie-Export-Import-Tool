# SwfMovie Export / Import Tool

Python GUI tool for Dead Island 2, Borderlands 3, Outlast 2 — export/import `.uexp` / `.swfmovie` ↔ `.gfx` font files with **auto-detect** header/footer (no hardcoded offsets).

## Install

```
pip install -r requirements.txt
```

## Run

```
python swf_tool.py
```

## Usage

### Export  `.uexp` / `.swfmovie` → `.gfx`

1. Select **EXPORT** mode
2. Choose input `.uexp` or `.swfmovie`
3. Output `.gfx` is auto-filled (appends `_1` if exists)
4. Click **Convert**

Creates:
- `filename.gfx` — editable GFX / Scaleform file
- `filename.gfx.hdr` — header bytes for later import
- `filename.gfx.ftr` — footer bytes for later import

### Edit the `.gfx`

Use any GFX/SWF editor (e.g. JPEXS Free Flash Decompiler, Scaleform GFx Editor).

### Import  `.gfx` → `.uexp` / `.swfmovie`

1. Select **IMPORT** mode
2. Choose edited `.gfx` file
3. Reference is auto-detected from original `.uexp` (same name)
4. Output `.uexp` is auto-filled
5. Click **Convert**

---

# SwfMovie Export / Import Tool (ภาษาไทย)

เครื่องมือ GUI สำหรับ Dead Island 2, Borderlands 3, Outlast 2 — export/import ไฟล์ฟอนต์ `.uexp` / `.swfmovie` ↔ `.gfx` โดย **ตรวจจับ header/footer อัตโนมัติ** (ไม่ต้อง hardcode offset)

## ติดตั้ง

```
pip install -r requirements.txt
```

## รัน

```
python swf_tool.py
```

## วิธีใช้

### Export  `.uexp` / `.swfmovie` → `.gfx`

1. เลือกโหมด **EXPORT**
2. เลือกไฟล์ input `.uexp` หรือ `.swfmovie`
3. ไฟล์ output `.gfx` เติมให้อัตโนมัติ (ถ้าซ้ำจะต่อ `_1`)
4. กด **Convert**

ไฟล์ที่ได้:
- `ชื่อไฟล์.gfx` — ไฟล์ GFX สำหรับแก้ไข
- `ชื่อไฟล์.gfx.hdr` — header เก็บไว้ใช้ตอน import
- `ชื่อไฟล์.gfx.ftr` — footer เก็บไว้ใช้ตอน import

### แก้ไข `.gfx`

ใช้โปรแกรมแก้ GFX/SWF เช่น JPEXS Free Flash Decompiler, Scaleform GFx Editor

### Import  `.gfx` → `.uexp` / `.swfmovie`

1. เลือกโหมด **IMPORT**
2. เลือกไฟล์ `.gfx` ที่แก้แล้ว
3. Reference ตรวจจับจาก `.uexp` ต้นฉบับอัตโนมัติ (ชื่อเดียวกัน)
4. ไฟล์ output `.uexp` เติมให้อัตโนมัติ
5. กด **Convert**

> **Note:** Header size field is automatically updated to match edited GFX data — no manual hex editing required.
>
> **หมายเหตุ:** อัปเดต size field ใน header ให้ตรงกับ GFX ที่แก้ไขแล้วอัตโนมัติ — ไม่ต้องแก้ hex เอง
