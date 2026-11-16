"""Generic native builder. Application source and detailed logs stay private.

This file contains no experiment source or credentials and may be published as
the public build recipe. Inputs and logs use authenticated Fernet encryption;
the short-lived key is a repository secret. No Actions artifacts/cache are used.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import traceback

from cryptography.fernet import Fernet


def unpack_request(token, key, destination, expected_source):
    """Authenticate before extracting; accept a fixed, two-file envelope."""
    plain = Fernet(key).decrypt(token)
    with tarfile.open(fileobj=io.BytesIO(plain), mode="r:gz") as envelope:
        members = envelope.getmembers()
        if ({m.name for m in members} != {"request.json", "source.tar.gz"}
                or len(members) != 2 or not all(m.isfile() for m in members)):
            raise ValueError("Invalid build envelope")
        request = json.load(envelope.extractfile("request.json"))
        source = envelope.extractfile("source.tar.gz").read()
    if (not re.fullmatch(r"[0-9a-f]{40}", expected_source)
            or request.get("source_sha") != expected_source
            or not re.fullmatch(r"[a-z][a-z0-9-]*", request.get("app", ""))
            or type(request.get("version")) is not int or request["version"] < 1
            or hashlib.sha256(source).hexdigest() != request.get("source_archive_sha256")):
        raise ValueError("Build request did not match the selected source")
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(source), mode="r:gz") as archive:
        archive.extractall(destination, filter="data")
    manifest = json.loads((destination / "experiments" / request["app"] / "experiment.json").read_text())
    if manifest["version"] != request["version"]:
        raise ValueError("Application version does not match the request")
    return request


def check_target(target):
    actual = (platform.system(), platform.machine().lower(), struct.calcsize("P"))
    wanted = {"windows-x64": "Windows", "linux-x64": "Linux"}
    if (target not in wanted or actual[0] != wanted[target]
            or actual[1] not in {"amd64", "x86_64"} or actual[2] != 8):
        raise ValueError("The build must run on the selected native x64 system")


def gh(*args, **kwargs):
    return subprocess.run(["gh", *args], check=True, **kwargs)


def run_build(args):
    check_target(args.target)
    if (os.environ.get("GITHUB_REPOSITORY") != "IanWHunter/mica-course-downloads"
            or not re.fullmatch(r"course-build-[a-z0-9-]+", args.tag)
            or not re.fullmatch(r"[0-9a-f]{64}", args.cipher_sha)):
        raise ValueError("Unrecognized build context")
    key = os.environ.pop("MICA_BUILD_INPUT_KEY").encode()
    cipher = Fernet(key)
    repo = "github.com/" + os.environ["GITHUB_REPOSITORY"]
    stages = []
    success = False
    with tempfile.TemporaryDirectory(prefix="mica-native-") as work:
        work = Path(work)
        logfile = work / "build.log"
        try:
            gh("release", "download", args.tag, "--repo", repo,
               "--pattern", "input.fernet", "--dir", str(work),
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            token = (work / "input.fernet").read_bytes()
            if hashlib.sha256(token).hexdigest() != args.cipher_sha:
                raise ValueError("Encrypted input digest did not match")
            source = work / "source"
            request = unpack_request(token, key, source, args.source)
            folder = source / "experiments" / request["app"]
            output = work / "output"
            environment = dict(os.environ)
            for name in ("GH_TOKEN", "GITHUB_TOKEN", "MICA_BUILD_INPUT_KEY",
                         "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN"):
                environment.pop(name, None)
            environment["MPLCONFIGDIR"] = str(work / "mpl")
            environment["MICA_DWF_PATH"] = str(work / "no-physical-hardware")
            commands = [
                ("dependencies", [sys.executable, "-m", "pip", "install", "pyinstaller==6.21.0",
                                   "-r", str(folder / "requirements.txt")]),
                ("release checks", [sys.executable, "-m", "unittest", "discover", "-s", "tests"]),
                ("native package and app checks", [sys.executable, "course_release/build.py",
                                                    str(folder), args.target, str(output)]),
            ]
            with logfile.open("w", encoding="utf-8") as log:
                for label, command in commands:
                    print(label + "...", flush=True)
                    result = subprocess.run(command, cwd=source, env=environment,
                                            stdout=log, stderr=subprocess.STDOUT, timeout=2700)
                    stages.append(dict(stage=label, exit_code=result.returncode))
                    if result.returncode:
                        raise RuntimeError("Native build stage failed")
            extension = ".zip" if args.target == "windows-x64" else ".tar.gz"
            artifact = output / f"{request['app']}-{request['version']}-{args.target}{extension}"
            if not artifact.is_file() or len(list(output.iterdir())) != 1:
                raise RuntimeError("Expected exactly one native app archive")
            with artifact.open("rb") as file:
                digest = hashlib.file_digest(file, "sha256").hexdigest()
            proof = dict(source_sha=request["source_sha"], version=request["version"],
                         target=args.target, native_system=platform.system(),
                         machine=platform.machine(), python=sys.version.split()[0],
                         archive=artifact.name, bytes=artifact.stat().st_size, sha256=digest,
                         stages=stages, packaged_startup_passed=True,
                         physical_hardware_used=False, app_source_published=False)
            report = work / (args.target + "-verification.json")
            report.write_text(json.dumps(proof, indent=2), encoding="utf-8")
            gh("release", "upload", args.tag, str(artifact), str(report), "--repo", repo,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            success = True
        except BaseException:
            with logfile.open("a", encoding="utf-8") as log:
                traceback.print_exc(file=log)
        finally:
            # Compiler and test traces may quote private source: encrypt them.
            encrypted = work / (args.target + "-build.log.fernet")
            encrypted.write_bytes(cipher.encrypt(logfile.read_bytes()))
            gh("release", "upload", args.tag, str(encrypted), "--repo", repo,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Native package checks passed." if success else "Build failed; encrypted diagnostics retained.", flush=True)
    return 0 if success else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--cipher-sha", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", choices=("windows-x64", "linux-x64"), required=True)
    try:
        raise SystemExit(run_build(parser.parse_args()))
    except Exception:
        # Never send private exception traces to the public workflow log.
        print("The build could not finish; review the private build diagnostics.", flush=True)
        raise SystemExit(1)
