# SR-RX-v2.1 — інженерний комплект схем і перевірок

> **Оновлення 20.10.2026, ПЗ0.3.1:** реалізовано керування/Pico/IMU, RX/FFT, GNSS, спектральне навчання й touch-меню. Додано [ARM64 Linux lab](deployment/linux_lab/README.md), [емуляцію підключення модулів](deployment/module_lab/README.md) і StorageGuard для запису на явно прив'язаний змонтований диск. [Код і запуск](software/README.md), [встановлення](software/DEPLOYMENT.md). Окремий [внутрішній прототип DC_CORE](build/kicad/pcb-prototype/README.md) має реальне розведення й нуль raw DRC findings; апаратне/виробниче приймання не виконано. Цей стан замінює старі описи в цьому файлі; джерело істини — STACK.md.

Редакція від 20.10.2026 продовжує роботу з коміту Claude `4653188`. У тому Git E1–E5 були порожніми; поточні заповнені схеми, netlist, PDF/SVG та звіти створюються інструментами в `tools/` із перевірених графів у `design/`.

Джерело істини — [STACK.md](STACK.md); поправки v2.1 зафіксовано на його початку. Почати з [поправок v2.1](build/12-revision-v2.1.md), [COMPLETION](COMPLETION.md), [OPEN_ITEMS](OPEN_ITEMS.md), [HANDOFF](HANDOFF.md), [KiCad README](build/kicad/README.md) та [монтажних карт](design/E5-connection-guide.md). Після зміни графів виконати `python3 tools/run_checks.py --export`, актуалізувати сім source snapshots та pin/ref inventory моделей і пройти повний цикл [Linux FINDINGS](deployment/linux_lab/FINDINGS.md): host regression, новий ARM64 Linux/module run, finalizer, документи/firmware та bundle. Застарілі результати й source binding не можна переносити на змінений код. Фінальна перевірка 23.10.2026 (`tools/run_checks.py --export`): 750 елементів, 2181 підключений контакт, 466 іменованих мереж, 137 явних NC; 14 електричних сторінок і кореневий зміст (PDF — 15 сторінок A2). KiCad 10.0.7 ERC: 0 помилок, 0 попереджень; зіставлення графів із XML-netlist — PASS. У реєстрі [OPEN_ITEMS](OPEN_ITEMS.md) 37 блокувальних воріт, включно з E5-10 (W1-2: апаратне утримання WIFI_PWR_EN). Хостова регресія: 644 тести, 643 PASS, 1 SKIP; `deployment/test.sh` — 37 PASS. Емуляція модулів перегенерована на хості x86_64; ARM64 Linux lab — лише [запис попереднього прогону](verification/linux-lab/README.md), повторно не виконувався.

**Апаратний випуск BLOCKED:** жодного стендового приймання не виконано. Реалізоване ПЗ перевіряється на хості; повний C++56MS/s/Lime, усі декодери, HTP/QAIRT та встановлений образ не заявлено як завершені. Початковий PCB-шаблон порожній, starter збережений нерозведеним, новий внутрішній прототип має траси. Його DRC не визначає фізичні інтерфейси/MPN/механіку. `readiness-contract.json` — специфікація, не прошивка.

**ISDT 608PD/raw-balance, у тому числі щомісячне балансування, заборонені до E1-02; J102 DNP/service-only.** Внутрішні sense-з'єднання Daly зберігаються. Не переносити B0 на P− і не обходити захист підключенням до raw B−.

[12-revision-v2.1](build/12-revision-v2.1.md) замінює старі розміри/параметри LAB5, S-band і відповідні інструкції. S-band LaNA WB + sysmocom cf2235-kt30 є зовнішнім антенним вузлом; старе розміщення всередині ручного корпуса не чинне. Старі ціни та підсумки v2 лишилися історичною оцінкою. [BOM схеми](build/11-schematic-bom.csv) не є готовим кошиком і включає частини комерційних модулів.

Редакцію опубліковано в Git: гілка `codex/sr-rx-v2-completion`, 23.10.2026 fast-forward злита в `ccr-1537979d-cj7q9t` (див. [RESTORE-GIT](RESTORE-GIT.md)).

---

## Історичний каталог аудиту v2

# Аудит компонентів портативного супутникового приймача (жовтень 2026)

Нижче збережено історичний каталог досліджень v2. Позначки готовності в ньому стосуються етапів дослідження, а не виробничого приймання v2.1.

- [Хронологія всіх зведень](summaries.md) — 259 записів
- Повні відповіді субагентів по кожному компоненту — посилання в таблиці нижче
- [Фінальні перевірки](final-checks.md)
- [Щохвилинний журнал аудиту](minute-log.md)
- [Додаткові дослідження (складні антени тощо)](extra-studies.md)

| Компонент | Етапи (✅ готово, ⏳ працює) | Поточний run |
|---|---|---|
| [2 m wide path second flamingo fm uses th](components/2_m_wide_path_second_flamingo_fm_uses_th.md) | · research · forums · fixes ✅ verify | `—` |
| [2 mm al mid plate copper clad fr4 rf bay](components/2_mm_al_mid_plate_copper_clad_fr4_rf_bay.md) | · research · forums · fixes ✅ verify | `—` |
| [65 100 w usb c pd charger 5 a c c cable](components/65_100_w_usb_c_pd_charger_5_a_c_c_cable.md) | · research · forums · fixes ✅ verify | `—` |
| [Ad8318 class log detector power meter](components/ad8318_class_log_detector_power_meter.md) | · research · forums · fixes ✅ verify | `—` |
| [Adafruit bno085 4754 rp2040 zero metal p](components/adafruit_bno085_4754_rp2040_zero_metal_p.md) | · research · forums · fixes ✅ verify | `—` |
| [Adafruit ch334f mtt hub 5997](components/adafruit_ch334f_mtt_hub_5997.md) | · research · forums · fixes ✅ verify | `—` |
| [Adafruit ina228 5832](components/adafruit_ina228_5832.md) | · research · forums · fixes ✅ verify | `—` |
| [Adafruit mcp23017 5346 0x20 outputs 0x22](components/adafruit_mcp23017_5346_0x20_outputs_0x22.md) | · research · forums · fixes ✅ verify | `—` |
| [Adi lt3045 paralleled 4 5 v lna rail](components/adi_lt3045_paralleled_4_5_v_lna_rail.md) | · research · forums · fixes ✅ verify | `—` |
| [Airspy hf discovery](components/airspy_hf_discovery.md) | · research · forums · fixes ✅ verify | `—` |
| [Airspy mini](components/airspy_mini.md) | · research · forums · fixes ✅ verify | `—` |
| [Allnet 64 gb microsd adafruit 5212 reade](components/allnet_64_gb_microsd_adafruit_5212_reade.md) | · research · forums · fixes ✅ verify | `—` |
| [Aneng an8008 9 dmm](components/aneng_an8008_9_dmm.md) | · research · forums · fixes ✅ verify | `—` |
| [Anker 737 power bank 20 v 5 a pdo 100 wh](components/anker_737_power_bank_20_v_5_a_pdo_100_wh.md) | · research · forums · fixes ✅ verify | `—` |
| [Antennas](components/antennas.md) | ✅ research ✅ forums ✅ fixes ✅ verify | `wf_6b9836f8-796` |
| [Antennas foldable](components/antennas_foldable.md) | ✅ research · forums · fixes ✅ verify | `—` |
| [Antennas patch chip](components/antennas_patch_chip.md) | ✅ research · forums · fixes ✅ verify | `—` |
| [Aon 3 3 v ldo tps709 class micropower uv](components/aon_3_3_v_ldo_tps709_class_micropower_uv.md) | · research · forums · fixes ✅ verify | `—` |
| [Asa 1 kg cnc kitchen m3 inserts and scre](components/asa_1_kg_cnc_kitchen_m3_inserts_and_scre.md) | · research · forums · fixes ✅ verify | `—` |
| [Bourns pec11r 4215f s0024 x3 c k ksc641j](components/bourns_pec11r_4215f_s0024_x3_c_k_ksc641j.md) | · research · forums · fixes ✅ verify | `—` |
| [Cable bulkhead set 7 sma 1 f bulkheads r](components/cable_bulkhead_set_7_sma_1_f_bulkheads_r.md) | · research · forums · fixes ✅ verify | `—` |
| [Compute](components/compute.md) | ✅ research ✅ forums ✅ fixes ✅ verify | `wf_88090a59-878` |
| [Compute os](components/compute_os.md) | ✅ research · forums · fixes ✅ verify | `—` |
| [Custom 2 layer pcbs power board 5 channe](components/custom_2_layer_pcbs_power_board_5_channe.md) | · research · forums · fixes ✅ verify | `—` |
| [Daly 4s 15 a common port balancing bms](components/daly_4s_15_a_common_port_balancing_bms.md) | · research · forums · fixes ✅ verify | `—` |
| [Dish replacement](components/dish_replacement.md) | ✅ research ✅ forums ✅ fixes ✅ verify | `wf_5a66d65f-c3f` |
| [Display](components/display.md) | ✅ research ✅ forums ✅ fixes ✅ verify | `wf_0e70c405-a03` |
| [Display hmi](components/display_hmi.md) | ✅ research · forums · fixes ✅ verify | `—` |
| [Flightaware pro stick plus](components/flightaware_pro_stick_plus.md) | · research · forums · fixes ✅ verify | `—` |
| [Fnirsi dps 150 bench supply](components/fnirsi_dps_150_bench_supply.md) | · research · forums · fixes ✅ verify | `—` |
| [Fnirsi fnb58 std no radio](components/fnirsi_fnb58_std_no_radio.md) | · research · forums · fixes ✅ verify | `—` |
| [Generic hmc7992 sp4t boards rtl a and rt](components/generic_hmc7992_sp4t_boards_rtl_a_and_rt.md) | · research · forums · fixes ✅ verify | `—` |
| [Gnss imu](components/gnss_imu.md) | ✅ research ✅ forums ✅ fixes ✅ verify | `wf_45d278c2-004` |
| [Gnss imu location](components/gnss_imu_location.md) | ✅ research · forums · fixes ✅ verify | `—` |
| [Hantek 6022be fx2lafw la](components/hantek_6022be_fx2lafw_la.md) | · research · forums · fixes ✅ verify | `—` |
| [Hf receiver](components/hf_receiver.md) | ✅ research · forums · fixes ✅ verify | `—` |
| [Hf selector 2x omron g6k 2f rf 5 v serie](components/hf_selector_2x_omron_g6k_2f_rf_5_v_serie.md) | · research · forums · fixes ✅ verify | `—` |
| [Ifixit portable anti static mat](components/ifixit_portable_anti_static_mat.md) | · research · forums · fixes ✅ verify | `—` |
| [Ip2368 4s 100 w pd board charge only bz](components/ip2368_4s_100_w_pd_board_charge_only_bz.md) | · research · forums · fixes ✅ verify | `—` |
| [Isdt 608pd balance charger](components/isdt_608pd_balance_charger.md) | · research · forums · fixes ✅ verify | `—` |
| [Lab instruments](components/lab_instruments.md) | ✅ research · forums · fixes ✅ verify | `—` |
| [Lab ui](components/lab_ui.md) | ✅ research · forums · fixes ✅ verify | `—` |
| [Leo bodnar lbe 1420 gpsdo](components/leo_bodnar_lbe_1420_gpsdo.md) | · research · forums · fixes ✅ verify | `—` |
| [Lime parts adt link r44sf i pex 90435 00](components/lime_parts_adt_link_r44sf_i_pex_90435_00.md) | · research · forums · fixes ✅ verify | `—` |
| [Limesdr micro m 2 basic 18 shipping 2x m](components/limesdr_micro_m_2_basic_18_shipping_2x_m.md) | · research · forums · fixes ✅ verify | `—` |
| [Litevna 64](components/litevna_64.md) | · research · forums · fixes ✅ verify | `—` |
| [Mech thermal storage](components/mech_thermal_storage.md) | ✅ research · forums · fixes ✅ verify | `—` |
| [Mechanical thermal](components/mechanical_thermal.md) | ✅ research ✅ forums ✅ fixes ✅ verify | `wf_e6b8e5e2-124` |
| [Molicel inr21700 p50b](components/molicel_inr21700_p50b.md) | · research · forums · fixes ✅ verify | `—` |
| [Narrowband sdr](components/narrowband_sdr.md) | ✅ research ✅ forums ✅ fixes ✅ verify | `wf_eb446444-464` |
| [Noise source mini circuits zfl 500ln or](components/noise_source_mini_circuits_zfl_500ln_or.md) | · research · forums · fixes ✅ verify | `—` |
| [Nooelec flamingo fm v2 100813](components/nooelec_flamingo_fm_v2_100813.md) | · research · forums · fixes ✅ verify | `—` |
| [Nooelec pad kit 2x 30 db pads 2x blk 89](components/nooelec_pad_kit_2x_30_db_pads_2x_blk_89.md) | · research · forums · fixes ✅ verify | `—` |
| [Nooelec sawbird goes cased 100792](components/nooelec_sawbird_goes_cased_100792.md) | · research · forums · fixes ✅ verify | `—` |
| [Nooelec sawbird h1](components/nooelec_sawbird_h1.md) | · research · forums · fixes ✅ verify | `—` |
| [Nooelec sawbird io cased 100788](components/nooelec_sawbird_io_cased_100788.md) | · research · forums · fixes ✅ verify | `—` |
| [Nooelec sawbird noaa cased 100800](components/nooelec_sawbird_noaa_cased_100800.md) | · research · forums · fixes ✅ verify | `—` |
| [Npu training](components/npu_training.md) | ✅ research · forums · fixes ✅ verify | `—` |
| [Pack sundries nickel fish paper kapton j](components/pack_sundries_nickel_fish_paper_kapton_j.md) | · research · forums · fixes ✅ verify | `—` |
| [Padded antenna roll element tube 15 20 l](components/padded_antenna_roll_element_tube_15_20_l.md) | · research · forums · fixes ✅ verify | `—` |
| [Pca9555 key expander piezo status led](components/pca9555_key_expander_piezo_status_led.md) | · research · forums · fixes ✅ verify | `—` |
| [Pelican 1450 apache 3800 case with divid](components/pelican_1450_apache_3800_case_with_divid.md) | · research · forums · fixes ✅ verify | `—` |
| [Pinecil v2 ironos bluetooth off](components/pinecil_v2_ironos_bluetooth_off.md) | · research · forums · fixes ✅ verify | `—` |
| [Pololu 2813 hp pushbutton power switch](components/pololu_2813_hp_pushbutton_power_switch.md) | · research · forums · fixes ✅ verify | `—` |
| [Pololu d36v28f5 2 for a 5 v only display](components/pololu_d36v28f5_2_for_a_5_v_only_display.md) | · research · forums · fixes ✅ verify | `—` |
| [Pololu d36v28f5 lab5](components/pololu_d36v28f5_lab5.md) | · research · forums · fixes ✅ verify | `—` |
| [Pololu d36v50f12 sys12](components/pololu_d36v50f12_sys12.md) | · research · forums · fixes ✅ verify | `—` |
| [Power](components/power.md) | ✅ research ✅ forums ✅ fixes ✅ verify | `wf_f924b2ab-5ad` |
| [Printed 30 mm hinged hood 7in ar film ve](components/printed_30_mm_hinged_hood_7in_ar_film_ve.md) | · research · forums · fixes ✅ verify | `—` |
| [Protection filter set 7 5 a pack 4 a j21](components/protection_filter_set_7_5_a_pack_4_a_j21.md) | · research · forums · fixes ✅ verify | `—` |
| [Qo 100 add on othernet bullseye tcxo lnb](components/qo_100_add_on_othernet_bullseye_tcxo_lnb.md) | · research · forums · fixes ✅ verify | `—` |
| [Radxa armor 7056a heatsink or stepped cu](components/radxa_armor_7056a_heatsink_or_stepped_cu.md) | · research · forums · fixes ✅ verify | `—` |
| [Radxa ufs 3 1 128 gb ra022 b10j0u2](components/radxa_ufs_3_1_128_gb_ra022_b10j0u2.md) | · research · forums · fixes ✅ verify | `—` |
| [Raspberry pi debug probe](components/raspberry_pi_debug_probe.md) | · research · forums · fixes ✅ verify | `—` |
| [Raspberry pi pico rp2040 hmi supervisor](components/raspberry_pi_pico_rp2040_hmi_supervisor.md) | · research · forums · fixes ✅ verify | `—` |
| [Rf frontend](components/rf_frontend.md) | ✅ research ✅ forums ✅ fixes ✅ verify | `wf_30889068-251` |
| [Rf sled hmc7992 sp4t pe4302 mcp23017 2 a](components/rf_sled_hmc7992_sp4t_pe4302_mcp23017_2_a.md) | · research · forums · fixes ✅ verify | `—` |
| [Rtl sdr blog v4l r828s](components/rtl_sdr_blog_v4l_r828s.md) | · research · forums · fixes ✅ verify | `—` |
| [Samsung t7 1 tb](components/samsung_t7_1_tb.md) | · research · forums · fixes ✅ verify | `—` |
| [Shielded hdmi lead adafruit 2420 2x wurt](components/shielded_hdmi_lead_adafruit_2420_2x_wurt.md) | · research · forums · fixes ✅ verify | `—` |
| [Shock corded mast 7 x 35 cm about 2 4 m](components/shock_corded_mast_7_x_35_cm_about_2_4_m.md) | · research · forums · fixes ✅ verify | `—` |
| [Sma torque wrench 0 9 n m adapter set](components/sma_torque_wrench_0_9_n_m_adapter_set.md) | · research · forums · fixes ✅ verify | `—` |
| [Software](components/software.md) | ✅ research ✅ forums ✅ fixes ✅ verify | `wf_e49d4f53-8d4` |
| [Software stack](components/software_stack.md) | ✅ research · forums · fixes ✅ verify | `—` |
| [Spare rtl sdr blog wideband lna v2](components/spare_rtl_sdr_blog_wideband_lna_v2.md) | · research · forums · fixes ✅ verify | `—` |
| [Storage](components/storage.md) | ✅ research ✅ forums ✅ fixes ✅ verify | `wf_3e735695-e00` |
| [Targets link budgets](components/targets_link_budgets.md) | ✅ research · forums · fixes ✅ verify | `—` |
| [Tca9517 buffer 74lvc1g17 2n7002 ao3400 f](components/tca9517_buffer_74lvc1g17_2n7002_ao3400_f.md) | · research · forums · fixes ✅ verify | `—` |
| [Ti tps2553 lab port 0 75 a lna ch1 4 300](components/ti_tps2553_lab_port_0_75_a_lna_ch1_4_300.md) | · research · forums · fixes ✅ verify | `—` |
| [Ti tps7a4701 ldo lnb 13 2 v boni 12 5 v](components/ti_tps7a4701_ldo_lnb_13_2_v_boni_12_5_v.md) | · research · forums · fixes ✅ verify | `—` |
| [Tinplate hf can lc mix 31 on vbus](components/tinplate_hf_can_lc_mix_31_on_vbus.md) | · research · forums · fixes ✅ verify | `—` |
| [Tinysa ultra zs407](components/tinysa_ultra_zs407.md) | · research · forums · fixes ✅ verify | `—` |
| [Tools spares notebook build tools calipe](components/tools_spares_notebook_build_tools_calipe.md) | · research · forums · fixes ✅ verify | `—` |
| [Travel tripod 35 cm folded 1 2 m or more](components/travel_tripod_35_cm_folded_1_2_m_or_more.md) | · research · forums · fixes ✅ verify | `—` |
| [Two stage coax cm choke ft 240 77 ft 240](components/two_stage_coax_cm_choke_ft_240_77_ft_240.md) | · research · forums · fixes ✅ verify | `—` |
| [Uputronics 440 mhz cubesat filtered prea](components/uputronics_440_mhz_cubesat_filtered_prea.md) | · research · forums · fixes ✅ verify | `—` |
| [V30 endurance microsd 128 256 gb](components/v30_endurance_microsd_128_256_gb.md) | · research · forums · fixes ✅ verify | `—` |
| [Waveshare lc76g 24370 rtc cr2032 cell](components/waveshare_lc76g_24370_rtc_cr2032_cell.md) | · research · forums · fixes ✅ verify | `—` |
| [Waveshare mtt bench hub bank powered](components/waveshare_mtt_bench_hub_bank_powered.md) | · research · forums · fixes ✅ verify | `—` |
| [Weather kit ipx4 ip54 mesh foam eptfe ve](components/weather_kit_ipx4_ip54_mesh_foam_eptfe_ve.md) | · research · forums · fixes ✅ verify | `—` |
| [Wideband sdr](components/wideband_sdr.md) | ✅ research ✅ forums ✅ fixes ✅ verify | `wf_e64436d6-ae7` |
| [Wisecoco 7in 1920x1080 2000 nit hdmi kit](components/wisecoco_7in_1920x1080_2000_nit_hdmi_kit.md) | · research · forums · fixes ✅ verify | `—` |

Етапи: research — дослідження; forums — відгуки з форумів; fixes — власні виправлення (лише якщо на форумах не знайшлося рішення); verify — адверсаріальна перевірка.

