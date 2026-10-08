"""Resolve safe versions and publication intent for portable builds."""
import re

VERSION_PATTERN = r"v\d+\.\d+\.\d+(?:-(?:alpha|beta|rc|preview)[.-]\d+)?"


def resolve_release(event, ref_type, ref_name, requested_version="", publish=False, run_number="0"):
    requested_version = requested_version.strip()
    if event == "push":
        if ref_type != "tag":
            raise ValueError("Automatic releases require a version tag")
        version, publish, create_tag = ref_name, True, False
    elif event == "workflow_dispatch":
        if ref_type == "tag":
            if requested_version and requested_version != ref_name:
                raise ValueError("Version input must match the selected tag")
            version, create_tag = ref_name, False
        else:
            if publish and not requested_version:
                raise ValueError("Enter an explicit version to create a draft release from a branch")
            if not str(run_number).isdigit():
                raise ValueError("Invalid workflow run number")
            version = requested_version or f"v0.0.0-preview.{run_number}"
            create_tag = publish
    else:
        raise ValueError("Unsupported release event")
    if not re.fullmatch(VERSION_PATTERN, version):
        raise ValueError("Use vX.Y.Z or a numbered alpha, beta, rc, or preview suffix (dot or hyphen)")
    return {"tag": version, "publish": str(publish).lower(), "create_tag": str(create_tag).lower()}
