#!/usr/bin/env python3
"""Actual spawned RX-worker/native-ABI failure smoke, without RF or acceptance.

Usage: PYTHONPATH=software python3 deployment/linux_lab/rx_worker_smoke.py
Run natively in the isolated Linux guest; cc builds a tiny no-USB/no-network RTL
ABI fixture. ControlGuard is explicitly replaced ONLY inside this component test.
No accepted hardware/control status is fabricated and no acceptance file is made.
IQ exists only in the worker pipe/RAM, never in report/files. Exit0 means these
component lifecycle checks passed, not that a physical receiver was qualified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

C_FIXTURE = r'''
#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/resource.h>
#include <sys/prctl.h>
static uint32_t frequency=0, rate=0;
static int token=307;
static void marker(const char *line) {
    const char *path=getenv("SRRX_COMPONENT_FIXTURE_MARKER");
    if (!path) return;
    int fd=open(path,O_WRONLY|O_CREAT|O_APPEND,0600);
    if (fd>=0) { size_t n=strlen(line); ssize_t written=write(fd,line,n); (void)written; close(fd); }
}
uint32_t rtlsdr_get_device_count(void) { return 1; }
int rtlsdr_get_device_usb_strings(uint32_t i,char *m,char *p,char *s) {
    (void)m; (void)p;
    if(i) return -1;
    if(s) strcpy(s,"SRRX-COMPONENT-FIXTURE");
    return 0;
}
int rtlsdr_open(void **d,uint32_t i) {
    if(i) return -1;
    *d=&token; marker("OPEN\n");
    struct rlimit lim; char text[96];
    if(!getrlimit(RLIMIT_CORE,&lim)) {
        snprintf(text,sizeof text,"CORE_LIMIT=%llu\n",(unsigned long long)lim.rlim_cur);
        marker(text);
    }
    snprintf(text,sizeof text,"DUMPABLE=%d\n",prctl(PR_GET_DUMPABLE,0L,0L,0L,0L));
    marker(text);
    return 0;
}
int rtlsdr_close(void *d) { (void)d; marker("CLOSE\n"); return 0; }
int rtlsdr_get_usb_strings(void *d,char *m,char *p,char *s) {
    (void)d; return rtlsdr_get_device_usb_strings(0,m,p,s);
}
int rtlsdr_set_bias_tee(void *d,int on) {
    (void)d;
    if(on) { marker("UNEXPECTED_BIAS_ON\n"); return -1; }
    marker("BIAS_OFF\n"); return 0;
}
int rtlsdr_set_direct_sampling(void *d,int on) { (void)d; return on ? -1:0; }
int rtlsdr_set_center_freq(void *d,uint32_t f) { (void)d; frequency=f; return 0; }
uint32_t rtlsdr_get_center_freq(void *d) { (void)d; return frequency; }
int rtlsdr_set_sample_rate(void *d,uint32_t r) { (void)d; rate=r; return 0; }
uint32_t rtlsdr_get_sample_rate(void *d) { (void)d; return rate; }
int rtlsdr_set_tuner_gain_mode(void *d,int on) { (void)d; return on ? -1:0; }
int rtlsdr_set_agc_mode(void *d,int on) { (void)d; return on ? -1:0; }
int rtlsdr_reset_buffer(void *d) { (void)d; return 0; }
int rtlsdr_read_sync(void *d,void *buffer,int length,int *count) {
    (void)d; (void)buffer; (void)length; (void)count;
    marker("READ\n");
#if FIXTURE_MODE == 1
    return -71;
#elif FIXTURE_MODE == 2
    signal(SIGTERM,SIG_IGN); marker("TERM_IGNORED\n");
    for(;;) pause();
#elif FIXTURE_MODE == 3
    raise(SIGSEGV); return -1;
#elif FIXTURE_MODE == 4
    if(length<3) return -1;
    memset(buffer,127,3); *count=3; return 0;
#elif FIXTURE_MODE == 5
    if(length<2) return -1;
    ((uint8_t*)buffer)[0]=127; ((uint8_t*)buffer)[1]=128;
    *count=2; return 0;
#else
#error Undefined fixture mode
#endif
}
'''


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--startup-timeout-s',type=float,default=60.0)
    parser.add_argument('--read-timeout-s',type=float,default=1.0)
    parser.add_argument('--compiler',default='cc')
    args=parser.parse_args(argv)
    if not (1 <= args.startup_timeout_s <= 60 and .1 <= args.read_timeout_s <= 5):
        parser.error('startup timeout1..60s, read timeout0.1..5s required')
    project=args.project.resolve(strict=True)
    sys.path.insert(0,str(project/'software'))
    sys.dont_write_bytecode=True
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    # Limit import/BLAS thread fan-out in both native and TCG guest runs.
    for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
        os.environ[key]='1'
    try:
        core_pattern=Path('/proc/sys/kernel/core_pattern').read_text()[:1024].strip()
        core_pattern_error=None
    except OSError as exc:
        # Some restricted host runners hide this sysctl. The native worker's
        # PR_GET_DUMPABLE evidence remains mandatory in every case below.
        core_pattern=None
        core_pattern_error=type(exc).__name__+': '+str(exc)[:300]
    compiler=shutil.which(args.compiler)
    if compiler is None:
        print(json.dumps({'status':'UNAVAILABLE','reason':'native C compiler missing',
                          'scope':'component-only-no-RF','physical_receiver_tested':False}))
        return 2
    try:
        import numpy as np
        import srrx.labrx as labrx
    except ImportError as exc:
        print(json.dumps({'status':'UNAVAILABLE','reason':str(exc),
                          'scope':'component-only-no-RF','physical_receiver_tested':False}))
        return 2
    cases=[]
    original_cwd=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='srrx-worker-native-') as temporary:
        work=Path(temporary)
        source=work/'fixture.c'; source.write_text(C_FIXTURE)
        binaries={}
        for name,mode in (('driver_error',1),('hang_ignoring_sigterm',2),('crash_sigsegv',3),
                          ('invalid_odd_short_read',4),('valid_even_short_read',5)):
            library=work/('libfixture_'+name+'.so')
            built=subprocess.run([compiler,'-std=c99','-shared','-fPIC','-O2','-Wall','-Wextra',
                                  '-Werror',f'-DFIXTURE_MODE={mode}',str(source),'-o',str(library)],
                                 capture_output=True,text=True,timeout=60)
            if built.returncode:
                print(json.dumps({'status':'FAIL','scope':'component-only-no-RF',
                                  'reason':'native fixture compilation failed','detail':built.stderr[:2000]}))
                return 1
            data=library.read_bytes()
            if data[:4]!=b'\x7fELF' or data[5]!=1:
                raise RuntimeError('Expected native little-endian Linux ELF fixture')
            binaries[name]=(library,hashlib.sha256(data).hexdigest(),struct.unpack_from('<H',data,18)[0])
        try:
            for name,(library,digest,elf_machine) in binaries.items():
                case_dir=work/name; case_dir.mkdir(); os.chdir(case_dir)
                marker=case_dir/'lifecycle.txt'
                calls=[]; workers=[]; guards=[]
                # Internal helper record only. This is deliberately NOT passed to
                # load_acceptance/load_driver_record or serialized as acceptance.
                record={'backend':'rtl','branch':'RTLA','serial':'SRRX-COMPONENT-FIXTURE',
                        'library_path':str(library),'library_sha256':digest}

                class FixtureGuard:
                    def __init__(self,transport,branch):
                        if branch!='RTLA': raise AssertionError('Unexpected component branch')
                        self.check_count=0; guards.append(self)
                    def check(self):
                        self.check_count+=1
                        return {'scope':'component-fixture-no-live-hardware-status'}

                def fixture_transport(request):
                    # No fake ACTIVE/qualified/accepted reply. Only record the
                    # requested de-energizing cleanup; there is no physical pin.
                    calls.append(dict(request))
                    return {'ok':True,'scope':'component-fixture-command-observed-only'}

                class ObservedWorker(labrx.WorkerSource):
                    def __init__(self,*a,**kw):
                        super().__init__(*a,**kw)
                        self.native_entry=False; self.actual_read_guard_checks=0
                        self.close_duration_s=None
                        workers.append(self)
                    def read(self,guard):
                        # A TCG guest's Python/NumPy startup is measured separately
                        # from the unchanged production read deadline. The native
                        # marker proves we reached C, rather than timing out import.
                        deadline=time.monotonic()+args.startup_timeout_s
                        while time.monotonic()<deadline:
                            guard.check()
                            text=marker.read_text() if marker.exists() else ''
                            if 'READ\n' in text:
                                self.native_entry=True
                                break
                            if not self.process.is_alive():
                                raise OSError('Fixture worker exited before native READ entry')
                            time.sleep(.02)
                        if not self.native_entry:
                            raise TimeoutError('Fixture native startup deadline exceeded')
                        before=guard.check_count
                        try:
                            return super().read(guard,timeout_s=args.read_timeout_s)
                        finally:
                            self.actual_read_guard_checks=guard.check_count-before
                    def close(self):
                        started=time.monotonic()
                        try:
                            return super().close()
                        finally:
                            self.close_duration_s=time.monotonic()-started

                started=time.monotonic(); error=None; sample_count=None
                with patch.dict(os.environ,{'SRRX_COMPONENT_FIXTURE_MARKER':str(marker)}):
                    try:
                        if name=='valid_even_short_read':
                            guard=FixtureGuard(fixture_transport,'RTLA')
                            worker=ObservedWorker(record,100_000_000,1_024_000)
                            try:
                                samples=worker.read(guard)
                                sample_count=int(samples.size)
                                if samples.shape!=(1,) or not bool(np.isfinite(samples).all()):
                                    raise AssertionError('Even2-byte short read did not become one finite complex64 sample')
                                del samples  # No samples enter JSON/report/file.
                            finally:
                                worker.close()
                        else:
                            with patch.object(labrx,'ControlGuard',FixtureGuard):
                                labrx.run_capture(center_hz=100_000_000,sample_rate=1_024_000,
                                    fft_size=1024,frames=1,output=case_dir/'unexpected-spectrum.json',
                                    survey=case_dir/'unexpected-survey.jsonl',record=record,
                                    transport=fixture_transport,source_factory=ObservedWorker)
                            raise AssertionError('Failure fixture unexpectedly produced a spectrum')
                    except Exception as exc:
                        error=exc
                    finally:
                        for worker in workers:
                            if worker.process.is_alive():
                                worker.close()
                elapsed=time.monotonic()-started
                text=marker.read_text() if marker.exists() else ''
                worker=workers[0] if workers else None
                messages=[]
                if worker is None or not worker.native_entry: messages.append('Native fixture READ was not reached')
                if worker and worker.process.is_alive(): messages.append('Worker remained alive after close')
                if worker and worker.close_duration_s is not None and worker.close_duration_s>3.0:
                    messages.append('Worker close exceeded3s bound')
                if 'CORE_LIMIT=0\n' not in text: messages.append('Worker core limit was not confirmed zero')
                if 'DUMPABLE=0\n' not in text: messages.append('Worker was not confirmed nondumpable before native READ')
                if 'UNEXPECTED_BIAS_ON' in text: messages.append('Binding attempted bias ON')
                if name=='valid_even_short_read':
                    if error is not None: messages.append(type(error).__name__+': '+str(error))
                    if sample_count!=1: messages.append('Expected one in-memory complex sample')
                else:
                    if error is None or isinstance(error,AssertionError): messages.append('Expected bounded worker failure was not observed')
                    if isinstance(error,EOFError): messages.append('Raw pipe EOF escaped the production clean-error boundary')
                    if calls!=[{'op':'control','name':'EN_RTLA','value':False}]: messages.append('Capture cleanup did not request exactly branch OFF')
                if name=='hang_ignoring_sigterm' and worker:
                    if 'TERM_IGNORED\n' not in text: messages.append('Native SIGTERM-ignoring hang was not exercised')
                    if worker.process.exitcode!=-signal.SIGKILL: messages.append('Hung worker did not require/receive SIGKILL fallback')
                    if worker.actual_read_guard_checks<2: messages.append('Parent observer did not remain responsive during C hang')
                if name=='crash_sigsegv' and worker and worker.process.exitcode!=-signal.SIGSEGV:
                    messages.append('Native SIGSEGV fixture exit not observed')
                artifacts=sorted(p.name for p in case_dir.iterdir() if p.is_file())
                if artifacts!=['lifecycle.txt']: messages.append('Unexpected output/core/IQ artifact in component case directory')
                cases.append({'case':name,'status':'PASS' if not messages else 'FAIL','issues':messages,
                    'native_read_entered':bool(worker and worker.native_entry),
                    'exception_type':None if error is None else type(error).__name__,
                    'exception':None if error is None else str(error)[:200],
                    'elapsed_s':round(elapsed,3),
                    'close_duration_s':None if not worker else round(worker.close_duration_s or 0,3),
                    'worker_exitcode':None if not worker else worker.process.exitcode,
                    'worker_alive_after_close':bool(worker and worker.process.is_alive()),
                    'actual_read_observer_checks':0 if not worker else worker.actual_read_guard_checks,
                    'production_capture_cleanup_exercised':name!='valid_even_short_read',
                    'clean_error_boundary':error is None or isinstance(error,(OSError,ValueError,RuntimeError)),
                    'branch_off_request_observed':calls==[{'op':'control','name':'EN_RTLA','value':False}],
                    'branch_off_electrically_tested':False,'fixture_short_sample_count':sample_count,
                    'core_rlimit_confirmed_zero':'CORE_LIMIT=0\n' in text,
                    'worker_dumpable_confirmed_zero':'DUMPABLE=0\n' in text,
                    'only_case_artifact':artifacts,'elf_machine':elf_machine})
        finally:
            os.chdir(original_cwd)
        report={'status':'PASS' if all(c['status']=='PASS' for c in cases) else 'FAIL',
                'scope':'spawned-worker-native-ABI-component-only-no-RF-no-accepted-hardware',
                'architecture':platform.machine(),'kernel':platform.release(),'python':platform.python_version(),
                'fixture_source_sha256':hashlib.sha256(C_FIXTURE.encode()).hexdigest(),
                'startup_deadline_s':args.startup_timeout_s,'production_read_deadline_s':args.read_timeout_s,
                'native_compile_performed':True,'control_guard_replaced_only_in_test':True,
                'kernel_core_pattern':core_pattern,'kernel_core_pattern_read_error':core_pattern_error,
                'core_protection_references':['https://man7.org/linux/man-pages/man5/core.5.html',
                    'https://man7.org/linux/man-pages/man2/pr_set_dumpable.2const.html'],
                'acceptance_file_created':False,'physical_receiver_tested':False,
                'physical_control_outputs_tested':False,'rf_transmitted':False,'raw_iq_persisted':False,
                'cases':cases}
        print(json.dumps(report,indent=2,allow_nan=False))
        return 0 if report['status']=='PASS' else 1


if __name__=='__main__':
    raise SystemExit(main())
