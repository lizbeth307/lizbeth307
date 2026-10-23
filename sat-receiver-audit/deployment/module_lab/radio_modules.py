#!/usr/bin/env python3
"""Exercise production receive-only ctypes bindings against native ABI fixtures.

No USB device, radio, acceptance record or live control state is synthesized.
The C libraries have no USB/network/TX implementation. Their short synthetic IQ
blocks stay in RAM. EMULATION_PASS describes these software checks only.
"""
from __future__ import annotations

import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile


RTL_SOURCE = r'''
#include <stdint.h>
#include <string.h>
static int mode, target, opened, closed, bias_on, bias_off, reads, last_index;
static int token;
static uint32_t frequency, rate;
static const char *identity(int id) { return id ? "LABRXB" : "LABRXA"; }
void fixture_reset(int m,int t) {
 mode=m;target=t;opened=closed=bias_on=bias_off=reads=0;last_index=-1;
 frequency=rate=0;
}
int fixture_opened(void){return opened;}
int fixture_closed(void){return closed;}
int fixture_bias_on(void){return bias_on;}
int fixture_bias_off(void){return bias_off;}
int fixture_reads(void){return reads;}
int fixture_index(void){return last_index;}
static int device_id(uint32_t index) {
 if(mode==1) return 1-(int)index;
 if(mode==2) return 1-target;
 if(mode==3) return index==1 ? 1-target : target;
 return (int)index;
}
uint32_t rtlsdr_get_device_count(void){return mode==2?1:mode==3?3:2;}
int rtlsdr_get_device_usb_strings(uint32_t index,char *m,char *p,char *s){
 (void)m;(void)p;
 if(mode==6 || index>=rtlsdr_get_device_count()) return -19;
 if(s) strcpy(s,identity(device_id(index)));
 return 0;
}
int rtlsdr_open(void **d,uint32_t index){
 opened++;last_index=(int)index;
 if(mode==5) return -5;
 token=device_id(index);*d=&token;return 0;
}
int rtlsdr_close(void *d){(void)d;closed++;return 0;}
int rtlsdr_get_usb_strings(void *d,char *m,char *p,char *s){
 (void)d;(void)m;(void)p;
 if(s) strcpy(s,mode==4?"REPLACED-DEVICE":identity(token));
 return 0;
}
int rtlsdr_set_bias_tee(void *d,int on){
 (void)d;if(on){bias_on++;return -1;}bias_off++;return 0;
}
int rtlsdr_set_direct_sampling(void *d,int on){(void)d;return on?-1:0;}
int rtlsdr_set_center_freq(void *d,uint32_t f){(void)d;frequency=f;return 0;}
uint32_t rtlsdr_get_center_freq(void *d){(void)d;return frequency;}
int rtlsdr_set_sample_rate(void *d,uint32_t r){(void)d;rate=r;return 0;}
uint32_t rtlsdr_get_sample_rate(void *d){(void)d;return mode==10?rate+1:rate;}
int rtlsdr_set_tuner_gain_mode(void *d,int on){(void)d;return on?-1:0;}
int rtlsdr_set_agc_mode(void *d,int on){(void)d;return on?-1:0;}
int rtlsdr_reset_buffer(void *d){(void)d;return 0;}
int rtlsdr_read_sync(void *d,void *buffer,int length,int *count){
 (void)d;reads++;
 if(mode==7)return -71;
 if(mode==11)return -19;
 if(mode==9){*count=0;return 0;}
 int n=mode==8?3:mode==12?2:32;
 if(length<n)return -1;
 for(int i=0;i<n;i++)((uint8_t*)buffer)[i]=(i%2)?191:64;
 *count=n;return 0;
}
'''


HF_SOURCE = r'''
#include <stdint.h>
typedef struct {void *device;void *ctx;float *samples;int sample_count;
                uint64_t dropped_samples;} transfer;
static int mode,closed,stopped,started,bias_on,bias_off;
static uint64_t requested;
static int token;
static int (*callback)(transfer*);
static void *context;
void fixture_reset(int m){mode=m;closed=stopped=started=bias_on=bias_off=0;requested=0;callback=0;}
int fixture_closed(void){return closed;}
int fixture_stopped(void){return stopped;}
int fixture_started(void){return started;}
int fixture_bias_on(void){return bias_on;}
int fixture_bias_off(void){return bias_off;}
uint64_t fixture_requested(void){return requested;}
int airspyhf_open_sn(void **d,uint64_t serial){
 requested=serial;
 if(mode==1 || serial!=UINT64_C(0x3070123456789abc))return -1;
 if(mode==2)return -17; /* Vendor open_sn rejects ambiguous emulated identity. */
 *d=&token;return 0;
}
int airspyhf_close(void *d){(void)d;closed++;return 0;}
int airspyhf_stop(void *d){(void)d;stopped++;callback=0;return 0;}
int airspyhf_set_bias_tee(void *d,int8_t on){
 (void)d;if(on){bias_on++;return -1;}bias_off++;return 0;
}
int airspyhf_set_freq(void *d,uint32_t f){(void)d;(void)f;return 0;}
int airspyhf_get_samplerates(void *d,uint32_t *out,uint32_t n){
 (void)d;if(mode==10)return -19;
 if(n==0)*out=2;else{out[0]=mode==9?192000:768000;out[1]=48000;}return 0;
}
int airspyhf_set_samplerate(void *d,uint32_t rate){(void)d;return rate==768000?0:-1;}
static int send_block(int kind){
 float samples[32];for(int i=0;i<16;i++){samples[2*i]=.5f;samples[2*i+1]=-.25f;}
 transfer t={&token,context,kind==5?0:samples,kind==6?0:16,kind==4?1:0};
 return callback(&t);
}
int airspyhf_start(void *d,int (*cb)(transfer*),void *ctx){
 (void)d;started++;callback=cb;context=ctx;
 if(mode==3)return -7;
 if(mode==8)return 0;
 /* 64 transfers fill the bounded queue; the 65th is dropped (callback still 0). */
 if(mode==7){for(int i=0;i<65;i++)if(send_block(0))return -9;return 0;}
 /* Callback failure is asynchronous in a real driver, not a start() return. */
 send_block(mode);return 0;
}
int fixture_inject_drop(void){return callback?send_block(4):-1;}
int fixture_send_block(void){return callback?send_block(0):-1;}
'''


def _bootstrap(project):
    project = Path(project).resolve(strict=True)
    sys.path.insert(0, str(project / 'software'))
    sys.dont_write_bytecode = True
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    return project


def _case(name, action):
    try:
        detail = action() or {}
        return {'name': name, 'status': 'EMULATION_PASS', **detail}
    except Exception as exc:
        return {'name': name, 'status': 'FAIL', 'error': type(exc).__name__ + ': ' + str(exc)[:400]}


def _require(condition, message):
    if not condition:
        raise AssertionError(message)


def _compile(compiler, directory, name, source):
    cfile, library = directory / (name + '.c'), directory / (name + '.so')
    cfile.write_text(source, encoding='utf-8')
    result = subprocess.run([compiler, '-std=c99', '-shared', '-fPIC', '-O2', '-Wall',
                             '-Wextra', '-Werror', str(cfile), '-o', str(library)],
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError('Native fixture compilation failed: ' + result.stderr[:2000])
    lib = C.CDLL(str(library))
    return library, lib


def _rtl_cases(library, lib, branch, serial, target):
    import numpy as np
    from srrx.receivers import RTLReceiver
    record = {'library_path': str(library), 'serial': serial}
    cases = []
    definitions = [
        ('serial_selected_stream', 0, None), ('serial_selection_survives_index_reorder', 1, None),
        ('unplugged_selected_serial_no_index_fallback', 2, 'missing or ambiguous'),
        ('duplicate_serial_no_index_fallback', 3, 'missing or ambiguous'),
        ('serial_changed_after_open', 4, 'serial changed'), ('native_open_error', 5, 'open RTL failed'),
        ('enumeration_disconnect', 6, 'enumerate RTL failed'), ('native_stream_error', 7, 'RTL read failed'),
        ('odd_short_read_rejected', 8, 'Invalid/empty'), ('empty_read_rejected', 9, 'Invalid/empty'),
        ('rate_readback_mismatch', 10, 'readback mismatch'), ('stream_unplug', 11, 'RTL read failed'),
        ('even_short_read_accepted_in_ram', 12, None)]
    for name, mode, expected in definitions:
        def action(mode=mode, expected=expected):
            lib.fixture_reset(mode, target)
            receiver, error, count = None, None, None
            try:
                receiver = RTLReceiver(record, 100_000_000, 1_024_000)
                samples = receiver.read()
                count = int(samples.size)
                _require(samples.dtype == np.dtype('complex64') and bool(np.isfinite(samples).all()),
                         'Production binding did not return finite complex64')
                _require(count == (1 if mode == 12 else 16), 'Unexpected short block size')
                del samples
            except (OSError, ValueError) as exc:
                error = exc
            finally:
                if receiver:
                    receiver.close(); receiver.close()
            if expected:
                _require(error is not None and expected in str(error), 'Expected fail-closed error: ' + expected)
            else:
                _require(error is None, 'Normal native stream failed: ' + str(error))
            _require(lib.fixture_bias_on() == 0, 'Binding requested bias ON')
            if mode in (2, 3, 6):
                _require(lib.fixture_opened() == 0, 'Missing/ambiguous enumeration still opened an index')
            if mode != 5 and lib.fixture_opened():
                _require(lib.fixture_closed() == 1, 'Device was not closed exactly once')
                _require(lib.fixture_bias_off() >= 2, 'RTL bias OFF missing at open/close')
            if mode in (0, 1):
                _require(lib.fixture_index() == (1-target if mode == 1 else target), 'Wrong physical index for serial')
            return {'requested_serial': serial, 'opened_index': lib.fixture_index(),
                    'open_calls': lib.fixture_opened(), 'close_calls': lib.fixture_closed(),
                    'bias_on_calls': lib.fixture_bias_on(), 'sample_count_ram_only': count,
                    'expected_error_observed': error is not None}
        cases.append(_case(name, action))
    return {'id': branch, 'design_refs': ['E4/A411' if branch == 'RTLA' else 'E4/A412'],
            'model_level': 'native_driver_abi', 'production_entrypoint': 'srrx.receivers.RTLReceiver',
            'status': 'EMULATION_PASS' if all(c['status'] == 'EMULATION_PASS' for c in cases) else 'FAIL',
            'physical_verified': False, 'scenarios': cases,
            'limits': ['Emulated librtlsdr ABI, no real USB enumeration/tuner/RF.',
                       'Internal fixture record bypasses hardware acceptance by design; this is not a physical capture.']}


def _hf_cases(library, lib):
    import numpy as np
    from srrx.receivers import AirspyHFReceiver
    serial = '3070123456789abc'
    record = {'library_path': str(library), 'serial': serial}
    lib.fixture_requested.restype = C.c_uint64
    cases = []
    definitions = [('serial_selected_callback_copy', 0, None), ('selected_serial_unplugged', 1, 'open serial'),
                   ('vendor_rejects_duplicate_identity', 2, 'open serial'), ('native_start_error', 3, 'start failed'),
                   ('dropped_samples_rejected', 4, 'dropped samples'), ('null_callback_samples_rejected', 5, 'null samples'),
                   ('empty_callback_block_rejected', 6, 'invalid block'), ('consumer_lag_drops_new_transfer_marks_gap', 7, None),
                   ('silent_stream_timeout', 8, 'sample timeout'), ('unsupported_live_rate_rejected', 9, 'absent'),
                   ('rate_query_disconnect', 10, 'rate count failed'), ('drop_after_initial_block', 11, 'dropped samples')]
    for name, mode, expected in definitions:
        def action(mode=mode, expected=expected):
            lib.fixture_reset(mode)
            receiver, error, count = None, None, None
            try:
                receiver = AirspyHFReceiver(record, 10_000_000, 768_000)
                if mode == 11:
                    lib.fixture_inject_drop()
                if mode == 7:
                    # Consumer lag is not fatal: the full queue keeps its 64 contiguous
                    # blocks, the 65th transfer is dropped and the next queued block is marked.
                    for _ in range(64):
                        receiver.read()
                        _require(receiver.discontinuity is False, 'Queued HF backlog was marked as a gap')
                    _require(lib.fixture_send_block() == 0, 'Consumer lag stopped the HF stream')
                samples = receiver.read()
                if mode == 7:
                    _require(receiver.discontinuity is True, 'Consumer-lag drop was not marked on the next queued block')
                count = int(samples.size)
                _require(samples.dtype == np.dtype('complex64') and count == 16,
                         'HF callback complex64 ABI/length mismatch')
                _require(bool(np.all(samples == np.complex64(.5-.25j))), 'Transient C callback data not copied correctly')
                del samples
            except (OSError, ValueError, TimeoutError) as exc:
                error = exc
            finally:
                if receiver:
                    receiver.close(); receiver.close()
            _require(lib.fixture_requested() == int(serial, 16), 'Exact uint64 serial was not forwarded')
            _require(lib.fixture_bias_on() == 0, 'Binding requested HF+ bias ON')
            if expected:
                _require(error is not None and expected in str(error), 'Expected rejection: ' + expected + ', got ' + str(error))
            else:
                _require(error is None, 'HF stream failed: ' + str(error))
            _require(lib.fixture_closed() == (0 if mode in (1, 2) else 1), 'HF close not exactly once')
            if mode in (0, 4, 5, 6, 7, 8, 11):
                _require(lib.fixture_stopped() == 1, 'Started HF stream not stopped exactly once')
            return {'requested_serial_hex': format(lib.fixture_requested(), '016x'),
                    'close_calls': lib.fixture_closed(), 'stop_calls': lib.fixture_stopped(),
                    'bias_on_calls': lib.fixture_bias_on(), 'sample_count_ram_only': count,
                    'expected_error_observed': error is not None}
        cases.append(_case(name, action))
    return {'id': 'HFPLUS', 'design_refs': ['E4/A414'], 'model_level': 'native_driver_abi',
            'production_entrypoint': 'srrx.receivers.AirspyHFReceiver',
            'status': 'EMULATION_PASS' if all(c['status'] == 'EMULATION_PASS' for c in cases) else 'FAIL',
            'physical_verified': False, 'scenarios': cases,
            'limits': ['Official open_sn callback ABI is emulated; no real USB or RF.',
                       'Duplicate serial rejection belongs to the vendor open_sn API; production has no independent HF enumeration API.',
                       'Callbacks use transient C stack buffers; native USB thread scheduling is not reproduced.']}


def run(project, compiler='cc', *, include_worker=True, include_control=True):
    project = _bootstrap(project)
    compiler_path = shutil.which(compiler)
    if not compiler_path:
        return {'schema_version': 1, 'status': 'UNAVAILABLE', 'reason': 'Native C compiler missing', 'modules': []}
    import numpy  # Explicit runtime requirement; no fake fallback FFT/receiver.
    modules = []
    with tempfile.TemporaryDirectory(prefix='srrx-radio-modules-') as temporary:
        directory = Path(temporary)
        rtl_path, rtl = _compile(compiler_path, directory, 'rtl_fixture', RTL_SOURCE)
        hf_path, hf = _compile(compiler_path, directory, 'hf_fixture', HF_SOURCE)
        modules.append(_rtl_cases(rtl_path, rtl, 'RTLA', 'LABRXA', 0))
        modules.append(_rtl_cases(rtl_path, rtl, 'RTLB', 'LABRXB', 1))
        modules.append(_hf_cases(hf_path, hf))
    worker = None
    if include_worker:
        child = subprocess.run([sys.executable, str(project/'deployment/linux_lab/rx_worker_smoke.py'),
                                '--project', str(project), '--compiler', compiler],
                               capture_output=True, text=True, timeout=420,
                               env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1'))
        try:
            worker = json.loads(child.stdout)
        except (json.JSONDecodeError, ValueError):
            worker = {'status': 'FAIL', 'reason': 'Worker smoke did not return JSON', 'stderr': child.stderr[:1000]}
        if child.returncode or worker.get('status') != 'PASS':
            worker['status'] = 'FAIL'
    control = None
    if include_control:
        import importlib.util
        spec = importlib.util.spec_from_file_location('srrx_radio_scenarios', Path(__file__).with_name('radio_scenarios.py'))
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        control = module.run(project)
        modules.extend(control['modules'])
    failed = any(m['status'] == 'FAIL' for m in modules) or (worker and worker.get('status') != 'PASS')
    return {'schema_version': 1, 'status': 'FAIL' if failed else 'EMULATION_PASS',
            'scope': 'native-driver-ABI-and-control-emulation-no-real-USB-or-analog-RF',
            'architecture': platform.machine(), 'python': platform.python_version(),
            'numpy': numpy.__version__, 'modules': modules, 'worker_failure_lifecycle': worker,
            'control_report': None if control is None else {k: v for k, v in control.items() if k != 'modules'},
            'fixture_source_sha256': {'rtl': hashlib.sha256(RTL_SOURCE.encode()).hexdigest(),
                                      'airspyhf': hashlib.sha256(HF_SOURCE.encode()).hexdigest()},
            'production_sources_sha256': {name: hashlib.sha256((project/name).read_bytes()).hexdigest()
                 for name in ('software/srrx/receivers.py', 'software/srrx/labrx.py')},
            'physical_verified': False, 'raw_iq_persisted': False, 'rf_transmitted': False,
            'acceptance_created': False, 'live_hardware_status_fabricated': False,
            'limits': ['An EMULATION_PASS is not hardware qualification or proof of analog gain/isolation/matching.',
                       'Unsupported inventory-only modules are explicitly reported rather than counted as driver emulation.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--compiler', default='cc')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--no-worker', action='store_true', help='Skip separately supervised crash/hang cases')
    parser.add_argument('--no-control', action='store_true', help='Only exercise native receiver ABIs')
    args = parser.parse_args(argv)
    try:
        report = run(args.project, args.compiler, include_worker=not args.no_worker, include_control=not args.no_control)
    except (OSError, ValueError, ImportError, subprocess.SubprocessError) as exc:
        report = {'schema_version': 1, 'status': 'FAIL', 'reason': type(exc).__name__ + ': ' + str(exc),
                  'physical_verified': False, 'raw_iq_persisted': False}
    rendered = json.dumps(report, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding='utf-8', newline='\n')
    print(rendered, end='')
    return 0 if report['status'] == 'EMULATION_PASS' else 2 if report['status'] == 'UNAVAILABLE' else 1


if __name__ == '__main__':
    raise SystemExit(main())
