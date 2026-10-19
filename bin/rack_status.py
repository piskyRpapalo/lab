#!/usr/bin/env python3
"""Calculate a rack receipt stamp without changing its source."""
import argparse
import datetime as dt
import json

TTL_DAYS = 7
TTL_SECONDS = TTL_DAYS * 86400


def parse_utc(value):
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise argparse.ArgumentTypeError("timestamp must include UTC offset Z or +00:00")
    return parsed.astimezone(dt.timezone.utc)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--observed-at", required=True, type=parse_utc)
    parser.add_argument("--now", type=parse_utc, default=lambda: dt.datetime.now(dt.timezone.utc))
    args = parser.parse_args()
    age = max(0, int((args.now - args.observed_at).total_seconds()))
    state = "STALE" if age >= TTL_SECONDS else "LIVE"
    print(json.dumps({"state": state, "ttl_days": TTL_DAYS, "age_seconds": age,
                      "observed_at": args.observed_at.isoformat().replace("+00:00", "Z"),
                      "evaluated_at": args.now.isoformat().replace("+00:00", "Z")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
