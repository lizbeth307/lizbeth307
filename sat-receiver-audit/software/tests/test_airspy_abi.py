"""Native C ABI fixture; not a physical SDR or vendor-driver qualification."""
import ctypes as C
import queue
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import numpy as np
from srrx.receivers import AirspyHFReceiver, _HFTransfer

SOURCE = r'''
#include <stdint.h>
typedef struct { void *device; void *ctx; float *samples; int sample_count;
                 uint64_t dropped_samples; } transfer;
static int stopped, closed, bias_on;
int airspyhf_open_sn(void **device,uint64_t serial) {
 if(serial!=0x307) return -1; *device=(void*)0x307; return 0;
}
int airspyhf_close(void *d){closed++;return 0;}
int airspyhf_stop(void *d){stopped++;return 0;}
int airspyhf_set_freq(void *d,uint32_t rate){return 0;}
int airspyhf_set_samplerate(void *d,uint32_t rate){return rate==768000?0:-1;}
int airspyhf_get_samplerates(void *d,uint32_t *out,uint32_t len){
 if(len==0) *out=2; else {out[0]=768000;out[1]=192000;} return 0;
}
int airspyhf_set_bias_tee(void *d,int8_t value){if(value)bias_on++;return 0;}
static int (*callback)(transfer*);static void *context;
int airspyhf_start(void *d,int (*cb)(transfer*),void *ctx){
 callback=cb;context=ctx;
 float values[2048];for(int i=0;i<1024;i++){values[2*i]=0.5f;values[2*i+1]=-0.25f;}
 transfer t={d,ctx,values,1024,0};return cb(&t);
}
int fixture_burst(int first,int n){
 int failed=0;for(int i=first;i<first+n;i++){float v[4]={(float)i,0,(float)i,0};
 transfer t={0,context,v,2,0};failed|=callback(&t);} return failed;
}
int fixture_stopped(void){return stopped;}
int fixture_closed(void){return closed;}
int fixture_bias_on(void){return bias_on;}
'''


class AirspyCallbackQueueTests(unittest.TestCase):
    """Python callback body only; the real ctypes trampoline is covered natively below."""
    def receiver(self):
        rx = object.__new__(AirspyHFReceiver)
        rx.blocks, rx.error, rx.discontinuity, rx._gap = queue.Queue(maxsize=3), None, False, False
        return rx

    def transfer(self, value, dropped=0):
        values = (C.c_float * 4)(value, 0, value, 0)
        t = _HFTransfer(None, None, C.cast(values, C.POINTER(C.c_float)), 2, dropped)
        return C.pointer(t), values

    def test_consumer_lag_drops_new_transfers_and_marks_the_next_queued_block(self):
        rx = self.receiver()
        for value in range(5):
            pointer, keep = self.transfer(float(value))
            self.assertEqual(rx._receive(pointer), 0)  # lag never stops the stream
        self.assertIsNone(rx.error)
        for value in range(3):  # the queued backlog stays in order and contiguous
            self.assertEqual(rx.read()[0], value)
            self.assertFalse(rx.discontinuity)
        for value in (5, 6):
            pointer, keep = self.transfer(float(value))
            self.assertEqual(rx._receive(pointer), 0)
        self.assertEqual(rx.read()[0], 5)
        self.assertTrue(rx.discontinuity)  # transfers 3 and 4 were dropped, never spliced
        self.assertEqual(rx.read()[0], 6)
        self.assertFalse(rx.discontinuity)

    def test_threaded_consumer_lag_never_marks_a_block_after_a_drop_contiguous(self):
        import sys
        import threading
        import time
        rx, received, done, latest = self.receiver(), [], threading.Event(), [0]
        def produce():
            try:
                for seq in range(1, 10001):
                    pointer, keep = self.transfer(float(seq))
                    if rx._receive(pointer):
                        break
                    latest[0] = seq
            finally:
                done.set()
        interval = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)  # preempt the callback thread as often as possible
        try:
            producer = threading.Thread(target=produce)
            producer.start()
            while not (done.is_set() and rx.blocks.empty()):
                try:
                    block = rx.read()
                except TimeoutError:
                    continue
                received.append((rx.discontinuity, int(block[0].real)))
                if len(received) % 32 == 0:
                    # A lagging consumer, like a slow fsync: wait until the producer has run more
                    # than the queue holds past this block, so a drop happens at any CPU speed
                    # (QEMU TCG included) instead of depending on scheduler timing.
                    target, deadline = received[-1][1] + rx.blocks.maxsize + 2, time.monotonic() + 10
                    while latest[0] < target and not done.is_set() and time.monotonic() < deadline:
                        time.sleep(.0005)
            producer.join()
        finally:
            sys.setswitchinterval(interval)
        self.assertIsNone(rx.error)
        previous = 0
        for gap, seq in received:
            self.assertGreater(seq, previous)
            self.assertEqual(gap, seq != previous + 1)  # contiguous exactly when nothing was dropped
            previous = seq
        self.assertTrue(any(gap for gap, _ in received))

    def test_usb_dropped_samples_remain_fatal(self):
        rx = self.receiver()
        pointer, keep = self.transfer(1.0, dropped=7)
        self.assertEqual(rx._receive(pointer), -1)
        with self.assertRaisesRegex(OSError, 'dropped samples'):
            rx.read()


@unittest.skipUnless(shutil.which('cc'), 'C compiler unavailable for native ABI fixture')
class AirspyNativeABITests(unittest.TestCase):
    def test_actual_ctypes_callback_copies_transient_complex_samples_and_closes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'fixture.c';binary=root/'fixture.so'
            source.write_text(SOURCE)
            subprocess.run(['cc','-shared','-fPIC','-O0',str(source),'-o',str(binary)],check=True,capture_output=True,timeout=15)
            rx=AirspyHFReceiver({'library_path':str(binary),'serial':'0000000000000307'},10000000,768000)
            # The C callback's stack buffer has already gone out of scope.
            values=rx.read()
            self.assertEqual(values.dtype,np.dtype('complex64'))
            self.assertEqual(values.shape,(1024,))
            self.assertTrue(np.all(values==np.complex64(.5-.25j)))
            rx.close();rx.close()
            lib=C.CDLL(str(binary))
            self.assertEqual(lib.fixture_stopped(),1)
            self.assertEqual(lib.fixture_closed(),1)
            self.assertEqual(lib.fixture_bias_on(),0)

    def test_actual_ctypes_callback_survives_consumer_lag_and_marks_the_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'fixture.c';binary=root/'fixture.so'
            source.write_text(SOURCE)
            subprocess.run(['cc','-shared','-fPIC','-O0',str(source),'-o',str(binary)],check=True,capture_output=True,timeout=15)
            rx=AirspyHFReceiver({'library_path':str(binary),'serial':'0000000000000307'},10000000,768000)
            try:
                rx.read()
                self.assertEqual(rx.lib.fixture_burst(0,70),0)  # 64 queued, 6 dropped; the stream keeps running
                for value in range(64):
                    self.assertEqual(rx.read()[0],value);self.assertFalse(rx.discontinuity)
                self.assertEqual(rx.lib.fixture_burst(70,1),0)
                self.assertEqual(rx.read()[0],70);self.assertTrue(rx.discontinuity)
                self.assertIsNone(rx.error)
            finally:
                rx.close()
