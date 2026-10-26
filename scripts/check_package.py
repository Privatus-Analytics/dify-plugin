"""Checks a built .difypkg against the Dify Marketplace review rules.

Our own copy of the blocking rules from langgenius/dify-marketplace-toolkit
(manifest fields, PRIVACY.md, README, icon, dependencies, package contents),
so the package can be checked before the pull request.

Usage: python scripts/check_package.py dist/privatus_analytics-0.0.1.difypkg
"""

import py_compile
import re
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml

HOSTS = r"github\.com|gitlab\.com|bitbucket\.org|gitee\.com|codeberg\.org|git\.sr\.ht"
REPO_URL_RE = re.compile(rf"^https?://(?:www\.)?(?:{HOSTS})/[^\s)>\"]+$", re.I)
REPO_LINK_RE = re.compile(rf"https?://(?:www\.)?(?:{HOSTS})/[^\s)>\"]+", re.I)
EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")
CJK_RE = re.compile(r"[㐀-䶿一-鿿]")
REQUIRED = ["author", "name", "version", "type", "icon", "plugins", "privacy", "repo", "contact",
            "label.en_US", "description.en_US", "meta.version", "meta.arch", "meta.runner.language",
            "meta.runner.version", "meta.runner.entrypoint", "meta.minimum_dify_version"]
BLOCKED_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".ruff_cache",
                ".mypy_cache", ".tox", ".nox", ".idea", ".vscode", "node_modules", "pycache", "build", "dist", "tests"}
BLOCKED_FILES = {".DS_Store", ".gitconfig", "Thumbs.db", "desktop.ini", "id_rsa", ".env"}
BLOCKED_SUFFIXES = {".key", ".pem", ".p12", ".pfx", ".pyc", ".pyo", ".log", ".tmp", ".swp", ".swo", ".bak",
                    ".difypkg", ".so", ".dll", ".exe", ".dylib"}
SECRET_RE = re.compile(r"(pat_[A-Za-z0-9]{16,}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
DEFAULT_ICON = '<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><path d="M20 20 V80 M20 20 H60 Q80 20 80 40 T60 60 H20" fill="none" stroke="black" stroke-width="5"/></svg>'


def dig(doc, dotted):
    for key in dotted.split("."):
        if not isinstance(doc, dict):
            return None
        doc = doc.get(key)
    return doc


def main(package: str) -> int:
    errors: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(package) as archive:
            for name in archive.namelist():
                if name.startswith("/") or ".." in Path(name).parts:
                    errors.append(f"unsafe path in package: {name}")
            archive.extractall(root)
        files = [p for p in root.rglob("*") if p.is_file()]
        for path in files:
            rel = path.relative_to(root)
            if set(rel.parts[:-1]) & BLOCKED_DIRS:
                errors.append(f"development folder in package: {rel}")
            if rel.name in BLOCKED_FILES or rel.suffix in BLOCKED_SUFFIXES:
                errors.append(f"blocked file in package: {rel}")
            text = path.read_text(errors="ignore")
            if SECRET_RE.search(text):
                errors.append(f"looks like a secret in: {rel}")
            if rel.suffix == ".py":
                try:
                    py_compile.compile(str(path), doraise=True, cfile=str(Path(tmp) / "x.pyc"))
                except py_compile.PyCompileError as err:
                    errors.append(f"python does not compile: {rel}: {err.msg}")
        (Path(tmp) / "x.pyc").unlink(missing_ok=True)

        manifest = yaml.safe_load((root / "manifest.yaml").read_text())
        for field in REQUIRED:
            if dig(manifest, field) in (None, "", [], {}):
                errors.append(f"manifest is missing {field}")
        author = manifest.get("author", "")
        if "dify" in author or "langgenius" in author:
            errors.append("author must not contain dify or langgenius")
        if manifest.get("type") != "plugin":
            errors.append("type must be plugin")
        if not REPO_URL_RE.match(str(manifest.get("repo", ""))):
            errors.append("repo must be a URL on an allowed source host")
        if not EMAIL_RE.match(str(manifest.get("contact", ""))):
            errors.append("contact must be an email address")
        privacy = root / str(manifest.get("privacy", ""))
        if not (root / "PRIVACY.md").is_file() or not privacy.is_file():
            errors.append("PRIVACY.md is missing or privacy does not point at it")
        elif "please fill in the privacy policy" in privacy.read_text().lower():
            errors.append("PRIVACY.md still has the template text")

        for key in ("icon", "icon_dark"):
            if manifest.get(key):
                icon = root / "_assets" / manifest[key]
                if not icon.is_file():
                    errors.append(f"icon not found: _assets/{manifest[key]}")
                else:
                    content = icon.read_text(errors="ignore")
                    if "DIFY_MARKETPLACE_TEMPLATE_ICON_DO_NOT_USE" in content or re.sub(r"\s", "", content) == re.sub(r"\s", "", DEFAULT_ICON):
                        errors.append(f"icon is the template icon: {manifest[key]}")

        readme = (root / "README.md").read_text()
        if not REPO_LINK_RE.search(readme):
            errors.append("README has no source repository link")
        if CJK_RE.search(re.sub(r"```.*?```", "", readme, flags=re.S)):
            errors.append("README must be in English")
        lowered = readme.lower()
        for section, words in {"setup": ("setup", "install"), "usage": ("usage", "example"),
                               "credentials": ("token", "api key"), "connection": ("connection", "network")}.items():
            if not any(w in lowered for w in words):
                errors.append(f"README does not explain {section}")

        for line in (root / "requirements.txt").read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if not re.search(r"(==|~=|>=|<=|<|>)", line):
                errors.append(f"requirement without a version: {line}")
            if "git+" in line or "://" in line:
                errors.append(f"requirement from git or a URL: {line}")
            match = re.match(r"dify[_-]plugin\s*>=\s*([0-9.]+)", line)
            if line.lower().replace("-", "_").startswith("dify_plugin") and (not match or tuple(map(int, match.group(1).split(".")[:3])) < (0, 9, 0)):
                errors.append("dify_plugin must be >= 0.9.0")

        for rel in manifest["plugins"]["tools"]:
            provider = yaml.safe_load((root / rel).read_text())
            for tool in provider["tools"]:
                spec = yaml.safe_load((root / tool).read_text())
                if not (root / spec["extra"]["python"]["source"]).is_file():
                    errors.append(f"tool source missing: {spec['extra']['python']['source']}")

        print(f"{len(files)} files checked in {Path(package).name}")
    for error in errors:
        print(f"ERROR {error}")
    print("passed" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
