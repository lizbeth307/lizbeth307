"""Native C ABI fixture; not a physical SDR or vendor-driver qualification."""
import ctypes as C
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import numpy as np
from srrx.receivers import AirspyHFReceiver

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
int airspyhf_start(void *d,int (*cb)(transfer*),void *ctx){
 float values[2048];for(int i=0;i<1024;i++){values[2*i]=0.5f;values[2*i+1]=-0.25f;}
 transfer t={d,ctx,values,1024,0};return cb(&t);
}
int fixture_stopped(void){return stopped;}
int fixture_closed(void){return closed;}
int fixture_bias_on(void){return bias_on;}
'''


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
