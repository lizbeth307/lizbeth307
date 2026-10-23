#!/bin/bash
# Runs only inside the dedicated, disconnected ARM64 guest.
set -eu
export DEBIAN_FRONTEND=noninteractive PIP_NO_INDEX=1 PIP_DISABLE_PIP_VERSION_CHECK=1
export ORT_DISABLE_TELEMETRY=1 QT_QPA_PLATFORM=offscreen QT_OPENGL=software
payload=/mnt/srrx-payload
results=/var/lib/srrx-linux-lab/results
# Refuse execution on the host or on a physical ARM board, before any writes.
test "$(id -u)" = 0
test "$(uname -m)" = aarch64
test "$(cat /proc/1/comm)" = systemd
python3 -I -B - <<'PY'
from pathlib import Path
if b'linux,dummy-virt' not in Path('/proc/device-tree/compatible').read_bytes().split(b'\0'):
    raise SystemExit('Dedicated QEMU virt guest required')
PY
mkdir -p "$results"
mount -t ext4 /dev/disk/by-label/SRRXRESULT "$results"
exec > >(tee -a "$results/bootstrap.log" /dev/console) 2>&1
python3 -I -B - "$payload/lab-clock.json" <<'PY'
import json,sys,time
from pathlib import Path
record=json.loads(Path(sys.argv[1]).read_text())
# This explicit software-lab clock never qualifies GNSS UTC or a device RTC.
time.clock_settime(time.CLOCK_REALTIME,record['host_unix_time_s']+time.monotonic())
print('Software lab clock set from host preparation timestamp; not GNSS')
PY
finish() {
    local code=$?
    trap - EXIT
    python3 - "$results" "$code" <<'PY'
import json,platform,sys,hashlib
from pathlib import Path
p=Path(sys.argv[1]);reports={}
for name in ('dependency-verification.json','software-tests.json','system-smoke.json','pty-smoke.json','gui-smoke.json','xcb-smoke.json','rx-worker-smoke.json','storage-smoke.json','module-lab/report.json'):
 try:reports[name]=json.loads((p/name).read_text())
 except (OSError,ValueError):reports[name]={'status':'MISSING_OR_INVALID'}
states={k:v.get('status',v.get('host_regression_status','UNKNOWN')) if type(v) is dict else 'INVALID' for k,v in reports.items()}
# wasSuccessful() ignores skips. Only documented gaps outside the locked guest
# wheelhouse may skip, each once; NumPy/Qt/ORT/compiler skips fail the run.
allowed={'Actual QNN HTP SDK library unavailable; no real manifest was generated',
 'PyMuPDF is not installed in this environment'}
u=reports['software-tests.json'];skipped=u.get('skipped',[]) if type(u) is dict else None
if states['software-tests.json']=='PASS' and (u.get('failures') or u.get('errors') or type(skipped) is not list
  or any(type(s) is not dict for s in skipped) or len({s.get('reason') for s in skipped})!=len(skipped)
  or any(s.get('reason') not in allowed for s in skipped)):
 states['software-tests.json']='PASS_WITH_UNEXPECTED_SKIPS'
expected={k:'PASS' for k in states};expected['gui-smoke.json']='PASS_LINUX_OFFSCREEN_SIMULATION'
expected['module-lab/report.json']='EMULATION_PASS_WITH_GAPS'
ok=int(sys.argv[2])==0 and states==expected
report={'schema_version':1,'status':'PASS' if ok else 'FAIL','bootstrap_exit_code':int(sys.argv[2]),
 'environment':{'architecture':platform.machine(),'kernel':platform.release(),
 'pid1':Path('/proc/1/comm').read_text().strip(),'os_release':Path('/etc/os-release').read_text(),
 'clock_source':'host preparation timestamp plus guest uptime; not GNSS qualification'},
 'suites':states,'physical_tests_performed':False,'hardware_qualified':False,
 'network_devices':[],'q6a_peripherals_emulated':False}
(p/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
print('SRRX_LINUX_LAB_RESULT',json.dumps(report))
PY
    sync
    systemctl poweroff --no-block
}
trap finish EXIT
python3 - "$payload" <<'PY'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1])
for x in json.loads((p/'payload-manifest.json').read_text()):
 f=p/x['path']
 if not f.is_file() or f.stat().st_size!=x['bytes'] or hashlib.sha256(f.read_bytes()).hexdigest()!=x['sha256']:
  raise SystemExit('Payload integrity mismatch: '+x['path'])
print('Payload hashes PASS')
PY
umask 022
# A cached guest's packages/venv are never trusted: reinstall every locked,
# hash-verified deb (no same-version skip) and recreate the venv below.
if compgen -G "$payload/debs/*.deb" > /dev/null; then
    dpkg -i "$payload"/debs/*.deb > "$results/dpkg-install.log" 2>&1
fi
systemctl stop srrx-linux-lab-sim.service srrx.service 2>/dev/null || true
# Remove only state that earlier lab smokes created in this marked guest, so
# changed units are reinstalled; guest_smoke still refuses foreign units/records.
rm -f /etc/systemd/system/srrx.service /etc/systemd/system/srrx-linux-lab-sim.service
rm -rf /etc/systemd/system/srrx.service.d
rm -f /etc/srrx/acceptance.json /etc/srrx/devices.json /etc/srrx/devices.env /etc/srrx/release.json /etc/srrx/build-manifest.json
systemctl daemon-reload
# Replace previous sources and venv with this exact manifest, owned by root.
mkdir -p /opt/srrx
find /opt/srrx -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
tar --no-same-owner --no-same-permissions -xzf "$payload/project.tar.gz" -C /opt/srrx
python3 - "$payload" <<'PY'
import hashlib,json,sys
from pathlib import Path
p=Path('/opt/srrx');payload=Path(sys.argv[1])
for x in json.loads((payload/'project-manifest.json').read_text()):
 f=p/x['path']
 if not f.is_file() or f.stat().st_size!=x['bytes'] or hashlib.sha256(f.read_bytes()).hexdigest()!=x['sha256']:
  raise SystemExit('Installed integrity mismatch: '+x['path'])
print('Installed project hashes PASS')
PY
groupadd -f labd
groupadd -f i2c
groupadd -f dialout
id labd >/dev/null 2>&1 || useradd --system --gid labd --home-dir /var/lib/srrx --shell /usr/sbin/nologin labd
id labclient >/dev/null 2>&1 || useradd --create-home --groups labd --shell /bin/bash labclient
cat > /etc/srrx-linux-lab.json <<'JSON'
{"schema_version":1,"environment":"qemu-arm64-linux-lab","hardware_passthrough":false}
JSON
python3 -m venv --clear --without-pip /opt/srrx/venv
pipwheel=$(find "$payload/wheels" -maxdepth 1 -name 'pip-*.whl' -print -quit)
test -n "$pipwheel"
PYTHONPATH="$pipwheel" /opt/srrx/venv/bin/python3 -m pip install --no-index --find-links "$payload/wheels" pip setuptools wheel > "$results/pip-bootstrap.log" 2>&1
# pip hashes only archives it installs: force every locked wheel through --require-hashes.
/opt/srrx/venv/bin/python3 -m pip install --no-index --find-links "$payload/wheels" --require-hashes --force-reinstall -r "$payload/wheelhouse-requirements.txt" > "$results/pip-dependencies.log" 2>&1
/opt/srrx/venv/bin/python3 -I -B - /opt/srrx/deployment/linux_lab "$payload" "$results/dependency-verification.json" <<'PY'
import json,re,subprocess,sys
from importlib.metadata import distributions
from pathlib import Path
lock,payload,out=Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3])
req=(lock/'wheelhouse-requirements.txt').read_bytes()
if (payload/'wheelhouse-requirements.txt').read_bytes()!=req:raise SystemExit('Payload wheel lock differs from the installed project lock')
norm=lambda n:re.sub(r'[-_.]+','-',n).lower()
want={norm(l.split('==',1)[0]):l.split('==',1)[1].split()[0] for l in req.decode().splitlines() if '==' in l}
have={norm(d.metadata['Name']):d.version for d in distributions()}
if have!=want:raise SystemExit('Venv distributions differ from the wheel lock: '+str(sorted(set(have.items())^set(want.items())))[:2000])
rows=subprocess.run(['dpkg-query','-W','--showformat=${Package}\t${Architecture}\t${Version}\t${db:Status-Abbrev}\n'],capture_output=True,text=True,check=True).stdout
installed={}
for row in rows.splitlines():
 name,arch,version,state=row.split('\t');installed[(name,arch)]=(version,state.strip())
debs=json.loads((lock/'guest-packages.lock.json').read_text())['packages']
bad=[x['package'] for x in debs if installed.get((x['package'],x['architecture']))!=(x['version'],'ii')]
if bad:raise SystemExit('Installed guest packages differ from the lock: '+', '.join(bad[:20]))
out.write_text(json.dumps({'status':'PASS','wheels':len(want),'debs':len(debs),'cached_dependency_state_trusted':False,
 'method':'venv recreated; every locked deb and wheel reinstalled from the hash-verified payload; installed versions equal both locks'},indent=2)+'\n')
print('Locked dependency reinstall and versions PASS')
PY
/opt/srrx/venv/bin/python3 -m pip install --no-index --no-cache-dir --force-reinstall --no-deps --no-build-isolation '/opt/srrx/software[radio,hmi,model]' > "$results/pip-install.log" 2>&1
/opt/srrx/venv/bin/python3 -m pip check
/opt/srrx/venv/bin/python3 -m pip freeze --all > "$results/python-packages.txt"
dpkg-query -W > "$results/debian-packages.txt"
cp "$payload/project-manifest.json" "$payload/payload-manifest.json" "$results/"
cd /opt/srrx
set +e
rm -f verification/software-tests.json
echo 'Running full software regression'
/opt/srrx/venv/bin/python3 tools/run_tests_offline.py > "$results/unit-tests.log" 2>&1
unit_code=$?
test ! -f verification/software-tests.json || cp verification/software-tests.json "$results/software-tests.json"
echo "Software regression exit: $unit_code; running systemd/Unix IPC smoke"
python3 deployment/linux_lab/guest_smoke.py --project /opt/srrx --report "$results/system-smoke.json" --lab-marker /etc/srrx-linux-lab.json
system_code=$?
echo "System smoke exit: $system_code; running real PTY smoke"
python3 deployment/linux_lab/pty_smoke.py --output "$results/pty-smoke.json"
pty_code=$?
echo "PTY smoke exit: $pty_code; running offscreen Qt process-failure smoke"
mkdir -p "$results/gui"
chown labclient:labd "$results/gui"
runuser -u labclient -- env PYTHONPATH=/opt/srrx/software QT_QPA_PLATFORM=offscreen QT_OPENGL=software ORT_DISABLE_TELEMETRY=1 /opt/srrx/venv/bin/python3 deployment/linux_lab/gui_smoke.py --project /opt/srrx --socket /run/srrx-linux-lab/control.sock --output "$results/gui" --timeout-scale 3
gui_code=$?
test ! -f "$results/gui/report.json" || cp "$results/gui/report.json" "$results/gui-smoke.json"
echo "Offscreen Qt exit: $gui_code; running XCB/Xvfb production menu"
mkdir -p "$results/xcb"
chown labclient:labd "$results/xcb"
runuser -u labclient -- /usr/bin/Xvfb :99 -screen 0 1280x800x24 -nolisten tcp > "$results/xcb/xvfb.log" 2>&1 &
xvfb_pid=$!
for retry in $(seq 1 100); do
    test ! -S /tmp/.X11-unix/X99 || break
    sleep 0.1
done
runuser -u labclient -- env DISPLAY=:99 PYTHONPATH=/opt/srrx/software QT_QPA_PLATFORM=xcb QT_OPENGL=software ORT_DISABLE_TELEMETRY=1 /opt/srrx/venv/bin/python3 deployment/linux_lab/xcb_smoke.py --socket /run/srrx-linux-lab/control.sock --output "$results/xcb" --timeout 90
xcb_code=$?
test ! -f "$results/xcb/report.json" || cp "$results/xcb/report.json" "$results/xcb-smoke.json"
kill "$xvfb_pid" 2>/dev/null
wait "$xvfb_pid" 2>/dev/null
echo "XCB exit: $xcb_code; running native RX worker failure smoke"
PYTHONPATH=software /opt/srrx/venv/bin/python3 deployment/linux_lab/rx_worker_smoke.py --project /opt/srrx > "$results/rx-worker-smoke.json"
rx_code=$?
echo "RX worker exit: $rx_code; running virtual block storage smoke"
/opt/srrx/venv/bin/python3 deployment/linux_lab/storage_smoke.py --project /opt/srrx --report "$results/storage-smoke.json"
storage_code=$?
echo "Storage exit: $storage_code; running all module models"
/opt/srrx/venv/bin/python3 deployment/module_lab/run.py --project /opt/srrx --output "$results/module-lab"
module_code=$?
printf '{"unit":%d,"system":%d,"pty":%d,"gui":%d,"xcb":%d,"rx":%d,"storage":%d,"modules":%d}\n' "$unit_code" "$system_code" "$pty_code" "$gui_code" "$xcb_code" "$rx_code" "$storage_code" "$module_code" > "$results/suite-exit-codes.json"
echo 'All requested ARM64 Linux lab suites completed'
test "$unit_code$system_code$pty_code$gui_code$xcb_code$rx_code$storage_code$module_code" = 00000000
