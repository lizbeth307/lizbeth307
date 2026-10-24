#!/usr/bin/env python3
"""Actual spawned RX-worker/native-ABI failure smoke, without RF or acceptance.

Usage: PYTHONPATH=software python3 deployment/linux_lab/rx_worker_smoke.py
Run natively in the isolated Linux guest; cc builds a tiny no-USB/no-network RTL
ABI fixture. ControlGuard is explicitly replaced ONLY inside this component test.
No accepted hardware/control status is fabricated and no acceptance file is made.
IQ exists only in the worker pipe/RAM, never in report/files. Exit0 means these
component lifecycle checks passed, not that a physical receiver was qualified.
Every case runs under the unchanged production startup budget
(labrx.STARTUP_TIMEOUT_S, read here and never assigned) and the production
driver-library owner/mode check (review finding RX-10).
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
#include <time.h>
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
/* Proves dlopen ran; a refused library must never reach this. */
__attribute__((constructor)) static void loaded(void) { marker("LOADED\n"); }
uint32_t rtlsdr_get_device_count(void) { return 1; }
int rtlsdr_get_device_usb_strings(uint32_t i,char *m,char *p,char *s) {
    (void)m; (void)p;
    if(i) return -1;
    if(s) strcpy(s,"SRRX-COMPONENT-FIXTURE");
    return 0;
}
int rtlsdr_open(void **d,uint32_t i) {
    if(i) return -1;
#if FIXTURE_MODE == 6
    /* A driver open that outlasts the production startup budget. */
    marker("OPEN_BLOCKING\n");
    struct timespec rest={15,0};
    nanosleep(&rest,NULL);
#endif
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
#elif FIXTURE_MODE == 6
    return -1;
#else
#error Undefined fixture mode
#endif
}
'''
# The labrx CLI boundary handles exactly these; any other type is a traceback.
CLEAN_ERRORS=(OSError,ValueError,RuntimeError)
BRANCH_OFF=[{'op':'control','name':'EN_RTLA','value':False}]
# (case, fixture mode, kind, runs). Each run gets its own copy of the mode's
# library, so a chown/chmod negative cannot change another case's file.
CASES=(('driver_error',1,'failure',1),('hang_ignoring_sigterm',2,'failure',1),('crash_sigsegv',3,'failure',1),
       ('invalid_odd_short_read',4,'failure',1),('valid_even_short_read',5,'short_read',1),
       ('startup_within_production_budget',5,'budget',3),('startup_budget_exceeded',6,'budget',1),
       ('library_not_trusted_owner',5,'untrusted',1),('library_group_writable',5,'untrusted',1))
UNTRUSTED_OWNER=65534  # nobody; the root guest moves the fixture to it, a non-root runner owns it already


def failure_issues(name,error,calls):
    """Public-error contract for the four failure fixtures; pure for unit tests."""
    messages=[]
    if error is None or isinstance(error,AssertionError): messages.append('Expected bounded worker failure was not observed')
    elif isinstance(error,EOFError): messages.append('Raw pipe EOF escaped the production clean-error boundary')
    elif not isinstance(error,CLEAN_ERRORS): messages.append('Unclean public error type escaped run_capture: '+type(error).__name__)
    elif name=='hang_ignoring_sigterm' and not isinstance(error,TimeoutError):
        messages.append('Native hang did not surface as the production read TimeoutError: '+type(error).__name__)
    if calls!=BRANCH_OFF: messages.append('Capture cleanup did not request exactly branch OFF')
    return messages


def budget_issues(case,error,ready_after_s,budget_s,elapsed_s):
    """Production startup-budget contract (review finding RX-02); pure for unit tests.

    elapsed_s: seconds from the worker spawn to the end of the first read().
    """
    messages=[]
    if case=='startup_within_production_budget':
        if error is not None: messages.append('Production startup failed: '+type(error).__name__)
        if ready_after_s is None: messages.append('Worker never reported ready')
        elif not 0<ready_after_s<budget_s: messages.append('Worker startup exceeded the production budget')
    elif case=='startup_budget_exceeded':
        if not isinstance(error,TimeoutError) or 'did not open' not in str(error):
            messages.append('Blocked driver open did not surface as the production startup TimeoutError')
        if ready_after_s is not None: messages.append('Blocked driver open unexpectedly reported ready')
        if elapsed_s is None or not budget_s<=elapsed_s<budget_s+1:
            messages.append('Startup timeout did not fire within 1 s after the production budget')
    else:
        messages.append('Unknown startup-budget case: '+str(case))
    return messages


def library_issues(error,markers,calls):
    """Untrusted-library contract (review finding RX-10); pure for unit tests.

    markers: native fixture marker lines; a refused library must leave none.
    """
    messages=[]
    if error is None or isinstance(error,AssertionError): messages.append('Untrusted driver library was not refused')
    elif not isinstance(error,CLEAN_ERRORS): messages.append('Unclean public error type escaped run_capture: '+type(error).__name__)
    elif 'trusted UID' not in str(error): messages.append('Refusal did not come from the driver-library owner/mode check')
    if set(markers)&{'LOADED','OPEN','OPEN_BLOCKING','READ'}: messages.append('Untrusted driver library was loaded')
    if calls!=BRANCH_OFF: messages.append('Capture cleanup did not request exactly branch OFF')
    return messages


def drop_page_cache():
    """Root only: start the first budget run from a cold page cache."""
    if not hasattr(os,'geteuid') or os.geteuid()!=0: return False
    os.sync()
    try:
        Path('/proc/sys/vm/drop_caches').write_text('3\n')
        return True
    except OSError:
        return False


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--read-timeout-s',type=float,default=1.0)
    parser.add_argument('--compiler',default='cc')
    args=parser.parse_args(argv)
    if not .1 <= args.read_timeout_s <= 5:
        parser.error('read timeout0.1..5s required')
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
    budget=labrx.STARTUP_TIMEOUT_S  # the production value; this harness never assigns it
    euid=os.geteuid()
    cases=[]
    original_cwd=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='srrx-worker-native-') as temporary:
        work=Path(temporary)
        source=work/'fixture.c'; source.write_text(C_FIXTURE)
        binaries={}
        for mode in sorted({mode for _,mode,_,_ in CASES}):
            library=work/('libfixture_mode'+str(mode)+'.so')
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
            binaries[mode]=(library,hashlib.sha256(data).hexdigest(),struct.unpack_from('<H',data,18)[0])
        try:
            for name,mode,kind,run,count in [c[:3]+(run,c[3]) for c in CASES for run in range(1,c[3]+1)]:
                case_id=name if count==1 else name+'_'+str(run)
                built_library,digest,elf_machine=binaries[mode]
                library=work/('libfixture_'+case_id+'.so')
                shutil.copyfile(built_library,library); library.chmod(0o755)
                # Lifecycle cases trust the account that compiled the fixture as well
                # (the non-root module lab); the guest runs as root, so there it is {0}.
                trusted=frozenset({0,euid})
                if name=='library_not_trusted_owner':
                    trusted=None  # the production default, labrx.TRUSTED_LIBRARY_UIDS
                    if euid==0: os.chown(library,UNTRUSTED_OWNER,UNTRUSTED_OWNER)
                elif name=='library_group_writable':
                    library.chmod(0o664)
                page_cache_dropped=drop_page_cache() if name=='startup_within_production_budget' and run==1 else None
                case_dir=work/case_id; case_dir.mkdir(); os.chdir(case_dir)
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
                        if trusted is not None: kw['trusted_library_uids']=trusted
                        super().__init__(*a,**kw)
                        self.native_entry=False; self.actual_read_guard_checks=0
                        self.close_duration_s=self.read_returned_after_s=None
                        workers.append(self)
                    def read(self,guard):
                        # The production read itself, from spawn: no pre-wait for
                        # the native marker, so its startup budget is what is tested.
                        before=guard.check_count
                        try:
                            return super().read(guard,timeout_s=args.read_timeout_s)
                        finally:
                            self.read_returned_after_s=time.monotonic()-self.started_at
                            self.actual_read_guard_checks=guard.check_count-before
                            self.native_entry='READ\n' in (marker.read_text() if marker.exists() else '')
                    def close(self):
                        started=time.monotonic()
                        try:
                            return super().close()
                        finally:
                            self.close_duration_s=time.monotonic()-started

                started=time.monotonic(); error=None; sample_count=None; result=None
                with patch.dict(os.environ,{'SRRX_COMPONENT_FIXTURE_MARKER':str(marker)}):
                    try:
                        if kind=='short_read':
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
                        elif name=='startup_within_production_budget':
                            with patch.object(labrx,'ControlGuard',FixtureGuard):
                                result=labrx.run_capture(center_hz=100_000_000,sample_rate=1_024_000,
                                    fft_size=64,frames=1,record=record,
                                    transport=fixture_transport,source_factory=ObservedWorker)
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
                lines=text.splitlines()
                worker=workers[0] if workers else None
                ready_after=None if worker is None else worker.ready_after_s
                enforced=bool(worker and worker.started_at is not None and labrx.STARTUP_TIMEOUT_S==budget)
                messages=[]
                if not enforced: messages.append('Case did not run under the production startup budget')
                if worker and worker.process.is_alive(): messages.append('Worker remained alive after close')
                if worker and worker.close_duration_s is not None and worker.close_duration_s>3.0:
                    messages.append('Worker close exceeded3s bound')
                if 'UNEXPECTED_BIAS_ON' in text: messages.append('Binding attempted bias ON')
                if kind=='untrusted':
                    messages.extend(library_issues(error,lines,calls))
                elif name=='startup_budget_exceeded':
                    messages.extend(budget_issues(name,error,ready_after,budget,worker and worker.read_returned_after_s))
                    if 'LOADED' not in lines or 'OPEN_BLOCKING' not in lines:
                        messages.append('Blocking native driver open was not reached')
                    if 'OPEN' in lines or 'READ' in lines: messages.append('Blocked driver open unexpectedly completed')
                    if worker and worker.process.exitcode not in (-signal.SIGTERM,-signal.SIGKILL):
                        messages.append('Blocked worker was not terminated by close()')
                    if calls!=BRANCH_OFF: messages.append('Capture cleanup did not request exactly branch OFF')
                else:
                    if worker is None or not worker.native_entry: messages.append('Native fixture READ was not reached')
                    if 'LOADED' not in lines: messages.append('Native fixture library was not loaded')
                    if 'CORE_LIMIT=0' not in lines: messages.append('Worker core limit was not confirmed zero')
                    if 'DUMPABLE=0' not in lines: messages.append('Worker was not confirmed nondumpable before native READ')
                if kind=='short_read':
                    if error is not None: messages.append(type(error).__name__+': '+str(error))
                    if sample_count!=1: messages.append('Expected one in-memory complex sample')
                    # worker.close() must run the worker's driver-close finally (rtlsdr_close).
                    if 'CLOSE' not in lines: messages.append('Native driver close did not run after worker.close()')
                elif kind=='failure':
                    messages.extend(failure_issues(name,error,calls))
                elif name=='startup_within_production_budget':
                    messages.extend(budget_issues(name,error,ready_after,budget,worker and worker.read_returned_after_s))
                    if not result or result.get('frames')!=1: messages.append('Production capture did not complete one frame')
                    elif result.get('worker_startup_s') is None or not result['worker_startup_s']<budget:
                        messages.append('run_capture did not report the measured worker startup')
                    if calls!=BRANCH_OFF: messages.append('Capture cleanup did not request exactly branch OFF')
                if name=='hang_ignoring_sigterm' and worker:
                    if 'TERM_IGNORED' not in lines: messages.append('Native SIGTERM-ignoring hang was not exercised')
                    if worker.process.exitcode!=-signal.SIGKILL: messages.append('Hung worker did not require/receive SIGKILL fallback')
                    if worker.actual_read_guard_checks<2: messages.append('Parent observer did not remain responsive during C hang')
                if name=='crash_sigsegv' and worker and worker.process.exitcode!=-signal.SIGSEGV:
                    messages.append('Native SIGSEGV fixture exit not observed')
                artifacts=sorted(p.name for p in case_dir.iterdir() if p.is_file())
                if artifacts!=([] if kind=='untrusted' else ['lifecycle.txt']):
                    messages.append('Unexpected output/core/IQ artifact in component case directory')
                info=library.stat()
                cases.append({'case':name,'run':run,'fixture_mode':mode,
                    'status':'PASS' if not messages else 'FAIL','issues':messages,
                    'production_budget_enforced':enforced,
                    'ready_after_s':None if ready_after is None else round(ready_after,3),
                    'budget_margin_s':None if ready_after is None else round(budget-ready_after,3),
                    'first_read_returned_after_s':None if not worker or worker.read_returned_after_s is None
                        else round(worker.read_returned_after_s,3),
                    'capture_worker_startup_s':None if not result else result.get('worker_startup_s'),
                    'page_cache_dropped':page_cache_dropped,
                    'trusted_library_uids':'production_default' if trusted is None else sorted(trusted),
                    'library_owner_uid':info.st_uid,'library_mode':oct(info.st_mode&0o7777),
                    'library_loaded':'LOADED' in lines,
                    'native_read_entered':bool(worker and worker.native_entry),
                    'exception_type':None if error is None else type(error).__name__,
                    'exception':None if error is None else str(error)[:200],
                    'elapsed_s':round(elapsed,3),
                    'close_duration_s':None if not worker else round(worker.close_duration_s or 0,3),
                    'worker_exitcode':None if not worker else worker.process.exitcode,
                    'worker_alive_after_close':bool(worker and worker.process.is_alive()),
                    'actual_read_observer_checks':0 if not worker else worker.actual_read_guard_checks,
                    'production_capture_cleanup_exercised':kind!='short_read',
                    'clean_error_boundary':error is None or isinstance(error,CLEAN_ERRORS),
                    'branch_off_request_observed':calls==BRANCH_OFF,
                    'branch_off_electrically_tested':False,'fixture_short_sample_count':sample_count,
                    'core_rlimit_confirmed_zero':'CORE_LIMIT=0' in lines,
                    'worker_dumpable_confirmed_zero':'DUMPABLE=0' in lines,
                    'only_case_artifact':artifacts,'elf_machine':elf_machine})
        finally:
            os.chdir(original_cwd)
        report={'status':'PASS' if cases and all(c['status']=='PASS' and c['production_budget_enforced'] for c in cases)
                    else 'FAIL',
                'scope':'spawned-worker-native-ABI-component-only-no-RF-no-accepted-hardware',
                'architecture':platform.machine(),'kernel':platform.release(),'python':platform.python_version(),
                'fixture_source_sha256':hashlib.sha256(C_FIXTURE.encode()).hexdigest(),
                'production_startup_budget_s':budget,'production_read_deadline_s':args.read_timeout_s,
                'production_trusted_library_uids':sorted(labrx.TRUSTED_LIBRARY_UIDS),'effective_uid':euid,
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
