"""Patient MSA fetcher for ColabFold's MMseqs2 API.

Boltz-2's built-in client has a tight retry budget and gives up after ~30-60s on slow
server responses ("Too many failed attempts"). This script polls until COMPLETE (or
error/timeout limit) and saves the resulting a3m to data/msa/<name>.a3m.

Usage:
    python scripts/fetch_msa.py --fasta data/phgdh_6CWA_chainA.fasta --name phgdh_6CWA_chainA
    python scripts/fetch_msa.py --seq MTPEG... --name custom_protein
"""
import argparse
import json
import shutil
import sys
import tarfile
import time
import urllib.request
import urllib.parse
from io import BytesIO
from pathlib import Path

import requests


HOST = "https://api.colabfold.com"


def submit(fasta_text: str, mode: str = "env") -> str:
    """Submit FASTA to ColabFold MSA endpoint, return ticket ID."""
    files = {"q": ("query.fasta", fasta_text)}
    data = {"mode": mode}
    r = requests.post(f"{HOST}/ticket/msa", files=files, data=data, timeout=30)
    r.raise_for_status()
    body = r.json()
    if body.get("status") not in {"PENDING", "RUNNING", "COMPLETE"}:
        raise RuntimeError(f"unexpected submit response: {body}")
    return body["id"]


def poll(ticket_id: str, max_wait_s: int = 600, step_s: int = 10) -> str:
    """Poll ticket until COMPLETE or ERROR or timeout."""
    t0 = time.time()
    last_status = None
    while time.time() - t0 < max_wait_s:
        r = requests.get(f"{HOST}/ticket/{ticket_id}", timeout=15)
        r.raise_for_status()
        status = r.json().get("status", "?")
        if status != last_status:
            print(f"  [{int(time.time()-t0):4d}s] {status}", flush=True)
            last_status = status
        if status == "COMPLETE":
            return status
        if status in {"ERROR", "UNKNOWN"}:
            raise RuntimeError(f"server reports {status}")
        time.sleep(step_s)
    raise TimeoutError(f"ticket still {last_status} after {max_wait_s}s")


def download(ticket_id: str, out_a3m: Path) -> int:
    """Download tar.gz, extract uniref.a3m, write to out_a3m. Return n lines."""
    r = requests.get(f"{HOST}/result/download/{ticket_id}", stream=True, timeout=60)
    r.raise_for_status()
    buf = BytesIO(r.content)
    # tarfile may complain about EOF but uniref.a3m is usually intact
    try:
        with tarfile.open(fileobj=buf, mode="r:gz") as tf:
            for member in tf.getmembers():
                if member.name == "uniref.a3m":
                    fobj = tf.extractfile(member)
                    if fobj is None:
                        raise RuntimeError("uniref.a3m extract returned None")
                    out_a3m.write_bytes(fobj.read())
                    return out_a3m.read_text().count("\n")
    except tarfile.ReadError:
        # Fall back to extracting via shell tar (more tolerant of EOF noise)
        import subprocess
        tmp = out_a3m.parent / f".tmp_{ticket_id[:8]}.tar.gz"
        tmp.write_bytes(buf.getvalue())
        subprocess.run(["tar", "xzf", str(tmp), "-C", str(out_a3m.parent)],
                       check=False, capture_output=True)
        extracted = out_a3m.parent / "uniref.a3m"
        if extracted.exists():
            shutil.move(str(extracted), str(out_a3m))
            tmp.unlink()
            return out_a3m.read_text().count("\n")
        tmp.unlink(missing_ok=True)
    raise RuntimeError("no uniref.a3m found in result tarball")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fasta", type=str, help="path to FASTA")
    p.add_argument("--seq", type=str, help="raw amino-acid sequence (alternative to --fasta)")
    p.add_argument("--name", required=True, help="output basename for data/msa/<name>.a3m")
    p.add_argument("--mode", default="env", choices=["env", "all"], help="MMseqs2 search mode")
    p.add_argument("--max-wait", type=int, default=600, help="max poll seconds")
    args = p.parse_args()

    if args.fasta:
        seq_text = Path(args.fasta).read_text()
    elif args.seq:
        seq_text = f">{args.name}\n{args.seq}\n"
    else:
        sys.exit("need --fasta or --seq")

    out = Path(__file__).resolve().parent.parent / "data" / "msa" / f"{args.name}.a3m"
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists() and out.stat().st_size > 1000:
        print(f"already cached: {out} ({out.stat().st_size:,} bytes)")
        return

    print(f"submit MSA for {args.name} (mode={args.mode})...")
    tid = submit(seq_text, mode=args.mode)
    print(f"ticket: {tid}")
    poll(tid, max_wait_s=args.max_wait)
    print(f"downloading to {out}...")
    n = download(tid, out)
    print(f"wrote {out} ({n} lines, {out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
