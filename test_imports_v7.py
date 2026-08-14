import sys
sys.path.insert(0, r'C:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6')
import os
os.chdir(r'C:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6')

results = []

try:
    from modules.session.snapshots import RequestSnapshot
    results.append("PASS: modules.session.snapshots.RequestSnapshot")
except Exception as e:
    results.append(f"FAIL: modules.session.snapshots - {e}")

try:
    from modules.transport.browser_seed_bundle import BrowserSeedBundle
    results.append("PASS: modules.transport.browser_seed_bundle.BrowserSeedBundle")
except Exception as e:
    results.append(f"FAIL: modules.transport.browser_seed_bundle - {e}")

try:
    from modules.session import SnapshotStore
    results.append("PASS: modules.session.SnapshotStore")
except Exception as e:
    results.append(f"FAIL: modules.session SnapshotStore - {e}")

try:
    from modules.transport import BrowserSeeder
    results.append("PASS: modules.transport.BrowserSeeder")
except Exception as e:
    results.append(f"FAIL: modules.transport.BrowserSeeder - {e}")

try:
    from modules.session import BlackBoxRecorder
    results.append("PASS: modules.session.BlackBoxRecorder")
except Exception as e:
    results.append(f"FAIL: modules.session.BlackBoxRecorder - {e}")

try:
    from modules.session import global_snapshot_store, ShapeDrift
    results.append("PASS: modules.session global_snapshot_store, ShapeDrift")
except Exception as e:
    results.append(f"FAIL: modules.session global_snapshot_store - {e}")

try:
    from modules.session.context import ReservationSessionContext
    results.append("PASS: modules.session.context.ReservationSessionContext")
except Exception as e:
    results.append(f"FAIL: modules.session.context - {e}")

try:
    from modules.webook.client import WebookApiClient
    results.append("PASS: modules.webook.client.WebookApiClient")
except Exception as e:
    results.append(f"FAIL: modules.webook.client - {e}")

print("=" * 60)
for r in results:
    print(r)
print("=" * 60)
passed = sum(1 for r in results if r.startswith("PASS"))
print(f"Result: {passed}/{len(results)} passed")
