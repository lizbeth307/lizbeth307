# Перевірка підключення модулів SR-RX

Це результати програмних моделей, а не дозвіл підключати залізо. Усі фізичні модулі мають стан NOT_TESTED.

Виконання наборів: **PASS**. Реєстр охоплює 754 елементи, 64 вузли та 166 деталізованих інтерфейсів.

PASS означає виконані сценарії конкретного драйвера або моделі. Відсутність реального USB/kernel, аналогового RF, калібрування, живлення або механіки залишається явно записаною в JSON та окремих звітах.

| Модуль | Позначення | Інтерфейс | З’єднання | Драйвер / функція | Ворота / статус джерела |
|---|---|---|---|---|---|
| Molicel INR21700-P50B 5Ah | BT101 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / module |
| Molicel INR21700-P50B 5Ah | BT102 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / module |
| Molicel INR21700-P50B 5Ah | BT103 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / module |
| Molicel INR21700-P50B 5Ah | BT104 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / module |
| Daly DL-J05G-L4S15ATJ 4S15A | U101 | analog_bms_no_software_bus | PASS | Лише з’єднання / не реалізовано |  / module |
| INA228AIDGSR на Adafruit 5832 | U102 | i2c_registers | PASS | Драйвер / модель: PASS |  / verified |
| TPS70933DBVR | U103 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| MCP65R41T-1202E/CHY | U104 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| Pololu 2813 HP | U106 | power_module_enable_pg_analog | PASS | Лише з’єднання / не реалізовано |  / module |
| Pololu D36V50F12#4095 | U107 | power_module_enable_pg_analog | PASS | Лише з’єднання / не реалізовано |  / module |
| Pololu D36V50F5 #4091 — LAB5 default | U108 | power_module_enable_pg_analog | PASS | Лише з’єднання / не реалізовано |  / module |
| XT30 сервісний заряд/розряд | J101 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| DNP — зовнішній balance 4S (GATE) | J102 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано | E1-02 DNP/service-only balance port; charger common-ground fault unresolved / TBD |
| USB-C PD заряд | J103 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| IP2368 COUT 4S retail board | U110 | usb_pd_power_and_unqualified_board_nodes | PASS | Лише з’єднання / не реалізовано | E1-01 retail revision/schematic/NTC/inhibit unresolved / module |
| TPS259470ARPWR USB-C | U109 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| KSD9700 70 °C NO | TH102 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / module |
| TPS259470ARPWR | U201 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS259470ARPWR | U202 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS259470ARPWR | U203 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| LT3045EMSE#PBF | U204 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| LT3045EMSE#PBF | U205 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS2553DBVR-1 | U206 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS2553DBVR-1 | U207 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS2553DBVR-1 | U208 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS2553DBVR-1 | U209 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS2553DBVR-1 | U210 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS7A4701RGWT | U211 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS259630DDAR | U212 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS7A4701RGWT | U213 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS259630DDAR | U214 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| INA3221AIRGVR | U215 | i2c_registers | PASS | Драйвер / модель: PASS |  / design |
| INA3221AIRGVR | U216 | i2c_registers | PASS | Драйвер / модель: PASS |  / design |
| TLV3011BIDBVR | U217 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TLV3011BIDBVR | U218 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TLV3011BIDBVR | U219 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS3701DDCR | U220 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS2553DBVR-1 | U221 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| Q6A J20 2x20 3.3V GPIO | J301 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / verified |
| Power-board control harness DESIGN | J302 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано | project powerboard controlharness assignment / design |
| MCP23017-E/SO #1 0x20 | U301 | i2c_registers | PASS | Драйвер / модель: PASS |  / verified |
| MCP23017-E/SO #3 0x22 | U302 | i2c_registers | PASS | Драйвер / модель: PASS |  / design |
| MCP23017-E/SO #4 0x23 | U303 | i2c_registers | PASS | Драйвер / модель: PASS |  / design |
| Waveshare LC76G GNSS 24370 | U304 | uart_nmea_and_pps | PASS | Драйвер / модель: PASS |  / module |
| Q6A J11 RTC battery 1.25mm | J303 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / verified |
| CR2032 3V primary | BT301 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / design |
| Raspberry Pi Pico SC0915 | U305 | project_uart_mcu | PASS | Драйвер / модель: PASS |  / module |
| LM4040C30IDBZR | U307 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| Power button momentary NO | SW301 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / design |
| PI4IOE5V9555LEX 0x20 | U306 | i2c_registers | PASS | Драйвер / модель: PASS |  / design |
| HOME momentary NO | SW302 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / design |
| BACK momentary NO | SW303 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / design |
| REC momentary NO | SW304 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / design |
| MARK momentary NO | SW305 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / design |
| FN momentary NO | SW306 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / design |
| LOCK momentary NO | SW307 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / design |
| ENC1_PRESS momentary NO | SW308 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / design |
| ENC2_PRESS momentary NO | SW309 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / design |
| TPD4E1U06DBVR | U310 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| TPD4E1U06DBVR | U311 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| PEC11R-4220F encoder | ENC301 | quadrature_contacts | PASS | Драйвер / модель: PASS |  / module |
| PEC11R-4220F encoder | ENC302 | quadrature_contacts | PASS | Драйвер / модель: PASS |  / module |
| TPD4E1U06DBVR | U312 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| TPD4E1U06DBVR | U313 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| Adafruit4162 VEML7700 0x10 | U308 | i2c_registers | PASS | Драйвер / модель: PASS |  / module |
| CPT-1207-3TH | BZ301 | piezo_drive_output | PASS | Лише з’єднання / не реалізовано |  / module |
| NoctuaNF-A4x10 5V nonPWM | FAN301 | motor_power_and_tach | PASS | Драйвер / модель: PASS |  / module |
| Delta BFB0305HA-C 5V 2wire | FAN302 | motor_power_and_tach | PASS | Лише з’єднання / не реалізовано |  / module |
| Waveshare RP2040-Zero 20187 | U309 | project_uart_and_spi_mcu | PASS | Драйвер / модель: PASS |  / module |
| Adafruit 4754 BNO085 SPI | U314 | spi_shtp_sensor | PASS | Драйвер / модель: PASS |  / module |
| Flamingo+ FM v2 #1 | A401 | analog_rf_functional_ports | PASS | Лише з’єднання / не реалізовано |  / module |
| SAWbird+ NOAA 100800 | A402 | analog_rf_functional_ports | PASS | Драйвер / модель: PASS |  / module |
| Flamingo+ FM v2 #2 optional | A403 | analog_rf_functional_ports | PASS | Лише з’єднання / не реалізовано |  / module |
| LNA V2 optional | A404 | analog_rf_functional_ports | PASS | Драйвер / модель: PASS |  / module |
| SMA attenuator 15/20/30 dB: bench selection | A405 | analog_rf_functional_ports | PASS | Лише з’єднання / не реалізовано |  / module |
| Boni-Whip supplied bias-tee | A406 | analog_rf_functional_ports | PASS | Драйвер / модель: PASS |  / module |
| YAT-10A+ 10 dB | A407 | analog_rf_functional_ports | PASS | Лише з’єднання / не реалізовано |  / verified |
| H1 SMA pad 0/2/3 dB | A408 | analog_rf_functional_ports | PASS | Лише з’єднання / не реалізовано |  / module |
| BLK-89-S+ | A409 | analog_rf_functional_ports | PASS | Лише з’єднання / не реалізовано |  / module |
| ANNE-50+ 50 Ω load | A410 | analog_rf_functional_ports | PASS | Лише з’єднання / не реалізовано |  / module |
| RTL-SDR Blog V4L LABRXA | A411 | usb_sdr_native_api | PASS | Драйвер / модель: PASS |  / module |
| RTL-SDR Blog V4L LABRXB | A412 | usb_sdr_native_api | PASS | Драйвер / модель: PASS |  / module |
| Airspy HF+ Discovery | A414 | usb_sdr_native_api | PASS | Драйвер / модель: PASS |  / module |
| LimeSDR Micro M.2 v1.2 receive-only | A415 | pcie_sdr_native_api | PASS | Драйвер / модель: PASS |  / module |
| Uputronics 440 Rev 3.0 external LNA | A418 | analog_rf_functional_ports | PASS | Драйвер / модель: PASS |  / module |
| GOES / H1 / iO / active patch external LNA | A419 | analog_rf_functional_ports | PASS | Драйвер / модель: PASS |  / module |
| Othernet Bullseye LNB | A420 | analog_rf_functional_ports | PASS | Драйвер / модель: PASS |  / module |
| AXING CFA 11-00 DC-isolated 75 Ω load | A421 | analog_rf_functional_ports | PASS | Лише з’єднання / не реалізовано |  / module |
| TCBT-2R5G+ ch4 | A424 | analog_rf_functional_ports | PASS | Драйвер / модель: PASS |  / verified |
| P1 VHF137 SMA: no DC | J401 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| P2 UHF SMA: 4.5 V | J402 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| P3 L-band SMA: 4.5 V | J403 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| P4 LNB F: 13.2 V | J404 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| P5 HF BNC: 13.8 V | J405 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| P6 VHF/AIS SMA: no DC | J406 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| P7 GNSS SMA | J407 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| P8 WIDE optional SMA | J408 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| BENCH internal SMA | J409 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| RTL-A RF internal SMA | J410 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| RTL-B RF internal SMA | J411 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| RX1 edge SMA | J412 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| RX1 panel SMA: captive loop | J413 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| RX2 panel SMA | J414 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| REF IN panel SMA | J415 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| UHF antenna feed / A418 input interface | J416 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| L-band antenna feed / A419 input interface | J417 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| Goobay 58814 75 Ω F-F 1 m | W401 | passive_cable_connectivity | PASS | Лише з’єднання / не реалізовано |  / module |
| 75 Ω shielded internal IF coax | W402 | passive_cable_connectivity | PASS | Лише з’єднання / не реалізовано |  / module |
| RX1 panel → Lime X2 MHF4 coax | W403 | passive_cable_connectivity | PASS | Лише з’єднання / не реалізовано |  / module |
| RX2 → Lime X4 MHF4 coax | W404 | passive_cable_connectivity | PASS | Лише з’єднання / не реалізовано |  / module |
| REF IN → J4 MHF4 coax | W405 | passive_cable_connectivity | PASS | Лише з’єднання / не реалізовано |  / module |
| CAB.01075 X1 → ANNE-50+ captive coax | W406 | passive_cable_connectivity | PASS | Лише з’єднання / не реалізовано |  / module |
| P7 SMA → LC76G IPEX coax | W407 | passive_cable_connectivity | PASS | Лише з’єднання / не реалізовано |  / module |
| RG316 common-mode choke FT240-77 +2631102002 | W408 | passive_cable_connectivity | PASS | Лише з’єднання / не реалізовано |  / module |
| Captive RX1 edge → profile pad coax | W409 | passive_cable_connectivity | PASS | Лише з’єднання / не реалізовано |  / module |
| Nooelec LaNA WB 100845 | A422 | analog_rf_functional_ports | PASS | Драйвер / модель: PASS |  / module |
| sysmocom cf2235-kt30 2170–2300 MHz | A423 | analog_rf_functional_ports | PASS | Лише з’єднання / не реалізовано |  / module |
| RG316 SMA-M/M 0.10 m helix → LaNA | W422 | passive_cable_connectivity | PASS | Лише з’єднання / не реалізовано |  / design |
| RG316 SMA-M/M 0.10 m LaNA → DC block | W423 | passive_cable_connectivity | PASS | Лише з’єднання / не реалізовано |  / design |
| RG316 SMA-M/M 1.00 m pod → RX2 | W424 | passive_cable_connectivity | PASS | Лише з’єднання / не реалізовано |  / design |
| USB-C power-only 1.50 m, 26 AWG pair | W425 | passive_cable_connectivity | PASS | Лише з’єднання / не реалізовано |  / design |
| Existing S-band helix feed SMA | J422 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / module |
| Mini-Circuits BLK-89-S+ pod DC block | A425 | analog_rf_functional_ports | PASS | Лише з’єднання / не реалізовано |  / module |
| G6K-2F-RF-S DC5 HF | K401 | physical_state_input_or_analog_load | PASS | Драйвер / модель: PASS |  / verified |
| G6K-2F-RF-S DC5 VHF | K402 | physical_state_input_or_analog_load | PASS | Драйвер / модель: PASS |  / verified |
| HMC7992LP3DE A | U405 | analog_or_discrete_control_ic | PASS | Драйвер / модель: PASS |  / verified |
| HMC7992LP3DE B | U406 | analog_or_discrete_control_ic | PASS | Драйвер / модель: PASS |  / verified |
| HMC7992LP3DE C | U407 | analog_or_discrete_control_ic | PASS | Драйвер / модель: PASS |  / verified |
| LM4040A20IDBZR 2.048 V 0.1% shunt | U458 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| TLV3012BIDBVR | U456 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| TLV3012BIDBVR | U457 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| TLV3012BIDBVR | U450 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| TLV3012BIDBVR | U451 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| TLV3012BIDBVR | U452 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| TLV3012BIDBVR | U453 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| TLV3012BIDBVR | U454 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| TLV3012BIDBVR | U455 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| Q6A onboard peripheral rail sources | U500 | sbc_internal_power_subinterface | PASS | Лише з’єднання / не реалізовано |  / module |
| Q6A J21 existing header pads | J521 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / verified |
| J21 service harness 3pin locking | J503 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано | project serviceharness assignment; physical qualification required / design |
| Q6A J5 stacked USB3 lower / USB2 upper | J511 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / verified |
| Q6A J2 stacked USB2 bank1 P3 / bank2 P2 | J512 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / verified |
| Adafruit5997 CH334F revC board | U510 | usb_hub_connectivity | PASS | Лише з’єднання / не реалізовано |  / module |
| LAB USB-A panel receptacle | J501 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / design |
| RTL-A USB cable endpoint | J543 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / design |
| RTL-B split-VBUS USB cable endpoint | J541 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / design |
| HF+ microUSB-B cable endpoint | J544 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS2553DBVR-1 | U501 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS2553DBVR-1 | U502 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS2553DBVR | U503 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| TPS2553DRVR | U505 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| Samsung T7 + intact A-to-C USB3 cable | U540 | usb_storage_block_device | PASS | Драйвер / модель: PASS |  / module |
| Q6A HDMI Type-A existing port | J520 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано |  / verified |
| Wisecoco display/controller assembly | U520 | hdmi_touch_vendor_backlight_unknown | PASS | Драйвер / модель: PASS | E3-02,E5-01 received display touch/DC/brightness interfaces unresolved / module |
| LM66100DCKR HDMI5V ideal diode | U506 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / design |
| Q6A MKEY host lane0 functional interface | J530 | pcie_host_interface | PASS | Лише з’єднання / не реалізовано | functional MKEY subset only, not full physical numbering / module |
| ADT-Link R44SF 5cm modified riser | U530 | pcie_pass_through_connectivity | PASS | Лише з’єднання / не реалізовано | E5-03 exactriser contacts/cutpoints unresolved / module |
| UART5 console 3pin locking | J502 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано | project UART5harness assignment / design |
| EDL recessed momentary NO | SW501 | physical_state_input_or_analog_load | PASS | Лише з’єднання / не реалізовано |  / design |
| Q6A factory EDL button functional pads | J522 | factory_button_pad_interface | PASS | Лише з’єднання / не реалізовано |  / module |
| LAB BUS 6pin locking DESIGN | J505 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано | projectLABBUSpin assignment, not a factoryconnectorprotocol / design |
| Olimex GX16-4 IMU DESIGN pinout | J504 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано | project GX16pin assignment; actual harness orientation/continuity unqualified / design |
| TPD4E1U06DBVR | U551 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| IMU pack cable termination DESIGN | J550 | passive_connector_or_named_boundary | PASS | Лише з’єднання / не реалізовано | project IMU cable termination; actual harness unqualified / design |
| TPD4E1U06DBVR | U552 | analog_or_discrete_control_ic | PASS | Лише з’єднання / не реалізовано |  / verified |
| TCA9517DR | U507 | i2c_electrical_buffer | PASS | Лише з’єднання / не реалізовано |  / design |

## Каталожні та заводські вузли

Ці сутності не мають окремого схемного символу/повної розпіновки в E1–E5. Їхні vendor interfaces залишаються NOT_TESTED; перевірка файлової системи або пов'язаного ref не підтверджує внутрішній контролер.

| Сутність | Інтерфейс | Межа | Результат |
|---|---|---|---|
| Radxa UFS3.1 storage module | FactoryQ6A UFS/block storage | core_onboard_not_separately_symbolized | CATALOGUE_ONLY / NOT_TESTED |
| Rescue microSD and USB card reader | microSD/USBmass-storage | support_or_optional_storage | CATALOGUE_ONLY / NOT_TESTED |
| Spare RTL-SDR Blog V4L | USBSDR API andRFinput | spare_not_simultaneously_core_A411_A412 | CATALOGUE_ONLY / NOT_TESTED |
| Airspy Mini optional receiver | USBSDR/libairspy plusRFinput | gated_optional_not_in_final_graph | CATALOGUE_ONLY / NOT_TESTED |
| FlightAware Pro Stick Plus | USBlibrtlsdr;LABUSB-A | lab_extended_optional | CATALOGUE_ONLY / NOT_TESTED |
| SAWbird+ GOES antenna assembly variant | RF+coax bias power | mutually_exclusive_A419_profile_variant | CATALOGUE_ONLY / NOT_TESTED |
| SAWbird+ H1 antenna assembly variant | RF+coax bias power | mutually_exclusive_A419_profile_variant | CATALOGUE_ONLY / NOT_TESTED |
| SAWbird+ iO antenna assembly variant | RF+coax bias power | gated_mutually_exclusive_A419_profile_variant | CATALOGUE_ONLY / NOT_TESTED |
| Active L-band patch assembly variant | RF+coax bias power | mutually_exclusive_A419_profile_variant | CATALOGUE_ONLY / NOT_TESTED |
| Boni-Whip active antenna | RF+coax power throughsuppliedbias-tee | external_antenna | CATALOGUE_ONLY / NOT_TESTED |
| GNSS antenna/feed | coaxRF/bias_if_selected | external_antenna | CATALOGUE_ONLY / NOT_TESTED |
| Passive patch/helix/dipole/Yagi/HFwire9:1/QO100horn assemblies | RFports/environment | core_and_backpack_physical_assemblies | CATALOGUE_ONLY / NOT_TESTED |
| 65–100W USB-C PD mains source/cable | USBPDCCpowercontracts | external_charge_source | CATALOGUE_ONLY / NOT_TESTED |
| Anker737 power bank | USBPDsource/contracts | external_charge_source | CATALOGUE_ONLY / NOT_TESTED |
| ISDT608PD service charger | PDinput,XT30output,4Sbalanceconnections | service_mode_BLOCKED_E1_02 | CATALOGUE_ONLY / NOT_TESTED |
| Waveshare externallypowered MTTbenchhub | USB2hubplus5Vbenchpower | bench_support | CATALOGUE_ONLY / NOT_TESTED |
| External RF sled v2 | LABI2CB/AUX12/GND/SLEDDET;MCP#2at0x21,ADS1115at0x48 | extended_external_assembly | CATALOGUE_ONLY / NOT_TESTED |
| AD8318-class detector +ADS1115 | RFpower→analogvoltage→externalADS1115I2CB | extended_external_assembly | CATALOGUE_ONLY / NOT_TESTED |
| DIYconducted noise-sourceassembly withZFL500seriesamplifier | AUX12NOISE_EN,RFoutputthroughpermanentpad | bench_only_external_assembly | CATALOGUE_ONLY / NOT_TESTED |
| LeoBodnarLBE1420GPSDO | USBHIDconfiguration,5Vpower,RFclockreference | extended_external_instrument | CATALOGUE_ONLY / NOT_TESTED |
| LiteVNA64 | RFports andexternalUSBcontrol/data | bench_instrument | CATALOGUE_ONLY / NOT_TESTED |
| tinySAUltra+ZS407 | RFmeasurement/source andexternalUSB | bench_instrument | CATALOGUE_ONLY / NOT_TESTED |
| FNIRSIFNB58Std noradio | USB-Cpower/PDtester/logger | bench_instrument | CATALOGUE_ONLY / NOT_TESTED |
| FNIRSIDPS150 benchsupply | Poweroutput andoptionalvendorcontrol | bench_instrument | CATALOGUE_ONLY / NOT_TESTED |
| ANENGAN8008/9 DMM | Manualelectricalmeasurements | manual_bench_instrument | CATALOGUE_ONLY / NOT_TESTED |
| Hantek6022BE | USBOscilloscope/OpenHantek6022 | bench_instrument | CATALOGUE_ONLY / NOT_TESTED |
| CY7C68013A fx2lafwlogic analyzer | USB/sigrok logiccapture | bench_instrument | CATALOGUE_ONLY / NOT_TESTED |
| RaspberryPiDebugProbeSC0889 | USBCMSIS-DAPv2/SWD/3.3VUART | bringup_instrument | CATALOGUE_ONLY / NOT_TESTED |
| PinecilV2 IronOS | USBPDpower/manualheater | manual_bench_tool | CATALOGUE_ONLY / NOT_TESTED |
| QCS6490HexagonHTP/QAIRT/FastRPC andAdreno | VendorLinuxkernel/drivers/DSPfirmware/runtimeAPI | factory_platform_internal | CATALOGUE_ONLY / NOT_TESTED |
