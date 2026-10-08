"""Build, extract, and smoke-test a Windows x64 portable release."""
import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(version):
    if not re.fullmatch(r"v\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?", version):
        raise ValueError("Use vX.Y.Z or vX.Y.Z-alpha.N / beta.N / rc.N")
    if sys.platform != "win32" or platform.machine().lower() not in ("amd64", "x86_64") or sys.maxsize <= 2**32:
        raise RuntimeError("Build with 64-bit Python on Windows x64")
    # Every invocation has its own staging area, so stale files cannot enter the ZIP.
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=artifacts, prefix="portable-") as temporary:
        staging = Path(temporary)
        subprocess.run([
            sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
            "--onedir", "--windowed", "--noupx", "--name", "LtATC",
            "--distpath", str(staging / "dist"), "--workpath", str(staging / "build"),
            "--specpath", str(staging), "--add-data", f"{ROOT / 'assets'}:assets", str(ROOT / "main.py"),
        ], cwd=ROOT, check=True)
        bundle = staging / "dist" / "LtATC"
        for name in ("README.md", "LICENSE"):
            shutil.copy2(ROOT / name, bundle / name)
        (bundle / "PLAY.txt").write_text(
            f"LtATC {version} - Windows x64 portable edition\n\n"
            "Extract the entire ZIP, then open LtATC.exe. Keep _internal beside it.\n"
            "Python and an installer are not required.\n"
            "Progress is saved in %LOCALAPPDATA%\\LtATC\\progress.json.\n"
            "Educational game only; never use for operational ATC training.\n",
            encoding="utf-8")
        filename = f"LtATC-{version}-Windows-x64"
        candidate = Path(shutil.make_archive(str(staging / filename), "zip", bundle.parent, "LtATC"))
        extracted = staging / "extracted"
        shutil.unpack_archive(candidate, extracted)
        # Launch away from the source tree: assets must come from the ZIP.
        isolated = staging / "smoke"
        isolated.mkdir()
        environment = os.environ.copy()
        environment["LOCALAPPDATA"] = str(isolated)
        environment["TEMP"] = environment["TMP"] = str(isolated)
        environment.pop("PYTHONPATH", None)
        report = isolated / "report.json"
        process = subprocess.run([str(extracted / "LtATC" / "LtATC.exe"), "--smoke-test", str(report)],
                                 cwd=isolated, env=environment, timeout=60,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
        if not report.exists():
            raise RuntimeError(f"Packaged game produced no smoke report (exit {process.returncode})")
        details = json.loads(report.read_text(encoding="utf-8"))
        if process.returncode != 0 or details.get("ok") is not True:
            raise RuntimeError(f"Packaged smoke test failed: {details}")
        shutil.copy2(report, artifacts / f"{filename}-smoke.json")
        output = artifacts / candidate.name
        shutil.copy2(candidate, output)
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        output.with_suffix(".zip.sha256").write_text(f"{digest}  {output.name}\n", encoding="ascii")
        print(f"Verified portable ZIP: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    build(parser.parse_args().version)
