#!/usr/bin/env python3
"""Reproducible first-order analysis of the E4 bipolar DC preflight detector.

Reads nominal resistor values from E4.json. This is an arithmetic/corner model,
not SPICE, a thermal simulation, or a claim that a prototype passed its gates.
Run: python design/E4-detector-analysis.py --json
"""
from __future__ import annotations
import argparse
import itertools
import json
import math
import re
import sys
from pathlib import Path


def ohms(component: dict) -> float:
    value = component['value']
    match = re.match(r'\s*([0-9.]+)\s*(kΩ|Ω)', value)
    if not match:
        raise ValueError(f"Cannot parse resistor {component['ref']}: {value!r}")
    return float(match.group(1)) * (1000 if match.group(2) == 'kΩ' else 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--design', type=Path, default=Path(__file__).with_name('E4.json'))
    parser.add_argument('--json', action='store_true', help='Emit machine-readable JSON to stdout')
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')  # UTF-8 report text on every host, not the locale codepage.
    design = json.loads(args.design.read_text(encoding='utf-8'))
    parts = {c['ref']: c for c in design['components']}
    r = lambda ref: ohms(parts[ref])
    tolerance = 0.001  # Initial resistor tolerance only. See explicit exclusions below.
    input_error_v = 0.011  # ±9mV full-temperature offset +2mV CMRR/PSRR allowance.
    hysteresis_allowance_v = 0.008  # Use full max hysteresis conservatively, not half.
    error_v = input_error_v + hysteresis_allowance_v
    leakage_a = 80e-9  # Net clamp leakage bound; two opposing diodes, each0..80nA.
    nominal_ref_v = 2.048
    normal_ref_v = (2.024, 2.072)  # ±15mV full-T at100µA plus1+8mV current-change bounds.
    names = ('R4420', 'R4421', 'R4422', 'R4402', 'R4403', 'R4404', 'R4405')
    nom = {name: r(name) for name in names}
    # The other two channel networks must really contain the same nominal values.
    for offset in (10, 20):
        for ref in ('R4420', 'R4421', 'R4422'):
            if r('R' + str(int(ref[1:]) + offset)) != r(ref):
                raise SystemExit(f'Channel network value differs from {ref}')

    def corners(reference_range: tuple[float, float]) -> dict:
        lower, upper = [], []
        options = [[nom[n] * (1 - tolerance), nom[n] * (1 + tolerance)] for n in names]
        for values in itertools.product(reference_range, *options,
                                        (-error_v, error_v), (-leakage_a, leakage_a)):
            vref, a, b, rb, lt, lb, ut, ub, err, leakage = values
            ra = a + b
            low = vref * lb / (lt + lb)
            high = vref * ub / (ut + ub)
            # Vs=(Vcoax/Ra+Vref/Rb-Ileak)/(1/Ra+1/Rb).
            # Solve for the actual coax voltage when Vs=threshold+input error.
            solve = lambda threshold: ra * (
                (threshold + err) * (1 / ra + 1 / rb) - vref / rb + leakage)
            lower.append(solve(low))
            upper.append(solve(high))
        return {
            'reference_range_v': list(reference_range),
            'lower_trip_range_v': [min(lower), max(lower)],
            'upper_trip_range_v': [min(upper), max(upper)],
            'corner_count': len(lower),
            'max_abs_trip_v': max(map(abs, lower + upper)),
        }

    # Reference-good comparators use their independent internal references.
    # Include a conservative100K from25°C at100ppm/K plus comparator allowance.
    pg_internal_min = 1.223 * (1 - 100e-6 * 100)
    pg_internal_max = 1.260 * (1 + 100e-6 * 100)
    frac_low_max = (r('R4407') * (1 + tolerance)) / (
        r('R4406') * (1 - tolerance) + r('R4407') * (1 + tolerance))
    frac_high_min = (r('R4409') * (1 - tolerance)) / (
        r('R4408') * (1 + tolerance) + r('R4409') * (1 - tolerance))
    pg_range = ((pg_internal_min - error_v) / frac_low_max,
                (pg_internal_max + error_v) / frac_high_min)
    expanded_ref = (min(1.650, pg_range[0]), max(2.263, pg_range[1]))
    normal = corners(normal_ref_v)
    expanded = corners(expanded_ref)
    ra, rb = r('R4420') + r('R4421'), r('R4422')
    low = nominal_ref_v * r('R4403') / (r('R4402') + r('R4403'))
    high = nominal_ref_v * r('R4405') / (r('R4404') + r('R4405'))
    solve_nom = lambda threshold: ra * (threshold * (1 / ra + 1 / rb) - nominal_ref_v / rb)
    bleed = sum(r('R' + str(i)) for i in range(4460, 4464))
    terminated = 1 / (1 / 50 + 1 / bleed)
    injected_port = lambda resistance: nominal_ref_v * resistance / (ra + rb + resistance)
    vdd_max = 3.3 * 1.05
    feed_max_a = (vdd_max - normal_ref_v[0]) / (r('R4400') * .99)
    gate_pd_max_a = 8 * vdd_max / (100_000 * .99)
    rail_bleed_max_a = vdd_max / (r('R4401') * .99)
    dcs_pullup_max_a = 3 * vdd_max / (10_000 * .99)
    quiescent_max_a = 8 * 3.6e-6
    total_max_a = feed_max_a + gate_pd_max_a + rail_bleed_max_a + dcs_pullup_max_a + quiescent_max_a
    # Minimum feed headroom at0V ports; a VF assumption is exposed, not a guarantee.
    # Full-range LM4040A20 minimum operating cathode current is80µA.
    ref_load_max_a = normal_ref_v[1] * (
        2 / ((r('R4402') + r('R4403')) * .999)
        + 1 / ((r('R4406') + r('R4407')) * .999)
        + 1 / ((r('R4408') + r('R4409')) * .999)
        + 3 / ((ra + rb) * .999)) + 1e-6  #1µA input/leakage reserve.
    shunt_min_a = 80e-6
    feed_res_max = r('R4400') * 1.01
    diode_vf_limit_v = 3.135 - normal_ref_v[1] - feed_res_max * (ref_load_max_a + shunt_min_a)
    headroom_examples = [
        {'assumed_diode_vf_v': vf,
         'available_cathode_current_a': (3.135 - vf - normal_ref_v[1]) / feed_res_max - ref_load_max_a,
         'meets_80ua_if_assumption_true': (3.135 - vf - normal_ref_v[1]) / feed_res_max - ref_load_max_a >= shunt_min_a}
        for vf in (.9, 1.0)]
    # Logical series sink: both channel decisions AND both reference-good decisions.
    truth = [{'lower_ok': a, 'upper_ok': b, 'ref_low_ok': c, 'ref_high_ok': e,
              'dcs': 'LOW_SAFE' if a and b and c and e else 'HIGH_UNSAFE'}
             for a, b, c, e in itertools.product((False, True), repeat=4)]
    report = {
        'model': 'E4 arithmetic corner sweep; not SPICE or prototype qualification',
        'design_file': str(args.design),
        'assumptions': {
            'initial_resistor_tolerance_fraction': tolerance,
            'comparator_input_error_allowance_v': input_error_v,
            'full_hysteresis_allowance_v': hysteresis_allowance_v,
            'net_clamp_leakage_allowance_a': leakage_a,
            'normal_reference_range_v': list(normal_ref_v),
            'reference_pg_derived_range_v': list(pg_range),
            'broad_reference_envelope_v': list(expanded_ref),
            'feed_diode_min_vf_for_maximum_current_bound_v': 0,
            'vdd_range_v': [3.135, 3.465],
            'foreign_dc_design_envelope_v': [-30, 30],
        },
        'excluded_from_model': [
            'PCB surface contamination/leakage, resistor TCR mismatch and thermal gradients',
            'RF parasitic capacitance/inductance, rectification and strong RF overload',
            'Full transient clamp waveforms, input-clamp current sharing and ESD/lightning',
            'Capacitor leakage, component faults and all system ground offsets',
            'Guarantee that every corner unit also accepts an open/floating antenna as safe',
        ],
        'nominal': {
            'lower_coax_trip_v': solve_nom(low), 'upper_coax_trip_v': solve_nom(high),
            'reference_pg_lower_v': 1.242 * (r('R4406') + r('R4407')) / r('R4407'),
            'reference_pg_upper_v': 1.242 * (r('R4408') + r('R4409')) / r('R4409'),
            'open_port_self_bias_v': injected_port(bleed),
            '50ohm_terminated_port_self_bias_v': injected_port(terminated),
            'port_bleed_ohm': bleed,
            'ideal_50ohm_port_bleed_insertion_loss_db': 20 * math.log10(1 + 50 / (2 * bleed)),
            'extra_bias_current_4v5_a': 4.5 / bleed,
            'extra_boni_bias_current_13v8_a': 13.8 / bleed,
            'bleed_power_at_30v_w': 30 * 30 / bleed,
            'per_bleed_resistor_power_at_30v_w': 30 * 30 / bleed / 4,
        },
        'normal_corners': normal,
        'expanded_reference_corners': expanded,
        'power': {
            'reference_feed_max_a': feed_max_a,
            'gate_pulldowns_max_a': gate_pd_max_a,
            'rail_bleed_max_a': rail_bleed_max_a,
            'three_E3_dcs_pullups_max_a': dcs_pullup_max_a,
            'eight_comparators_quiescent_max_a': quiescent_max_a,
            'total_conservative_3v3_a': total_max_a,
            'lab5_detector_current_a': 0,
            'off_3v3_leakage_voltage_bound_v': 80e-9 * r('R4401') * 1.01,
            'negative_clamp_current_bound_at_minus30v_a': (30 + normal_ref_v[1]) / (ra * .999),
            'minimum_feed_headroom': {
                'condition': 'VDD3.135V, REF2.072V, all ports0V, resistor extremes;1µA input/leak reserve',
                'reference_load_max_a': ref_load_max_a,
                'required_minimum_shunt_cathode_current_a': shunt_min_a,
                'maximum_diode_vf_for_required_headroom_v': diode_vf_limit_v,
                'conditional_examples': headroom_examples,
                'full_temperature_diode_vf_guaranteed_by_this_model': False,
                'qualification': 'Measure cold minimum-supply headroom. If REF collapses, reference-good must force DCS HIGH; that is safe-state behavior, not proof of usable preflight.',
            },
        },
        'logic_truth_table': truth,
        'conclusions': {
            'analytical_max_abs_trip_below_0v1_under_listed_assumptions': expanded['max_abs_trip_v'] < .1,
            'analytical_power_allocation_below_12ma': total_max_a < .012,
            'hardware_qualified': False,
            'required_acceptance': 'Each real channel must accept0V and open/50ohm loads, reject±0.100V in both sweep directions over admitted temperature/supply, pass startup/off-state/ref-fault tests, and meet RF loading gates.',
            'bias_rule': 'Only preflight with own bias OFF. Own bias ON normally drives DCS HIGH. Enable only after≥500ms settling and≥500ms continuous LOW.',
        },
    }
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Nominal window: {solve_nom(low)*1000:.3f} .. {solve_nom(high)*1000:.3f} mV")
        print(f"Normal corner |trip|max: {normal['max_abs_trip_v']*1000:.3f} mV")
        print(f"Expanded reference corner |trip|max: {expanded['max_abs_trip_v']*1000:.3f} mV")
        print(f"Open/50ohm self-bias: {injected_port(bleed)*1000:.3f}/{injected_port(terminated)*1000:.3f} mV")
        print(f"Conservative3.3V current: {total_max_a*1000:.3f} mA")
        print(f"Minimum-feed condition: diode VF must be≤{diode_vf_limit_v:.3f} V; cold headroom qualification OPEN")
        print('Hardware qualification: OPEN. Assumptions and exclusions: rerun with --json.')
    # Explicit exits, not assert: python -O must not hide a failed target.
    if not expanded['max_abs_trip_v'] < .1:
        raise SystemExit('Listed arithmetic assumptions no longer meet100mV rejection target')
    if not total_max_a < .012:
        raise SystemExit('Detector budget exceeds12mA allocation')


if __name__ == '__main__':
    main()
