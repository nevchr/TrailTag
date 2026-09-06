from pathlib import Path


project_root = Path(SPECPATH)

analysis = Analysis(
    [str(project_root / "trailtag.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        *[(str(path), "packaging") for path in (project_root / "packaging").glob("arrow-*.svg")],
        (str(project_root / "README.md"), "."),
        (
            str(project_root / "packaging" / "trailtag.ico"),
            "packaging",
        ),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=False,
    optimize=0,
)

# Codex's workspace runtime puts unrelated Poppler/libheif DLLs on PATH.
# PyInstaller can otherwise mistake those for TrailTag dependencies; one of
# them has the same name as Windows' ICU library but an incompatible API.
analysis.binaries = [
    entry
    for entry in analysis.binaries
    if "codex-primary-runtime/dependencies/native"
    not in Path(entry[1]).as_posix().lower()
]

python_archive = PYZ(analysis.pure)

executable = EXE(
    python_archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="TrailTag",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "packaging" / "trailtag.ico"),
    version=str(
        project_root
        / "packaging"
        / "windows_version_info.txt"
    ),
)

distribution = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="TrailTag",
)
