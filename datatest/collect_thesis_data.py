"""
THESIS DATA COLLECTION SCRIPT
==============================
Prerequisites:
    pip install requests

How to run:
    1. Start your stack:    docker compose up -d
    2. Wait until translation-service is healthy (models finish loading)
    3. From your repo root: python collect_thesis_data.py
    4. Paste both output files to Claude:
           thesis_data_report.txt
           thesis_data_raw.json
"""

import subprocess, platform, json, time, statistics, sys, os, datetime

try:
    import requests
except ImportError:
    print("ERROR: run  pip install requests  then re-run.")
    sys.exit(1)

PRODUCT_URL      = "http://localhost:3000"
TRANSLATION_URL  = "http://localhost:3001"
TIMING_RUNS      = 7
TRANSLATION_TIMEOUT = 180

TEST_PRODUCTS = [
    {"name": "ASUS ROG Strix 27-inch Gaming Monitor",
     "description": "QHD 170Hz IPS display with 1ms response time, HDR400, and G-Sync compatible.",
     "price": 349.99, "target_languages": ["es","fr","de"], "category": "electronics"},
    {"name": "Logitech MX Master 3S Wireless Mouse",
     "description": "Advanced ergonomic mouse with 8000 DPI sensor, quiet clicks, and USB-C charging.",
     "price": 99.99,  "target_languages": ["es","fr","de"], "category": "electronics"},
    {"name": "Sony WH-1000XM5 Noise Cancelling Headphones",
     "description": "Industry-leading noise cancellation, 30-hour battery, multipoint Bluetooth connection.",
     "price": 279.99, "target_languages": ["es","fr","de"], "category": "electronics"},
    {"name": "Samsung 1TB NVMe SSD 980 Pro",
     "description": "PCIe 4.0 NVMe M.2 solid state drive with sequential read speed up to 7000 MB/s.",
     "price": 89.99,  "target_languages": ["es","fr","de"], "category": "electronics"},
    {"name": "Men's Merino Wool Crew Neck Sweater",
     "description": "100% extra-fine merino wool, machine washable, available in navy, grey, and burgundy.",
     "price": 69.99,  "target_languages": ["es","fr","de"], "category": "clothing"},
    {"name": "Women's Waterproof Hiking Jacket",
     "description": "Breathable 3-layer shell with sealed seams, adjustable hood, and pit-zip ventilation.",
     "price": 129.99, "target_languages": ["es","fr","de"], "category": "clothing"},
    {"name": "Unisex Cotton Canvas Tote Bag",
     "description": "Heavy-duty 12oz natural cotton canvas with reinforced handles, holds up to 22 lbs.",
     "price": 19.99,  "target_languages": ["es","fr","de"], "category": "clothing"},
    {"name": "Kids Fleece-Lined Winter Gloves",
     "description": "Touchscreen-compatible fingertips, adjustable wrist strap, available in sizes XS to L.",
     "price": 14.99,  "target_languages": ["es","fr","de"], "category": "clothing"},
    {"name": "Philips 3000 Series Air Purifier",
     "description": "HEPA filter removes 99.97% of particles, covers up to 480 sq ft, auto mode included.",
     "price": 159.99, "target_languages": ["es","fr","de"], "category": "home_appliances"},
    {"name": "Instant Pot Duo 7-in-1 Electric Pressure Cooker",
     "description": "6-quart capacity, pressure cooker, slow cooker, rice cooker, steamer, and saute pan.",
     "price": 89.99,  "target_languages": ["es","fr","de"], "category": "home_appliances"},
    {"name": "Dyson V12 Detect Slim Cordless Vacuum",
     "description": "Laser dust detection, LCD screen shows particle count, 60-min battery runtime.",
     "price": 649.99, "target_languages": ["es","fr","de"], "category": "home_appliances"},
    {"name": "Bosch 500 Series Dishwasher 44 dBA",
     "description": "PrecisionWash with intelligent sensors, third rack, 6 wash cycles, stainless steel tub.",
     "price": 849.99, "target_languages": ["es","fr","de"], "category": "home_appliances"},
    {"name": "Fitbit Charge 6 Advanced Fitness Tracker",
     "description": "Built-in GPS, heart rate monitoring, sleep tracking, 7-day battery, water resistant 50m.",
     "price": 149.99, "target_languages": ["es","fr","de"], "category": "sports"},
    {"name": "Yoga Mat Non-Slip 6mm Extra Thick",
     "description": "Eco-friendly TPE foam, moisture-resistant surface, includes carrying strap and bag.",
     "price": 34.99,  "target_languages": ["es","fr","de"], "category": "sports"},
    {"name": "Adjustable Dumbbell Set 5 to 52 Pounds",
     "description": "Replaces 15 sets of weights, dial selector adjusts in 2.5 lb increments, compact tray.",
     "price": 299.99, "target_languages": ["es","fr","de"], "category": "sports"},
    {"name": "Carbon Fiber Road Bicycle Helmet",
     "description": "MIPS protection system, 18 ventilation channels, aerodynamic shell, 240g lightweight.",
     "price": 119.99, "target_languages": ["es","fr","de"], "category": "sports"},
    {"name": "Organic Almond Milk Protein Shake Powder",
     "description": "25g plant protein per serving, almond milk base, no artificial sweeteners, gluten-free.",
     "price": 39.99,  "target_languages": ["es","fr","de"], "category": "food"},
    {"name": "Whole Grain Oat and Honey Granola Bar",
     "description": "Made with rolled oats, wildflower honey, and sunflower seeds. No high-fructose corn syrup.",
     "price": 8.99,   "target_languages": ["es","fr","de"], "category": "food"},
    {"name": "Cold-Pressed Extra Virgin Olive Oil 500ml",
     "description": "Single-origin Greek Koroneiki olives, harvested November 2024, acidity below 0.2%.",
     "price": 22.99,  "target_languages": ["es","fr","de"], "category": "food"},
    {"name": "Dark Roast Ethiopian Single Origin Coffee Beans",
     "description": "Whole bean 250g, tasting notes of dark chocolate and dried cherry, roasted weekly.",
     "price": 17.99,  "target_languages": ["es","fr","de"], "category": "food"},
]

def run_cmd(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"[ERROR: {e}]"

report_lines = []
raw_data = {}

def log(text=""):
    print(text)
    report_lines.append(str(text))

def section(title):
    bar = "=" * 60
    print(f"\n{bar}\n  {title}\n{bar}")
    report_lines.extend([f"\n{bar}", f"  {title}", bar])

def wait_for_translations(product_id, languages, timeout=TRANSLATION_TIMEOUT):
    """Poll until all requested language translations appear in the response list."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{TRANSLATION_URL}/translations/{product_id}", timeout=10)
            if r.status_code == 200:
                data = r.json()
                if not isinstance(data, list):
                    for key in ["translations", "items", "data"]:
                        if key in data and isinstance(data[key], list):
                            data = data[key]
                            break
                    else:
                        time.sleep(2)
                        continue
                present = {t.get("language") for t in data if t.get("language")}
                if all(lang in present for lang in languages):
                    return data, time.time() - start
        except Exception as e:
            print(f"  [polling error: {e}]")
        time.sleep(2)
    return [], time.time() - start

def extract_id(response_json):
    for key in ["id", "productId", "product_id"]:
        if key in response_json:
            return response_json[key]
    if "data" in response_json and isinstance(response_json.get("data"), dict):
        for key in ["id", "productId", "product_id"]:
            if key in response_json["data"]:
                return response_json["data"][key]
    return None

log("THESIS DATA COLLECTION — " + datetime.datetime.now().isoformat())
log()

# ── 1. SYSTEM INFO ────────────────────────────────────
section("1. SYSTEM INFORMATION")
log(f"Python: {sys.version}")
log()
log("-- Windows version --")
log(run_cmd("ver"))
log(f"platform: {platform.version()} / {platform.machine()}")
log()
log("-- CPU --")
log(run_cmd("wmic cpu get Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed /format:list"))
log()
log("-- RAM --")
log(run_cmd('systeminfo | findstr /C:"Total Physical Memory"'))
log()
log("-- Docker version --")
log(run_cmd("docker --version"))
log(run_cmd("docker compose version"))
log()
log("-- Docker resource limits (CPUs / Memory visible inside Docker) --")
log(run_cmd("docker info 2>&1 | findstr /I \"CPUs Memory\""))
log()
raw_data["system"] = {
    "python": sys.version,
    "os": platform.version(),
    "machine": platform.machine(),
    "cpu": run_cmd("wmic cpu get Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed /format:list"),
    "ram": run_cmd('systeminfo | findstr /C:"Total Physical Memory"'),
    "docker": run_cmd("docker --version"),
    "compose": run_cmd("docker compose version"),
    "docker_resources": run_cmd("docker info 2>&1 | findstr /I \"CPUs Memory\""),
}

# ── 2. DOCKER STATUS ──────────────────────────────────
section("2. DOCKER CONTAINER STATUS")
log(run_cmd("docker compose ps"))
log()
log("-- Images --")
log(run_cmd("docker images --format \"table {{.Repository}}\t{{.Tag}}\t{{.Size}}\""))
raw_data["docker_status"] = run_cmd("docker compose ps")

# ── 3. HEALTH CHECK ───────────────────────────────────
section("3. SERVICE HEALTH CHECK")
for name, url in [("product-service",    f"{PRODUCT_URL}/health"),
                  ("translation-service", f"{TRANSLATION_URL}/health")]:
    try:
        r = requests.get(url, timeout=10)
        log(f"{name}: HTTP {r.status_code}  body={r.text[:300]}")
    except Exception as e:
        log(f"UNREACHABLE: {name} — {e}")
        log("STOPPING. Run: docker compose up -d  and wait for models to load.")
        with open("thesis_data_report.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        sys.exit(1)

# ── 4. API RESPONSE TIME MEASUREMENT ─────────────────
section("4. API RESPONSE TIME MEASUREMENT")
log(f"Each endpoint called {TIMING_RUNS} times. Reporting median/min/max in ms.")
log()

timing_results = {}

def time_request(method, url, json_body=None, params=None, label=""):
    times, last_status = [], None
    fn = {"GET": requests.get, "POST": requests.post,
          "PUT": requests.put, "DELETE": requests.delete}[method]
    for _ in range(TIMING_RUNS):
        kw = {"timeout": 15}
        if json_body is not None: kw["json"] = json_body
        if params   is not None: kw["params"] = params
        t0 = time.perf_counter()
        try:
            r = fn(url, **kw)
            times.append((time.perf_counter() - t0) * 1000)
            last_status = r.status_code
        except Exception:
            pass
    v = sorted(times)
    med = round(statistics.median(v), 1) if v else None
    mn  = round(v[0], 1)  if v else None
    mx  = round(v[-1], 1) if v else None
    p95 = round(v[min(int(len(v)*0.95), len(v)-1)], 1) if v else None
    rec = {"label": label, "method": method, "status": last_status,
           "median_ms": med, "min_ms": mn, "max_ms": mx, "p95_ms": p95}
    log(f"  {method:6} {label:50}  median={med}ms  min={mn}ms  max={mx}ms  HTTP={last_status}")
    return rec

temp_r = requests.post(f"{PRODUCT_URL}/products",
    json={"name": "Timing Probe", "description": "Timing only", "price": 1.0, "target_languages": []},
    timeout=15).json()
temp_id = extract_id(temp_r)
log(f"  [Temp product id={temp_id}]")
log()
log("Product Service:")

timing_results["GET /products"] = time_request(
    "GET", f"{PRODUCT_URL}/products", label="GET /products")

if temp_id:
    timing_results["GET /products/:id"] = time_request(
        "GET", f"{PRODUCT_URL}/products/{temp_id}", label="GET /products/:id")
    timing_results["GET /products/:id?lang=es"] = time_request(
        "GET", f"{PRODUCT_URL}/products/{temp_id}", params={"lang": "es"},
        label="GET /products/:id?lang=es")

timing_results["POST /products (no translation)"] = time_request(
    "POST", f"{PRODUCT_URL}/products",
    json_body={"name": "Post Probe", "description": "desc", "price": 1.0, "target_languages": []},
    label="POST /products (no translation)")

timing_results["POST /products (translation trigger)"] = time_request(
    "POST", f"{PRODUCT_URL}/products",
    json_body={"name": "Post Probe Translated", "description": "Nice product description for timing.",
               "price": 9.99, "target_languages": ["es","fr","de"]},
    label="POST /products (translation fired)")

if temp_id:
    timing_results["PUT /products/:id"] = time_request(
        "PUT", f"{PRODUCT_URL}/products/{temp_id}",
        json_body={"name": "Updated Probe", "description": "Updated.", "price": 2.0, "target_languages": []},
        label="PUT /products/:id (no translation)")

log()
log("  [Creating product for DELETE timing, waiting for 1 language translation...]")
del_r = requests.post(f"{PRODUCT_URL}/products",
    json={"name": "Delete Probe", "description": "Will be deleted.", "price": 3.0, "target_languages": ["es"]},
    timeout=15).json()
del_id = extract_id(del_r)
if del_id:
    wait_for_translations(del_id, ["es"])
    timing_results["DELETE /products/:id"] = time_request(
        "DELETE", f"{PRODUCT_URL}/products/{del_id}",
        label="DELETE /products/:id (sync translation cleanup)")

timing_results["GET /health (product)"] = time_request(
    "GET", f"{PRODUCT_URL}/health", label="GET /health")

log()
log("Translation Service:")
timing_results["GET /translations"]            = time_request("GET", f"{TRANSLATION_URL}/translations",            label="GET /translations")
timing_results["GET /translations/statistics"] = time_request("GET", f"{TRANSLATION_URL}/translations/statistics", label="GET /translations/statistics")
timing_results["GET /dashboard"]               = time_request("GET", f"{TRANSLATION_URL}/dashboard",               label="GET /dashboard")
timing_results["GET /health (translation)"]    = time_request("GET", f"{TRANSLATION_URL}/health",                  label="GET /health")

raw_data["timing"] = timing_results

# ── 5. PIPELINE TIMING ────────────────────────────────
section("5. TRANSLATION PIPELINE TIMING (end-to-end)")
log("Time from POST /products until all 3 translations appear in GET /translations/{id}")
log()

pipeline_probes = [
    {"name": "Smart LED Desk Lamp",
     "description": "Adjustable color temperature 2700K to 6500K, USB-C charging port, memory function.",
     "price": 45.0, "target_languages": ["es","fr","de"]},
    {"name": "Stainless Steel Water Bottle 750ml",
     "description": "Double-wall vacuum insulation keeps drinks cold 24h or hot 12h, leak-proof lid.",
     "price": 29.0, "target_languages": ["es","fr","de"]},
    {"name": "Wireless Bluetooth Speaker Portable",
     "description": "360-degree sound, IPX7 waterproof, 20-hour battery, built-in microphone for calls.",
     "price": 79.0, "target_languages": ["es","fr","de"]},
]

pipeline_results = []
for prod in pipeline_probes:
    log(f"  Creating: '{prod['name']}'")
    t0 = time.perf_counter()
    r  = requests.post(f"{PRODUCT_URL}/products", json=prod, timeout=15)
    post_ms = (time.perf_counter() - t0) * 1000
    prod_id = extract_id(r.json())
    log(f"    POST returned {post_ms:.0f}ms  id={prod_id} — waiting...")
    translations, wait_sec = wait_for_translations(prod_id, prod["target_languages"])
    log(f"    All {len(translations)} translations present after {wait_sec:.1f}s from POST")
    for t in translations:
        log(f"      lang={t.get('language')}  created_at={t.get('created_at')}")
    pipeline_results.append({
        "product_name": prod["name"],
        "product_id": prod_id,
        "post_response_ms": round(post_ms, 1),
        "all_translations_present_sec": round(wait_sec, 1),
        "translation_count": len(translations),
        "created_ats": [{"lang": t.get("language"), "created_at": t.get("created_at")} for t in translations],
    })

raw_data["pipeline_timing"] = pipeline_results

# ── 6. DOCKER RESOURCE USAGE ─────────────────────────
section("6. DOCKER RESOURCE USAGE")
log("-- Active snapshot (~3s after triggering a translation) --")
snap_r  = requests.post(f"{PRODUCT_URL}/products",
    json={"name": "Resource Probe", "description": "Resource monitoring test.", "price": 1.0,
          "target_languages": ["es","fr","de"]}, timeout=15).json()
snap_id = extract_id(snap_r)
time.sleep(3)
active_stats = run_cmd("docker stats --no-stream --format \"table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\"")
log(active_stats)
log()

log("-- Idle snapshot (after translation completes) --")
wait_for_translations(snap_id, ["es","fr","de"])
time.sleep(3)
idle_stats = run_cmd("docker stats --no-stream --format \"table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\"")
log(idle_stats)

raw_data["docker_stats_active"] = active_stats
raw_data["docker_stats_idle"]   = idle_stats

# ── 7. TRANSLATION QUALITY TEST SET ──────────────────
section("7. TRANSLATION QUALITY TEST SET (20 products)")
log(f"Creating {len(TEST_PRODUCTS)} products and collecting translations.")
log()

quality_results = []
for i, prod in enumerate(TEST_PRODUCTS):
    log(f"  [{i+1:02}/{len(TEST_PRODUCTS)}] {prod['name'][:55]}")
    r = requests.post(f"{PRODUCT_URL}/products", json={
        "name": prod["name"], "description": prod["description"],
        "price": prod["price"], "target_languages": prod["target_languages"],
    }, timeout=15)
    if r.status_code not in (200, 201):
        log(f"    ERROR {r.status_code}: {r.text[:150]}")
        continue
    prod_id = extract_id(r.json())
    quality_results.append({
        "product_id": prod_id, "category": prod["category"],
        "source_name": prod["name"], "source_description": prod["description"],
        "translations": {},
    })
    log(f"    queued id={prod_id}")
    time.sleep(0.3)

log()
log("Collecting translations (waiting for each to appear)...")
log()

for i, entry in enumerate(quality_results):
    pid = entry["product_id"]
    if not pid:
        continue
    log(f"  [{i+1:02}/{len(quality_results)}] id={pid} [{entry['category']}]")
    translations, wait_sec = wait_for_translations(pid, ["es","fr","de"])
    log(f"    {len(translations)} translations in {wait_sec:.1f}s")
    for t in translations:
        lang = t.get("language", "unknown")
        entry["translations"][lang] = {
            "translated_name":        t.get("translated_name"),
            "translated_description": t.get("translated_description"),
            "original_name":          t.get("original_name"),
            "original_description":   t.get("original_description"),
            "is_edited":              t.get("is_edited"),
            "created_at":             t.get("created_at"),
            "confidence":             None,   # not in your API response
            "status":                 "completed",
        }

log()
log("--- Sample: first product ---")
if quality_results:
    e = quality_results[0]
    log(f"id={e['product_id']}  [{e['category']}]")
    log(f"  SRC name: {e['source_name']}")
    log(f"  SRC desc: {e['source_description']}")
    for lang, t in e["translations"].items():
        log(f"  [{lang}] name: {t['translated_name']}")
        log(f"  [{lang}] desc: {t['translated_description']}")

raw_data["quality_test_set"] = quality_results

# ── 8. EXISTING TEST SUITE ────────────────────────────
section("8. test_services.py OUTPUT")
if os.path.exists("test_services.py"):
    log("Running test_services.py ...")
    result = subprocess.run([sys.executable, "test_services.py"],
                            capture_output=True, text=True, timeout=300)
    output = result.stdout + result.stderr
    log(output)
    raw_data["test_services_output"]     = output
    raw_data["test_services_returncode"] = result.returncode
else:
    log("WARNING: test_services.py not found. Run from repo root.")
    raw_data["test_services_output"] = "NOT FOUND"

# ── 9. NETWORK ISOLATION ──────────────────────────────
section("9. NETWORK ISOLATION VERIFICATION")
log("-- Docker networks --")
log(run_cmd("docker network ls"))
log()
for label, candidates in [
    ("product-service",     ["thesis-product-service-1",     "product-service"]),
    ("translation-service", ["thesis-translation-service-1", "translation-service"]),
    ("product-db",          ["thesis-product-db-1",           "product-db"]),
    ("translation-db",      ["thesis-translation-db-1",       "translation-db"]),
]:
    for name in candidates:
        out = run_cmd(f"docker inspect {name} --format \"{{{{json .NetworkSettings.Networks}}}}\" 2>&1")
        if "error" not in out.lower()[:20]:
            log(f"-- {label} ({name}) --")
            log(out[:600])
            log()
            break

log("-- Cross-DB access test (expects FAILURE) --")
log("Trying to reach product-db:5432 from translation-service:")
for container in ["thesis-translation-service-1", "translation-service"]:
    out = run_cmd(f"docker exec {container} python3 -c \"import socket; s=socket.socket(); s.settimeout(5); s.connect(('product-db',5432)); print('CONNECTED')\" 2>&1")
    if "[ERROR" not in out[:15]:
        log(f"  [{container}]: {out[:400]}")
        break

raw_data["network_isolation"] = run_cmd("docker network ls")

# ── 10. STATISTICS ENDPOINT ───────────────────────────
section("10. TRANSLATION STATISTICS")
try:
    r = requests.get(f"{TRANSLATION_URL}/translations/statistics", timeout=15)
    log(f"HTTP {r.status_code}")
    log(json.dumps(r.json(), indent=2, ensure_ascii=False))
    raw_data["translation_statistics"] = r.json()
except Exception as e:
    log(f"ERROR: {e}")
    raw_data["translation_statistics"] = str(e)

# ── 11. RAW TRANSLATION SAMPLE ────────────────────────
section("11. RAW TRANSLATION RESPONSE SAMPLE")
if quality_results and quality_results[0]["product_id"]:
    r = requests.get(f"{TRANSLATION_URL}/translations/{quality_results[0]['product_id']}", timeout=10)
    log(f"GET /translations/{quality_results[0]['product_id']} → HTTP {r.status_code}")
    log(json.dumps(r.json(), indent=2, ensure_ascii=False)[:4000])
    raw_data["raw_translation_sample"] = r.json()

# ── WRITE FILES ───────────────────────────────────────
section("WRITING OUTPUT FILES")
with open("thesis_data_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))
with open("thesis_data_raw.json", "w", encoding="utf-8") as f:
    json.dump(raw_data, f, indent=2, ensure_ascii=False, default=str)

print()
print("=" * 60)
print("  DONE — paste both files to Claude:")
print("  thesis_data_report.txt")
print("  thesis_data_raw.json")
print("=" * 60)