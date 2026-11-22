#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check whether a Tizen package's signatures chain to roots your watch trusts.

A Tizen watch only installs a package whose author and distributor signatures
chain to root certificates listed in its own trust store. This script reads the
signatures inside a .tpk/.wgt and compares their roots with a copy of the
watch's trust store, so you can tell in seconds whether an install can succeed.

Usage:
    # 1. Copy the trust store from your watch (debugging on, same Wi-Fi)
    sdb connect <watch-ip>:26101
    sdb pull /usr/share/ca-certificates ./watch-ca

    # 2. Check a package
    pip install cryptography
    python3 check_signature_trust.py MyFace.tpk --watch-ca ./watch-ca

Exit code is 0 when every signature chains to a trusted, non-revoked root,
and 1 otherwise. A trusted root is necessary but not sufficient: developer
roots also require your watch's device ID in the distributor certificate.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import sys
import warnings
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

try:
    from cryptography import x509
    from cryptography.hazmat.primitives.serialization import Encoding
except ImportError:  # pragma: no cover
    sys.exit("This script needs the 'cryptography' package: pip install cryptography")

# Some old Samsung-issued certificates carry empty country fields; that is harmless here.
warnings.filterwarnings("ignore", message="Attribute's length")

DSIG = "{http://www.w3.org/2000/09/xmldsig#}"
REVOKED_DOMAIN = "tizen-revoked"


@dataclass
class WatchRoot:
    path: Path
    cert: x509.Certificate
    sha1: str
    domains: set[str] = field(default_factory=set)


def sha1_colon(cert: x509.Certificate) -> str:
    digest = hashlib.sha1(cert.public_bytes(Encoding.DER)).hexdigest().upper()
    return ":".join(digest[i:i + 2] for i in range(0, len(digest), 2))


def common_name(name: x509.Name) -> str:
    attrs = name.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
    return attrs[0].value if attrs else name.rfc4514_string()


def load_fingerprint_domains(ca_dir: Path) -> dict[str, set[str]]:
    """Map SHA-1 fingerprint -> set of CertificateDomain names."""
    domains: dict[str, set[str]] = {}
    for xml_path in sorted(ca_dir.rglob("fingerprint_list*.xml")):
        root = ET.parse(xml_path).getroot()
        for domain in root.iter("CertificateDomain"):
            name = domain.get("name", "")
            for fp in domain.iter("FingerprintSHA1"):
                key = (fp.text or "").strip().upper()
                if key:
                    domains.setdefault(key, set()).add(name)
    return domains


def load_watch_roots(ca_dir: Path) -> list[WatchRoot]:
    fp_domains = load_fingerprint_domains(ca_dir)
    roots: list[WatchRoot] = []
    for pem_path in sorted(ca_dir.rglob("*.pem")):
        try:
            certs = x509.load_pem_x509_certificates(pem_path.read_bytes())
        except ValueError:
            continue
        for cert in certs:
            fp = sha1_colon(cert)
            roots.append(WatchRoot(pem_path, cert, fp, fp_domains.get(fp, set())))
    return roots


def signature_certs(xml_bytes: bytes) -> list[x509.Certificate]:
    root = ET.fromstring(xml_bytes)
    certs = []
    for node in root.iter(f"{DSIG}X509Certificate"):
        der = base64.b64decode("".join((node.text or "").split()))
        certs.append(x509.load_der_x509_certificate(der))
    return certs


def top_of_chain(certs: list[x509.Certificate]) -> x509.Certificate:
    """Return the certificate nearest the root (its issuer is not in the list)."""
    subjects = {c.subject for c in certs}
    for cert in certs:
        if cert.issuer == cert.subject or cert.issuer not in subjects:
            return cert
    return certs[-1]


def check(package: Path, ca_dir: Path) -> bool:
    roots = load_watch_roots(ca_dir)
    if not roots:
        sys.exit(f"No root certificates (*.pem) found under {ca_dir}")
    if not any(r.domains for r in roots):
        print("warning: no fingerprint_list*.xml found; trust levels cannot be read\n")

    with zipfile.ZipFile(package) as zf:
        sig_names = sorted(n for n in zf.namelist()
                           if n.endswith(".xml") and "signature" in n.rsplit("/", 1)[-1])
        if not sig_names:
            sys.exit(f"{package} contains no signature files: it is unsigned")
        all_ok = True
        for name in sig_names:
            certs = signature_certs(zf.read(name))
            if not certs:
                print(f"{name}: no certificates found")
                all_ok = False
                continue
            top = top_of_chain(certs)
            issuer = top.subject if top.issuer == top.subject else top.issuer
            chain = " -> ".join(common_name(c.subject) for c in certs)
            print(f"{name}")
            print(f"  chain : {chain} -> {common_name(issuer)}")

            matches = [r for r in roots if r.cert.subject == issuer]
            if not matches:
                print(f"  root  : {common_name(issuer)}")
                print("  result: NOT IN WATCH TRUST STORE  (install will fail: -12 / <-32>)")
                all_ok = False
            else:
                for r in matches:
                    doms = ", ".join(sorted(r.domains)) or "not listed"
                    print(f"  root  : {common_name(issuer)}  [{r.path.name}]  domains: {doms}")
                if any(REVOKED_DOMAIN in r.domains for r in matches):
                    print("  result: ROOT IS REVOKED ON THIS WATCH  (install will fail)")
                    all_ok = False
                elif any(r.domains for r in matches):
                    print("  result: trusted root")
                else:
                    print("  result: root present but not in any trust domain  (install will fail)")
                    all_ok = False
            print()
    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("package", type=Path, help=".tpk or .wgt file to check")
    parser.add_argument("--watch-ca", type=Path, required=True,
                        help="folder pulled from the watch: sdb pull /usr/share/ca-certificates ./watch-ca")
    args = parser.parse_args()
    ok = check(args.package, args.watch_ca)
    print("OVERALL:", "all signatures chain to trusted roots" if ok
          else "at least one signature will be rejected by this watch")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
