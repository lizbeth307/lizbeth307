#!/usr/bin/env python3
"""Production RF policy and exact Lime guard snippets, all explicitly emulated.

SimHardware is never promoted to physical/accepted hardware. HMC, relay, DC and
bias checks exercise control logic, not analog switching or a detector voltage.
Unsupported USB/analog modules remain inventory-only records in the JSON.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def _require(condition, message):
    if not condition:
        raise AssertionError(message)


def _case(name, action):
    try:
        return {'name': name, 'status': 'EMULATION_PASS', **(action() or {})}
    except Exception as exc:
        return {'name': name, 'status': 'FAIL', 'error': type(exc).__name__ + ': ' + str(exc)[:500]}


def _record(identifier, refs, cases, *, limits=(), level='control_logic'):
    return {'id': identifier, 'design_refs': refs, 'model_level': level,
            'status': 'EMULATION_PASS' if all(c['status'] == 'EMULATION_PASS' for c in cases) else 'FAIL',
            'physical_verified': False, 'scenarios': cases, 'limits': list(limits)}


def _policy(project):
    from srrx.hardware import SimHardware, load_mapping
    from srrx.policy import CAPS, SafetyPolicy
    hardware = SimHardware(load_mapping(project/'design/E3.json'))
    policy = SafetyPolicy(hardware, clock=lambda: 0)
    inputs = hardware.read_inputs()
    inputs.update(DCS_UHF=False, DCS_LBAND=False, DCS_HF=False,
                  PG_LNB=True, PG_BONI=True, PTC_AUX=True, OVP_LNB_N=True)
    policy.refresh_inputs(inputs, 0)
    limits = {}
    for branch, (cap, vcap) in CAPS.items():
        baseline = min(.1, cap*.5)
        limits[branch] = {'baseline_a': baseline, 'max_current_a': min(cap*.8, baseline*1.2),
                          'min_voltage_v': min(3, vcap-.2), 'max_voltage_v': vcap}
    policy.configure_limits(limits)
    policy.refresh_telemetry({b: {'current_a': 0, 'voltage_v': 0, 'timestamp_ms': 0} for b in CAPS}, 0)
    policy.set_readiness(pico_active=True, commissioned=True)
    _require(policy.command('lease', {'owner': 'module-lab-SIMULATION', 'ttl_ms': 5000}, 0)['ok'], 'SIM lease rejected')
    _require(policy.command('arm', True, 0)['ok'], 'SIM arm rejected')
    _require(hardware.physical is False and policy.status()['simulation'] is True, 'Simulation identity lost')
    return policy, hardware, inputs


def _dwell(policy, inputs):
    from srrx.policy import CAPS
    for now in (200, 400, 500, 700, 900, 1000):
        policy.refresh_inputs(inputs, now)
    policy.refresh_telemetry({b: {'current_a': 0, 'voltage_v': 0, 'timestamp_ms': 1000} for b in CAPS}, 1000)


def _hmc(project, receiver, ref):
    cases = []
    def routing():
        from srrx.policy import ROUTES
        policy, hardware, _ = _policy(project)
        policy.command('disarm', True, 0)
        _require(policy.command('mode', 'lab', 0)['ok'], 'SIM bench mode rejected')
        policy.command('confirmations', {'bench_loads': True}, 0)
        _require(policy.command('arm', True, 0)['ok'], 'SIM rearm rejected')
        tested = []
        for route in ('RF4', 'RF3', 'RF2', 'PARK'):
            before = len(hardware.trace)
            _require(policy.command('route_'+receiver, route, 0)['ok'], 'Route rejected: '+route)
            writes = [e['outputs'] for e in hardware.trace[before:] if e.get('event') == 'outputs']
            an, bn = 'SW_'+receiver+'_A', 'SW_'+receiver+'_B'
            _require((hardware.outputs[an], hardware.outputs[bn]) == ROUTES[route], 'HMC truth table mismatch')
            if route != 'PARK':
                _require(len(writes) >= 2 and writes[0][an] is False and writes[0][bn] is False,
                         'Route transition lacked explicit 00 PARK write')
            tested.append({'route': route, 'A': hardware.outputs[an], 'B': hardware.outputs[bn]})
        return {'truth_table': tested, 'explicit_park_before_active': True, 'analog_rf_simulated': False}
    cases.append(_case('actual_policy_truth_table_and_park_before_switch', routing))
    def denied():
        policy, hardware, _ = _policy(project)
        old = dict(hardware.outputs)
        for name, value in (('TX_ENABLE', True), ('SW_'+receiver+'_A', True),
                            ('route_'+receiver, 'TX'), ('route_'+receiver, {'RF2': True})):
            _require(not policy.command(name, value, 0)['ok'], 'Raw/TX route bypass accepted')
        _require(hardware.outputs == old, 'Rejected route altered outputs')
        policy.trip('fixture supervisor loss')
        _require(policy.command('route_'+receiver, 'PARK', 0)['ok'], 'Emergency PARK unavailable')
        _require(not policy.command('route_'+receiver, 'RF2', 0)['ok'], 'Fault latch allowed active route')
        return {'raw_gpio_and_tx_rejected': True, 'fault_latch_no_auto_route': True}
    cases.append(_case('raw_gpio_tx_and_fault_latch', denied))
    return _record('HMC7992_'+receiver, ['E4/'+ref], cases,
                   limits=['Actual SafetyPolicy and graph-derived SimHardware mapping only.',
                           '00 PARK is RF1 termination by design; RF impedance, isolation and switching transients require hardware.'])


def _relays(project):
    def action():
        policy, hardware, _ = _policy(project)
        _require(not policy.command('relay', 'HF', 0)['ok'], 'Relay enabled without initial dwell')
        _require(policy.command('relay', 'HF', 10)['ok'], 'HF relay rejected after dwell')
        _require(hardware.outputs['K1_ON'] and not hardware.outputs['K2_ON'], 'HF relay image wrong')
        _require(not policy.command('relay', 'VHF', 11)['ok'], 'HF to VHF skipped break-before-make')
        _require(not hardware.outputs['K1_ON'] and not hardware.outputs['K2_ON'], 'Break was not PARK')
        _require(not policy.command('relay', 'VHF', 20)['ok'], 'Relay dwell shorter than10ms accepted')
        _require(policy.command('relay', 'VHF', 21)['ok'], 'VHF rejected after10ms')
        _require(not policy.command('relay', '11', 21)['ok'], 'Forbidden relay11 accepted')
        _require(not any(e.get('outputs', {}).get('K1_ON') and e.get('outputs', {}).get('K2_ON')
                         for e in hardware.trace), 'Relay11 appeared in output trace')
        policy.trip('fixture heartbeat failure')
        _require(not hardware.outputs['K1_ON'] and not hardware.outputs['K2_ON'], 'Trip did not PARK relays')
        return {'break_before_make_ms': 10, 'relay_11_observed': False, 'trip_park_observed': True}
    return _record('RF_RELAYS', ['E4/K401', 'E4/K402'], [_case('hf_vhf_park_never_11', action)],
                   limits=['Relay coil commands only, no coil current/contact bounce or RF path emulation.'])


def _dc_and_bias(project):
    from srrx.policy import DCS
    graph = json.loads((project/'design/E4.json').read_text())
    result = []
    for branch, dcs in DCS.items():
        def action(branch=branch, dcs=dcs):
            policy, hardware, inputs = _policy(project)
            if branch == 'BONI':
                policy.command('confirmations', {'boni_connected': True, 'boni_profile': True}, 0)
                _require(policy.command('relay', 'HF', 10)['ok'], 'Boni HF prerequisite failed')
            _require(not policy.command('EN_'+branch, True, 10)['ok'], 'DC preflight omitted')
            inputs[dcs] = True
            for now in (200, 400, 600, 800, 1000):
                policy.refresh_inputs(inputs, now)
            _require(not policy.command('EN_'+branch, True, 1000)['ok'], 'Unsafe/unknown DC input enabled bias')
            inputs[dcs] = False
            for now in (1001, 1200, 1400, 1501):
                policy.refresh_inputs(inputs, now)
            from srrx.policy import CAPS
            policy.refresh_telemetry({b: {'current_a': 0, 'voltage_v': 0, 'timestamp_ms': 1501} for b in CAPS}, 1501)
            _require(policy.command('EN_'+branch, True, 1501)['ok'], 'Settled LOW rejected')
            inputs[dcs] = True  # Own bias makes DC present, not a foreign-DC trip.
            policy.refresh_inputs(inputs, 1502)
            _require(policy.fault is None, 'Own DC incorrectly tripped running bias')
            _require(policy.command('EN_'+branch, False, 1502)['ok'], 'OFF rejected')
            _require(not policy.command('EN_'+branch, True, 1502)['ok'], 'Immediate re-enable skipped OFF settling')
            _require(not hardware.outputs['EN_'+branch], 'Rejected re-enable left bias ON')
            return {'unsafe_high_blocks_enable': True, 'off_settling_ms': 500,
                    'continuous_safe_low_ms': 500, 'own_bias_high_is_not_foreign_dc': True,
                    'analog_voltage_threshold_tested': False}
        refs = ['E4/'+c['ref'] for c in graph['components']
                if any(p.get('net') == dcs for p in c['pins'])]
        # External assemblies on the actual biased paths, not the optional
        # channel4 LNA. These refs receive digital-control coverage only.
        refs.append({'LNA2': 'E4/A418', 'LNA3': 'E4/A419', 'BONI': 'E4/A406'}[branch])
        limits = ['HIGH models unsafe, unknown, detector-off or open line; LOW is a digital fixture input.',
                  'Comparator threshold, hysteresis, RF loading and power-off leakage are not physically emulated.']
        if branch == 'LNA3':
            limits.append('A419 denotes the selected GOES / H1 / iO / active-patch profile boundary; no interchangeable profile or LNA is physically qualified by this check.')
        result.append(_record('DC_PREFLIGHT_'+branch, refs,
                              [_case('unsafe_off_low_dwell_own_bias_off', action)],
                              limits=limits))
    def rest():
        policy, hardware, _ = _policy(project)
        checked = []
        for branch in ('LNA1', 'LNA4', 'SB_LNA', 'RTLA', 'RTLB', 'HFP'):
            _require(policy.command('EN_'+branch, True, 0)['ok'], 'Enable rejected: '+branch)
            _require(policy.command('EN_'+branch, False, 0)['ok'], 'OFF rejected: '+branch)
            checked.append(branch)
        _require(not policy.command('EN_LNB', True, 0)['ok'], 'LNB enabled outside RF3')
        _require(policy.command('route_RTLB', 'RF3', 0)['ok'], 'LNB RF3 selection failed')
        _require(policy.command('EN_LNB', True, 0)['ok'], 'LNB enable failed on RF3')
        _require(not policy.command('route_RTLB', 'RF2', 0)['ok'], 'Active LNB route change accepted')
        policy.command('route_RTLB', 'PARK', 0)
        _require(not hardware.outputs['EN_LNB'], 'Emergency PARK did not disable LNB')
        return {'sequential_enable_off_branches': checked, 'lnb_requires_rf3': True,
                'lnb_park_disables_bias': True, 'physical_current_measured': False}
    result.append(_record('RF_BRANCH_ENABLES', ['E4/A402', 'E4/A404', 'E4/A424', 'E4/A422',
                                              'E4/A411', 'E4/A412', 'E4/A414', 'E4/A420'],
                          [_case('actual_policy_bias_receiver_and_lnb_interlocks', rest)],
                          limits=['Monitored values/limits are explicitly synthetic policy inputs; no ADC or analog module gain measured.']))
    return result


def _body(text, signature):
    start = text.index('{', text.index(signature)) + 1
    depth, index = 1, start
    while depth:
        if text[index] == '{': depth += 1
        if text[index] == '}': depth -= 1
        index += 1
    return text[start:index-1]


def _lime(project):
    def action():
        compiler = shutil.which('g++')
        _require(compiler is not None, 'g++ required for actual extracted guard compilation')
        vendor = _load('srrx_module_vendor_patch', project/'deployment/vendor_patch.py')
        with tempfile.TemporaryDirectory(prefix='srrx-lime-guard-') as temporary:
            root = Path(temporary)
            receipt = vendor.apply_to_copy('limesuiteng', project/'deployment/upstream-fixtures/limesuiteng',
                                           root/'patched', fixture=True)
            streaming = (root/'patched/plugins/soapysdr/Streaming.cpp').read_text()
            micro = (root/'patched/src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp').read_text()
            setup = _body(streaming, 'SoapySDR::Stream* Soapy_limesuiteng::setupStream(').split('std::unique_lock', 1)[0]
            native = _body(micro, 'std::unique_ptr<lime::RFStream> LimeSDR_Micro::StreamCreate(').split('if (!la9310', 1)[0]
            configure = _body(micro, 'OpStatus LimeSDR_Micro::Configure(').split('OpStatus status;', 1)[0]
            calibrate = _body(micro, 'OpStatus LimeSDR_Micro::Calibrate(').split('mLMSChips', 1)[0]
            write = _body(streaming, 'int Soapy_limesuiteng::writeStream(')
            waveform = _body(micro, 'OpStatus LimeSDR_Micro::UploadTxWaveform(')
            _require('StreamTx' not in write and 'samples' not in waveform, 'TX work remains in disabled entrypoint')
            code = ('#include <map>\n#include <vector>\n#include <stdexcept>\n#include <cassert>\n'
                    'constexpr int SOAPY_SDR_RX=1,SOAPY_SDR_TX=0,SOAPY_SDR_NOT_SUPPORTED=-5;\n'
                    'enum class TRXDir{Rx,Tx};enum class OpStatus{Success,NotSupported};\n'
                    'struct Config{std::map<TRXDir,std::vector<int>> channels;};\n'
                    'struct Channel{struct{bool enabled=false;}tx;};struct SDRConfig{Channel channel[2];};\n'
                    'bool setup(int direction){'+setup+'return true;}\n'
                    'void* stream(const Config& config){'+native+'return (void*)1;}\n'
                    'OpStatus configure(const SDRConfig& cfg){'+configure+'return OpStatus::Success;}\n'
                    'OpStatus calibrate(TRXDir trx){'+calibrate+'return OpStatus::Success;}\n'
                    'int write(){'+write+'}\nOpStatus waveform(){'+waveform+'}\n'
                    'int main(){for(int d:{0,2,-1}){bool rejected=false;try{setup(d);}catch(const std::runtime_error&){rejected=true;}assert(rejected);}'
                    'assert(setup(SOAPY_SDR_RX));Config c;c.channels[TRXDir::Rx]={0};assert(stream(c));'
                    'c.channels[TRXDir::Tx]={0};assert(!stream(c));SDRConfig s;assert(configure(s)==OpStatus::Success);'
                    's.channel[0].tx.enabled=true;assert(configure(s)==OpStatus::NotSupported);'
                    's.channel[0].tx.enabled=false;s.channel[1].tx.enabled=true;assert(configure(s)==OpStatus::NotSupported);'
                    'assert(calibrate(TRXDir::Tx)==OpStatus::NotSupported);assert(calibrate(TRXDir::Rx)==OpStatus::Success);'
                    'assert(write()==SOAPY_SDR_NOT_SUPPORTED);assert(waveform()==OpStatus::NotSupported);}')
            source, binary = root/'guards.cpp', root/'guards'
            source.write_text(code)
            compiled = subprocess.run([compiler, '-std=c++20', '-Wall', '-Werror', str(source), '-o', str(binary)],
                                      capture_output=True, text=True, timeout=60)
            _require(compiled.returncode == 0, 'Guard compile failed: '+compiled.stderr[:1000])
            executed = subprocess.run([str(binary)], capture_output=True, timeout=10)
            _require(executed.returncode == 0, 'Actual patched guards failed native assertions')
            return {'exact_patch_sha256': receipt['patch_sha256'], 'upstream_commit': receipt['upstream_commit'],
                    'compiled_actual_guard_snippets': True, 'full_sdk_compiled': False,
                    'tx_entrypoints_rejected': ['Soapy setupStream', 'Soapy writeStream', 'Micro Configure TX0/TX1',
                                                'Micro StreamCreate TX', 'Micro Calibrate TX', 'Micro UploadTxWaveform'],
                    'rx_guard_paths_allowed': True, 'runtime_receiver_backend_enabled': False}
    return _record('LIME', ['E4/A415'], [_case('exact_patched_guard_snippets_native_compile', action)],
                   limits=['Exact patched source snippets compiled with minimal types; not a complete LimeSuiteNG build or ABI.',
                           'Raw register/firmware paths, PCIe enumeration and RF cannot be qualified here; production Lime RX backend remains blocked.'])


def _inventory(project):
    deploy = _load('srrx_module_deploy', project/'deployment/deploy.py')
    def rules():
        config = json.loads((project/'deployment/devices.template.json').read_text())
        config['i2c'] = {'ina228': {'path': '/dev/i2c-1', 'of_fullname': '/soc/i2c@1'},
                         'control': {'path': '/dev/i2c-2', 'of_fullname': '/soc/i2c@2'}}
        config['pico']['kernel_parent'] = 'c880000.serial'
        config['usb']['hfplus']['serial'] = 'AIRSPYHF SN:3070123456789abc'
        config['wifi_bt']['fe11s_port4_usb_path'] = '1-1.4'
        generated = deploy.udev_rules(config)
        _require('LABRXA' in generated and 'LABRXB' in generated and '3070123456789abc' in generated,
                 'Serial-bound receiver rules missing')
        for field in ('duplicate', 'wrong_vid', 'lime_enabled'):
            invalid = copy.deepcopy(config)
            if field == 'duplicate': invalid['usb']['rtl_b']['serial'] = 'LABRXA'
            elif field == 'wrong_vid': invalid['usb']['rtl_a']['vid'] = '0001'
            else: invalid['lime']['enabled'] = True
            try:
                deploy.validate_devices(invalid)
            except ValueError:
                continue
            raise AssertionError('Invalid device inventory accepted: '+field)
        return {'production_selector': 'deployment.deploy.validate_devices/udev_rules',
                'synthetic_inventory_only': True, 'rules_installed': False, 'kernel_usb_enumeration_tested': False}
    result = [_record('RECEIVER_USB_IDENTITY_RULES', ['E4/A411', 'E4/A412', 'E4/A414'],
                      [_case('serial_bound_inventory_rejects_duplicate_wrong_vid_and_lime', rules)],
                      limits=['Candidate udev rule generation, not device discovery against sysfs.'])]
    for identifier, refs, label, reason in (
            ('USB_HUB_CH334F', ['E5/U510'], 'Adafruit5997 CH334F revC', 'No project USB-hub/kernel enumeration driver implemented.'),
            ('DISPLAY_TOUCH', ['E5/U520'], 'Wisecoco display/controller/touch assembly', 'Qt events and display metadata are not a USB HID/display hardware driver emulation.'),
            ('SSD_T7', ['E5/U540'], 'Samsung T7', 'No USB mass-storage/UAS/SCSI or SSD failure emulation implemented.'),
            ('HANTEK', [], 'Optional Hantek bench scope', 'No Hantek acquisition driver or fixed schematic module is implemented.')):
        result.append({'id': identifier, 'design_refs': refs, 'name': label, 'model_level': 'unsupported',
                       'status': 'UNSUPPORTED', 'physical_verified': False, 'scenarios': [],
                       'inventory_only': True, 'reason': reason})
    graph = json.loads((project/'design/E4.json').read_text())
    for part in graph['components']:
        if part['kind'] != 'module' or part['ref'] in ('A411', 'A412', 'A414', 'A415'):
            continue
        result.append({'id': 'RF_ASSEMBLY_'+part['ref'], 'design_refs': ['E4/'+part['ref']],
                       'name': part['value'], 'model_level': 'unsupported', 'status': 'UNSUPPORTED',
                       'physical_verified': False, 'scenarios': [], 'inventory_only': True,
                       'reason': 'Passive/active analog RF assembly: graph inventory only. Bias control coverage does not model gain, noise, matching or RF transfer.'})
    return result


def run(project):
    project = Path(project).resolve(strict=True)
    sys.path.insert(0, str(project/'software'))
    sys.dont_write_bytecode = True
    modules = [_hmc(project, receiver, ref) for receiver, ref in (('RTLA', 'U405'), ('RTLB', 'U406'), ('LIME', 'U407'))]
    modules.append(_relays(project))
    modules.extend(_dc_and_bias(project))
    modules.append(_lime(project))
    modules.extend(_inventory(project))
    return {'schema_version': 1,
            'status': 'FAIL' if any(m['status'] == 'FAIL' for m in modules) else 'EMULATION_PASS',
            'scope': 'production-control-policy-and-exact-TX-guard-source-emulation', 'modules': modules,
            'physical_verified': False, 'analog_rf_simulated': False, 'raw_iq_persisted': False,
            'acceptance_created': False, 'production_mode_used': 'SIMULATION',
            'production_sources_sha256': {p: hashlib.sha256((project/p).read_bytes()).hexdigest()
                 for p in ('software/srrx/policy.py', 'software/srrx/hardware.py', 'deployment/deploy.py',
                           'deployment/vendor_patch.py', 'deployment/patches/limesuiteng-rx-only.patch')},
            'limits': ['Synthetic readiness/limits/telemetry exist only inside SimHardware; no live HARDWARE status returned.',
                       'UNSUPPORTED records are inventory coverage, not successful device-driver or analog emulation.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        report = run(args.project)
    except (OSError, ValueError, ImportError, subprocess.SubprocessError) as exc:
        report = {'schema_version': 1, 'status': 'FAIL', 'reason': type(exc).__name__+': '+str(exc),
                  'physical_verified': False}
    rendered = json.dumps(report, indent=2, allow_nan=False)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(rendered)
    print(rendered, end='')
    return 0 if report['status'] == 'EMULATION_PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
