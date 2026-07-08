"""Check whether external DNS resolution works for the WM refresh dependencies."""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
from typing import Any

DEFAULT_HOSTS = [
    "raw.githubusercontent.com",
    "api.open-meteo.com",
    "ensemble-api.open-meteo.com",
    "archive-api.open-meteo.com",
    "site.api.espn.com",
    "aws-0-eu-west-1.pooler.supabase.com",
    "db.srcwznnkbhrtstqbkijx.supabase.co",
]
CRITICAL_HOSTS = [
    "raw.githubusercontent.com",
    "api.open-meteo.com",
    "site.api.espn.com",
    "aws-0-eu-west-1.pooler.supabase.com",
]


def check_dns_health(hosts: list[str] | None = None) -> dict[str, Any]:
    hosts = hosts or DEFAULT_HOSTS
    results = []
    for host in hosts:
        try:
            resolved = socket.getaddrinfo(host, None)
            addresses = sorted({item[4][0] for item in resolved})
            results.append({"host": host, "status": "ok", "addresses": addresses})
        except OSError as exc:
            results.append({"host": host, "status": "failed", "error": str(exc)})

    scutil_result = subprocess.run(
        ["scutil", "--dns"],
        capture_output=True,
        text=True,
        check=False,
    )
    scutil_excerpt = (scutil_result.stdout or scutil_result.stderr).strip().splitlines()[:20]
    host_status = {item["host"]: item["status"] for item in results}
    ok_hosts = [item["host"] for item in results if item["status"] == "ok"]
    failed_hosts = [item["host"] for item in results if item["status"] != "ok"]
    global_outage = not ok_hosts
    critical_outage = all(host_status.get(host) != "ok" for host in CRITICAL_HOSTS if host in host_status)

    summary = {
        "status": "ok" if all(item["status"] == "ok" for item in results) else "failed",
        "hosts": results,
        "ok_hosts": ok_hosts,
        "failed_hosts": failed_hosts,
        "global_outage": global_outage,
        "critical_outage": critical_outage,
        "scutil_status": "ok" if scutil_result.returncode == 0 else "unavailable",
        "scutil_dns_excerpt": scutil_excerpt,
    }
    if not scutil_excerpt:
        summary["notes"] = ["scutil returned no DNS excerpt; host-level resolution results above are authoritative."]
    if global_outage:
        summary.setdefault("notes", []).append(
            "No configured dependency host resolved successfully; treat this refresh as a hard infrastructure failure."
        )
    elif critical_outage:
        summary.setdefault("notes", []).append(
            "All critical refresh hosts failed DNS resolution; external refresh, DB import and live verification are not trustworthy."
        )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check DNS resolution for WM refresh dependencies")
    parser.add_argument("hosts", nargs="*")
    args = parser.parse_args(argv)
    result = check_dns_health(args.hosts or None)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
