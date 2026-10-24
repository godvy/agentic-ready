"""Pre-compute every sample audit (guide x version x mode) so the demo works offline."""
import json
from concurrent.futures import ThreadPoolExecutor

from engine.pipeline import audit

CATALOG = json.load(open("samples/catalog.json", encoding="utf-8"))
CACHE_FILE = "samples/cached_results.json"


def cache_key(guide: str, version: str, mode: str) -> str:
    return f"{guide}:{version}:{mode}"


if __name__ == "__main__":
    jobs = [(g, v, m) for g in CATALOG for v in ("bad", "good") for m in ("instruct", "execute")]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = pool.map(lambda j: audit(CATALOG[j[0]][j[1]], CATALOG[j[0]]["tasks"][j[2]], j[2],
                                           reference=CATALOG[j[0]]["reference"]), jobs)
        cache = {cache_key(*j): {k: v for k, v in r.items() if k != "html"} for j, r in zip(jobs, results)}
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=1)
    for k, v in cache.items():
        print(f"{k:<28} {v['score']}")
