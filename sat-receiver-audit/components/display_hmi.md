# Display hmi: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_d9388111-e66`_

- **Subsystem:** display_hmi (Wisecoco 7in FHD 2000-nit kit + 4D Systems fallback, field EDID/pixel clock and harmonic scan, sun/thermal, glove touch, RP2040 Pico HMI with encoders and keys)
- **Findings:**
  1.
    - **Claim in stack:** 2.6 / #74-76: Wisecoco 7in (6.97in) 1920x1080 LTPS, $132, InStock, 0 reviews, '2000+ cd/m2 typ' in table and '2500' only in title, 316 PPI
    - **Finding:** Re-read 18 Oct 2026. Price $132.00 (list $135.00). schema.org availability is InStock. Reviews: 0. The page was last modified 2026-09-17. Brightness: '2000+ cd/m2 (Typ.)' in the list and '2000cd/m2' in the table; '2500Nits' appears only in the title. The page gives two different active areas: 154.368x86.832 mm in the table (6.97in, 316 PPI) and 155.82x87.83 mm in the list (7.04in, about 313 PPI). Outline is 164.22x97.98 mm. The page has no variants and no package contents.
    - **Verdict:** confirmed
    - **Action:** Keep the gate. Size the bezel only from the measured glass (D5 already says this).
    - **Impact:** No change to price or BOM.
    - **Sources:**
      - https://www.wisecocodisplay.com/product/7-inch-1920x1080-high-brightness-2500nits-lcd-panel-with-hdmi-in-board-ips-mipi-interface-tft-lcd-screen/
  2.
    - **Claim in stack:** Wisecoco touch must be USB-HID (gate); listing still says 'I2C Capacitive Touch'
    - **Finding:** Still true. The page description reads 'HDMI Driver Board, Mipi Interface and I2C Capacitive Touch', and the spec table lists 'Interface Type: I2C'. USB is not mentioned anywhere. The only USB evidence is for a different Wisecoco 7in kit: a Raspberry Pi forum post from Apr 2024 shows it enumerating as 1a86:e5e3 'wch.cn CH57x' under hid-multitouch. In the same thread the poster later says the unit itself was failing, on a Pi 3 as well.
    - **Verdict:** confirmed
    - **Action:** Keep D5. Also ask Wisecoco: the touch IC, whether the touch is in-cell/TDDI, and how the USB-C VBUS behaves (see the VBUS finding).
    - **Impact:** The gate is still unmet as of the 2026-09-17 page revision.
    - **Sources:**
      - https://www.wisecocodisplay.com/product/7-inch-1920x1080-high-brightness-2500nits-lcd-panel-with-hdmi-in-board-ips-mipi-interface-tft-lcd-screen/
      - https://forums.raspberrypi.com/viewtopic.php?t=368455
  3.
    - **Claim in stack:** D5: operating temperature is one of the questions to ask Wisecoco
    - **Finding:** The listing now answers it: operating -20 to 70 C, storage -30 to 80 C. The likely twin glass, Youritech ET070FH01-HT, has the same 154.368x86.832 mm active area, a 164.19x97.87 mm outline, the same -20 to 70 C / -30 to 80 C ratings, 2000 cd/m2 typical and in-cell touch. Youritech offers optical bonding only as a customisation.
    - **Verdict:** corrected
    - **Action:** Remove temperature from the question list. Keep the 70 C derating in the thermal model, which already shows 71 C at 35 C ambient in sun at 100%.
    - **Impact:** Confirms that the existing NTC derating (above 60 C go to 50%, above 68 C go to 20%) is needed.
    - **Sources:**
      - https://www.wisecocodisplay.com/product/7-inch-1920x1080-high-brightness-2500nits-lcd-panel-with-hdmi-in-board-ips-mipi-interface-tft-lcd-screen/
      - https://www.youritech.com/products/7-inch-tft-lcd-display-1920x1080-mipi-2000nits-high-brightness-lcd-display-with-in-cell-touch-for-healthcare-medical-display-solution.html
  4.
    - **Claim in stack:** Wisecoco is the main pick if it is bonded (6.2:1 at 100 klx with AR vs 1.5:1 with an air gap)
    - **Finding:** The contrast model holds: it implies about 1.2% reflectance when bonded with AR and about 12% with an air gap (my recalculation). If the panel is the in-cell Youritech twin, there may be no separate cover glass at all, and 'bonding' would only mean a cover lens that Wisecoco adds. In-cell or TDDI touch often needs host-side firmware or a vendor MCU, and its sensitivity drops through a thick cover lens. Both points are inference.
    - **Verdict:** new_risk
    - **Action:** Add to the D5 questions: is the touch in-cell or a separate CTP? What is the cover-lens thickness, and is it bonded? Reject the panel if it is in-cell with no USB-HID MCU.
    - **Impact:** If the touch is in-cell, a thick protective lens or gloves may disable it; the encoders and keys already cover every critical action.
    - **Sources:**
      - https://www.youritech.com/products/7-inch-tft-lcd-display-1920x1080-mipi-2000nits-high-brightness-lcd-display-with-in-cell-touch-for-healthcare-medical-display-solution.html
  5.
    - **Claim in stack:** Fallback 4D 4DHDMI-70-1280-800-CT-EAR-1000: 1000 nit, bonded, 12 V 540 mA, -20...70 C, GT928 touch on USB-C
    - **Finding:** The datasheet (Rev 1.0, 08/08/2025) confirms: 'Capacitive Touch, Glass 1:1 size of LCD. Optical Bonded to LCD'; 1000 cd/m2 typical; 800:1 contrast; 12 V 540 mA typical on the barrel jack (about 6.5 W), or 5 V 1300 mA on USB; operating -20 to +70 C, storage -30 to +80 C; 'USB-C Power and Touch Interface'; Mini-HDMI (19-pin), HDMI 1.4. The datasheet does not name the touch IC, so GT928 is not confirmed.
    - **Verdict:** confirmed
    - **Action:** Keep it as the fallback. Change 'GT928' to 'touch IC unverified (USB-HID per datasheet)'.
    - **Impact:** The 4D numbers already used for the power budget (6.5 W) are right.
    - **Sources:**
      - https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_0.pdf
  6.
    - **Claim in stack:** 4D price: $128.95 at DigiKey (13 pcs, then 4 weeks) / $141.85 at the 4D store
    - **Finding:** DigiKey 1613-4DHDMI-70-1280-800-CT-EAR-1000-ND: $128.95, 13 in stock, 4-week standard lead time, status Active. Its short description wrongly reads '9.0in 1280 X 800 500CD/M2'; the detailed description is correct (7in). The 4D store variant 'Capacitive / 1280 x 800 - 1000 cd/m2 / Display Tabs' is $141.85 and available; the product record was updated 2026-10-02.
    - **Verdict:** confirmed
    - **Action:** Check the manufacturer part number on the order line because of the DigiKey description error.
    - **Impact:** No price change.
    - **Sources:**
      - https://www.digikey.com/en/products/result?keywords=4DHDMI-70-1280-800-CT-EAR-1000
      - https://4dsystems.com.au/products/4dhdmi-7-0
  7.
    - **Claim in stack:** D4/D5 and Pico GP17: backlight dimming is analog/DC from the Pico; derate on panel NTC; the 4D comes with a per-profile modeset table
    - **Finding:** On the 4D, brightness is adjusted only through the OSD. The OSD buttons sit on an external button board that is 'available on request' and does not ship by default; it connects through a 10-pin 2.0 mm port (Menu/Down/Up/Enter/Power). The datasheet offers DDC/CI only as a customisation. The standard cover glass has no AR, AG or AF treatment. So on the fallback, Pico GP17 has nothing to drive, and the thermal derating and VEML7700 auto-brightness do not work out of the box.
    - **Verdict:** new_risk
    - **Action:** If the 4D is ordered: also request the OSD button board and drive it from the Pico with open-drain lines (pinout to be confirmed by 4D), or ask 4D for DDC/CI. Keep the AR film. Ask Wisecoco the same question (backlight IC, how dimming is controlled), which dropped out of the D5 list.
    - **Impact:** Without this, the fallback has fixed brightness and no thermal derating (it does run cooler at 6.5 W).
    - **Sources:**
      - https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_0.pdf
  8.
    - **Claim in stack:** C5 / 5.2: J2a = FE1.1s P2 carries USB-HID touch from the display board with its VBUS not connected; HDMI pin 18 cut or diode
    - **Finding:** On the 4D, a single USB-C carries both power and touch, and the datasheet says this port's power 'parallels' the other power input. If VBUS is cut, the touch device may not enumerate, because many device controllers wait for VBUS before attaching. If VBUS is connected, the panel can draw up to 1.3 A from the hub. Separately, cutting HDMI pin 18 (+5 V) can stop many HDMI receivers from asserting HPD, since HPD is often pulled up from that +5 V. The RA620 would then report no sink. All of this is inference from the HDMI and USB specs.
    - **Verdict:** new_risk
    - **Action:** Use a series Schottky on HDMI pin 18, not a cut, and check HPD on the bench. For touch, feed VBUS through a 100 mA current-limited, diode-isolated 5 V sense line, or confirm with the vendor that the touch enumerates without VBUS. Add an HPD/enumeration step to the 20-cold-boot acceptance test.
    - **Impact:** Without these, the panel may not be detected or touch may not appear on a board that is otherwise correct.
    - **Sources:**
      - https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_0.pdf
  9.
    - **Claim in stack:** C12: field EDID DTD1 151.50 MHz (2200x1148, 59.99 Hz, clean window 148.11-153.27) and DTD2 127.90 MHz (2200x1125, 51.68 Hz, clean 123.62-128.04); 148.5 bring-up only; 128.70 banned
    - **Finding:** My own scan (model) used 14 core windows from STACK sections 4 and 5.7: FM, VOR, LRPT 137-138, 2 m, AIS, DAB III 174-240, sondes 400-406, 70 cm, QO-100 NB IF, ADS-B, H1 1418-1423, Inmarsat-C 1537-1544.2, GNSS 1559-1610, HRPT 1686-1711. Settings: 0.5 MHz guard, harmonics up to 2.5 GHz. Clean windows: 123.89-128.04 and 148.12-153.22 MHz, which matches the STACK windows. Adding the optional US UAT, NOAA WX, Region 2 2 m, L5/E5a and QO-100 WB IF narrows them to 124.92-128.04 and 149.90-153.22. 151.50 has no hit; nearest is 5.5 MHz (1st harmonic vs 2 m). 127.90 has no hit; nearest is 12x = 1534.8 MHz, 2.2 MHz below Inmarsat-C, with only 0.14 MHz (0.11%) of headroom above it. With 0.5% downspread SSC, neither mode hits a core band. 151.5x15 = 2272.5 MHz lands inside the Lime-only S-band, 13.5 MHz from Black Kite, as STACK says. 148.5 MHz: x5 = 742.5 (QO-100 WB IF; with SSC it smears into the NB IF), x8 = 1188 (L5). 128.70 MHz: x12 = 1544.4 (0.2 MHz from Inmarsat-C). Both confirmed.
    - **Verdict:** confirmed
    - **Action:** Keep both DTDs. After bring-up, measure the real pixel clock in debugfs. If it comes out above about 128.0 MHz, use only 151.50.
    - **Impact:** The pixel-clock plan is sound for every core band (model, not a measurement).
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/disp_hmi_r2/calc/scan.py
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/disp_hmi_r2/calc/win.py
  10.
    - **Claim in stack:** C12 / 5.7: the 151.5 line rate of 68.86 kHz is at least 8.6 kHz from every LF carrier; the 127.9 line rate of 58.14 kHz is 1.86 kHz from 60 kHz
    - **Finding:** Recalculated nearest-harmonic offsets. 68.864 kHz: 60 kHz 8.86, 77.5 kHz 8.64, 40 kHz 28.9, 162 kHz 24.3, 518 kHz 32.9, 4209.5 kHz 8.82, and 490 kHz NAVTEX only 7.95 kHz (7x = 482.05 kHz). 58.136 kHz: 60 kHz 1.86, 518 kHz 5.23, 162 kHz 12.4.
    - **Verdict:** corrected
    - **Action:** Change the wording to 'at least 8.6 kHz from every LF time-signal carrier; 7.95 kHz from NAVTEX 490 kHz'. This is harmless for 170 Hz FSK.
    - **Impact:** Wording only.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/disp_hmi_r2/calc/other.py
  11.
    - **Claim in stack:** C12 'two DTDs in order of attempt', video=HDMI-A-1:1920x1080@60 or @52, mode pinned in the labwc output config
    - **Finding:** (1) labwc has no output-mode setting in rc.xml. Its manual says outputs are managed by an external wlr-output-management tool such as wlr-randr or kanshi, and only later labwc versions add <reuseOutputMode>. kanshi 1.5.1-1 is in noble universe for arm64. (2) wlroots uses the EDID preferred mode, which is DTD1, by default. The host cannot tell whether the sink actually displays a mode, so 'order of attempt' can only be a bench procedure, not a runtime fallback. (3) The kernel's cmdline match compares the integer-rounded refresh (drm_mode_vrefresh): 59.988 rounds to 60 and 51.68 to 52, so @60/@52 do match. That part is my reading of the source.
    - **Verdict:** corrected
    - **Action:** Pin the mode with a kanshi profile (e.g. mode 1920x1080@59.988Hz) started from labwc autostart, or with wlr-randr. After acceptance, ship an EDID whose preferred DTD is the accepted mode. Optionally add the 'e' force flag to video=.
    - **Impact:** As written, the labwc 'output config' step cannot be implemented.
    - **Sources:**
      - https://labwc.github.io/labwc-config.5.html
      - https://packages.ubuntu.com/noble/kanshi
  12.
    - **Claim in stack:** #20 / 5.4: HDMI only, through the RA620 DP-to-HDMI bridge on connector HDMI-A-1; EDID override from initramfs; 2 HBR2 lanes
    - **Finding:** The local Radxa 6.18.2 and 7.0.11 DTS both have compatible 'radxa,ra620' on simple-bridge with DRM_MODE_CONNECTOR_HDMIA, and mdss_dp_out data-lanes <0 1>. The packaged config-6.18.2-4-qcom has DRM_MSM=y (built-in, so the EDID file must be in the initramfs), DRM_LOAD_EDID_FIRMWARE=y, DRM_SIMPLE_BRIDGE=y, HID_MULTITOUCH=m, TOUCHSCREEN_GOODIX=m and EDT_FT5X06=m. 7.0.11-7 changes DRM_MSM to m. The drm.edid_firmware=[<connector>:]<file> syntax is confirmed in kernel-parameters.txt. Radxa states HDMI 2.0 at 4K30 (297 MHz), which fits the roughly 360 MHz 2-lane HBR2 ceiling.
    - **Verdict:** confirmed
    - **Action:** Keep it. Add an initramfs-tools hook that copies edid/field.bin, and on path B (7.0.11) still keep the file in the initramfs.
    - **Impact:** None.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/radxa/q6a-linux-6.18.2.dts
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl/skeptic_sw/x6182/boot/config-6.18.2-4-qcom
      - https://raw.githubusercontent.com/torvalds/linux/master/Documentation/admin-guide/kernel-parameters.txt
      - https://radxa.com/products/dragon/q6a/
  13.
    - **Claim in stack:** 5.7 known-lines table and A/B matrix (SSC assumed for the 148.5 smear)
    - **Finding:** In upstream msm dp_ctrl.c, link training uses panel->link_info.rate, the sink's maximum, whatever the mode is. The PHY SSC is switched on (DP_SPREAD_AMP_0_5) whenever the sink's DPCD reports MAX_DOWNSPREAD. So a 0.5% downspread is likely, and the link rate does not follow the pixel clock. If the RA620 ever advertises only RBR, the 162.000 MHz link symbol clock would fall between the two AIS channels; at HBR or HBR2 (270/540 MHz) there are no core hits (model).
    - **Verdict:** new_risk
    - **Action:** Add a check of the DP link rate and lane count in debugfs or dmesg (drm.debug) to the bench steps. If it is RBR, add 162.000 MHz to the known-lines table and to the AIS A/B test.
    - **Impact:** Low probability: with 2 lanes, a 1080p field mode needs at least HBR.
    - **Sources:**
      - https://raw.githubusercontent.com/torvalds/linux/master/drivers/gpu/drm/msm/dp/dp_ctrl.c
  14.
    - **Claim in stack:** D5 asks Wisecoco for the DSI mode and the bridge lane rate
    - **Finding:** Model: in non-burst mode with 4 lanes and 24 bpp, the DSI HS clock is 3x the pixel clock (383.7 MHz at 127.9, 454.5 MHz at 151.5). Its harmonics are a subset of the pixel harmonics, so they stay clean; the lane rate is 767 or 909 Mbps. Two things on the panel board are not controlled by the EDID: a burst-mode DSI PLL, and the board's own crystal. A 27 MHz crystal would land exactly on 162.000 (AIS, x6), 1701.0 (Metop AHRPT 1701.3, x63), 405.0 (sondes, x15), 432.0 and 1539.0 (Inmarsat-C range). 24 MHz gives 1704 and 144; 25 MHz is already listed.
    - **Verdict:** new_risk
    - **Action:** Add to the D5 questions: bridge IC, pass-through or scaler, crystal frequency, and burst-mode lane rate. Add the panel board's crystal comb to the 5.7 known-lines table once it is known.
    - **Impact:** A crystal comb from a board 1-2 cm behind the glass could cost dB on AIS, Metop or sondes; only the A/B test would catch it.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/disp_hmi_r2/calc/other.py
  15.
    - **Claim in stack:** D5 fallback: order the 4D 'with a per-profile modeset table in labd' (no field pixel clock is defined for 1280x800)
    - **Finding:** Model scan for 1280x800: the usual 71.0 MHz (CVT-RB) hits H1 1420.0 (x20), BDS B1 1562 (x22), HRPT 1704 (x24) and DAB 213 (x3). 72.4 MHz hits 144.8, 434.4 and 1592.8. 83.5 MHz hits 1419.5 (H1). Between 50 and 123 MHz the only clean window is 81.5-82.0 MHz (81.63-82.03 with optional bands), for example 81.8 MHz with 1440x947 totals (59.99 Hz) or 1680x812 (59.96 Hz), which leaves only about ±0.25% margin. Because the 4D has an OSD, it probably has a scaler (inference). In that case its panel-side clock is fixed by the 4D board, and no host EDID can move it.
    - **Verdict:** new_risk
    - **Action:** Before ordering, ask 4D for the panel timing, whether the board scales, and the board crystal. Define a 4D field EDID at about 81.8 MHz if the board passes timing through. Otherwise rely on shielding plus the A/B test, and note the possible line at H1 1420.0.
    - **Impact:** The fallback could put a line on H1, GNSS or HRPT that the field EDID cannot remove.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/disp_hmi_r2/calc/win4d.py
      - https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_0.pdf
  16.
    - **Claim in stack:** HDMI cable: Adafruit 2420 (short, shielded) + 2x Wurth 74271140, 10-15 cm, Mix-31/61 ferrites; budget FPC kit 3548+3560 at $14.50
    - **Finding:** Adafruit 2420 is a 'Slim HDMI Cable - 450mm', $9.95, in stock; the page does not state shielding or connector types. Wurth 74271140 is a WE-STAR-TEC for 2-3 mm cable, NiZn material '4 W 620', 92 ohm at 25 MHz and 178 ohm at 100 MHz, $3.91 at DigiKey. It is not a Fair-Rite Mix-31/61 part and may not fit an HDMI cable. The FPC kit price checks out (3548 $6.50 x2 + 3560 10 cm $1.50 = $14.50), but the ribbon is unshielded. The 4D input is Mini-HDMI, so it needs 3552 (straight Mini HDMI plug) instead.
    - **Verdict:** corrected
    - **Action:** Specify a 10-15 cm shielded HDMI A to (panel connector) cable. Buy a snap ferrite sized to that cable's outer diameter, either Fair-Rite 31/61 or Wurth STAR-FIX/TEC of the right size. If the FPC kit is used, wrap it in grounded copper tape. Use 3552 for the 4D.
    - **Impact:** The cable line ($17.77) needs re-pricing; the 45 cm cable cannot be the 10-15 cm run.
    - **Sources:**
      - https://www.adafruit.com/product/2420
      - https://www.adafruit.com/product/3548
      - https://www.adafruit.com/product/3560
      - https://www.we-online.com/en/components/products/WE-STAR-TEC
      - https://www.digikey.com/en/products/result?keywords=74271140
  17.
    - **Claim in stack:** VEML7700 drives the Day/Night/Red themes and sits outside the hood
    - **Finding:** Datasheet Rev 1.8 (28-Nov-2024): range 0 to about 140 klx at gain 1/8 and IT 25 ms; resolution down to 0.0042 lx/ct; fixed address 0x10. Direct sun (about 100-120 klx) is within range, and 0x10 does not collide with the PCA9555 at 0x20 on Pico I2C0.
    - **Verdict:** confirmed
    - **Action:** Use gain 1/8 and IT 25 ms whenever the reading exceeds about 20 klx.
    - **Impact:** None.
    - **Sources:**
      - https://www.vishay.com/docs/84286/veml7700.pdf
  18.
    - **Claim in stack:** D16 / 5.6: sustained about 1000 nit in noon sun; panel about 71 C at 35 C, 100%, above its 70 C rating; hood, NTC derating
    - **Finding:** Both panels are rated -20 to 70 C operating and -30 to 80 C storage (Wisecoco listing, 4D datasheet), so the derating plan is needed and correctly placed. New: an unpowered device left face-up in sun can exceed the 80 C storage limit. The polariser axis (polarised sunglasses) was in the display_market conditions but is missing from D5.
    - **Verdict:** new_risk
    - **Action:** Close the hood as a lid when stored, and add a 'do not leave face-up in sun' label. Add the polariser transmission axis to the D5 questions, and test with polarised glasses during acceptance.
    - **Impact:** Panel damage from heat in storage; a screen that goes black through polarised glasses outdoors.
    - **Sources:**
      - https://www.wisecocodisplay.com/product/7-inch-1920x1080-high-brightness-2500nits-lcd-panel-with-hdmi-in-board-ips-mipi-interface-tft-lcd-screen/
      - https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_0.pdf
  19.
    - **Claim in stack:** D16 / #52: capacitive touch does not work through gloves, so encoders and keys cover every critical action; targets of 15-20 mm
    - **Finding:** Neither the Wisecoco page nor the 4D datasheet documents a glove mode. The Youritech twin claims 'PCAP touch with glove compatibility' only as a marketing line. The GT928 datasheet is not reachable at Goodix and the controller is unconfirmed anyway. The design principle is correct.
    - **Verdict:** confirmed
    - **Action:** Keep 'every item works by buttons and encoders' as an acceptance test. Treat glove touch as a bonus to test on arrival.
    - **Impact:** None.
    - **Sources:**
      - https://www.youritech.com/products/7-inch-tft-lcd-display-1920x1080-mipi-2000nits-high-brightness-lcd-display-with-in-cell-touch-for-healthcare-medical-display-solution.html
      - https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_0.pdf
  20.
    - **Claim in stack:** HMI MCU: Raspberry Pi Pico (RP2040), 2 pcs, GBP 3.80 each at The Pi Hut (marked unverified); 26 GPIO; pin map in 5.2
    - **Finding:** The Pi Hut lists SC0915 (no headers) at GBP 3.80, available. The Raspberry Pi list price is from $4. The 'Pico 1 series will remain in production until at least January 2036'. Pico datasheet build 03/07/2026: VSYS 1.8-5.5 V, GPIO24 is the internal VBUS sense, GPIO23 is the SMPS PS pin. The pin map is valid: UART0 GP0/1, UART1 GP8/9, I2C0 GP4/5, encoders on consecutive pins for the PIO quadrature program, ADC GP26-28, GP24 internal. Current Pico SDK is 2.3.1 (4 Sep; 2.3.0 on 3 Jul; the page shows no year, 2026 inferred). RP2040's default clk_sys stays 125 MHz; 200 MHz has been opt-in since SDK 2.1.1.
    - **Verdict:** confirmed
    - **Action:** Mark the line as verified. World price: $4.00 list, $8.00 for two plus shipping.
    - **Impact:** The price is at most about $2 lower in USD; no design change.
    - **Sources:**
      - https://thepihut.com/products/raspberry-pi-pico
      - https://www.raspberrypi.com/products/raspberry-pi-pico/
      - https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
      - https://github.com/raspberrypi/pico-sdk/releases
  21.
    - **Claim in stack:** 5.7 known lines: 12 MHz (hub, RP2040) at 144.000 / 432.000 / 1704.0 MHz
    - **Finding:** Confirmed, and there are more RP2040-side sources (model). (1) clk_sys must stay at 125 MHz, which has no core hits. The 200 MHz option (SYS_CLK_MHZ=200 / PICO_USE_FASTEST_SUPPORTED_CLOCK) puts x2 = 400.000 (sondes) and x8 = 1600.000 (GLONASS G1). (2) clk_usb/clk_adc at 48 MHz adds 144/432 and 1584 MHz. (3) The Pico's RT6150 runs in PFM by default, which gives a load-dependent irregular comb in LF/MF/HF; the datasheet says driving GPIO23 high forces PWM and 'reduces the output ripple considerably'.
    - **Verdict:** new_risk
    - **Action:** Firmware rules: keep clk_sys at 125 MHz and never enable 200 MHz. Drive GP23 high in the HF/LF Quiet profiles, or always if the Pico's current budget allows. Put the Pico states (PFM vs PWM, clock) into the A/B matrix.
    - **Impact:** Avoids self-made lines on sondes and GLONASS, and LF/HF hash from the HMI MCU that sits right beside the HF+.
    - **Sources:**
      - https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
      - https://github.com/raspberrypi/pico-sdk/releases
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/disp_hmi_r2/calc/other.py
  22.
    - **Claim in stack:** Encoders, keys, knobs: Bourns PEC11R-4215F-S0024 x3, C&K KSC641J IP67 x10, Adafruit 2055 x2 = $17.75 (DigiKey lines unverified)
    - **Finding:** PEC11R-4215F-S0024-ND: $2.95, 13,117 in stock, Active, 24 PPR with detents, push switch, 6 mm flatted shaft, 30k cycles, no IP rating. KSC641J LFS: $0.82 (qty 1) or $0.70 (qty 10), 30,086 in stock, Active, IP67, 6.2x6.2 mm SMT, 340 gf, 7.7 mm hard actuator. C&K is now part of Littelfuse. Adafruit 2055 'Scrubber Knob - 35mm': $0.95, in stock. Total 3x2.95 + 10x0.70 + 2x0.95 = $17.75, which matches. The PEC11R is not sealed, and the KSC641J is SMT only, so it needs a keypad PCB with 12 mm caps or a silicone boot.
    - **Verdict:** confirmed
    - **Action:** Mark the line as verified. For rain and dust, add a panel O-ring or boot over each encoder. Grayhill 62SG with its optional shaft/panel seal is an alternative (datasheet not read).
    - **Impact:** Price confirmed; sealing is a mechanical task.
    - **Sources:**
      - https://www.digikey.com/en/products/result?keywords=PEC11R-4215F-S0024
      - https://www.digikey.com/en/products/detail/c-k/KSC641J-LFS/1003852
      - https://www.ckswitches.com/media/1972/ksc6.pdf
      - https://www.adafruit.com/product/2055
      - https://www.mouser.lt/datasheet/3/1072/1/62sg_datasheet.pdf
  23.
    - **Claim in stack:** Rule: receive-only on air (STACK checks Wi-Fi/BT rfkill and a quiet 2.4 GHz band)
    - **Finding:** The only documented Wisecoco USB-touch bridge reports itself as 'wch.cn CH57x'. WCH CH57x parts (CH573/CH571 BLE, CH572 BLE 5.0, CH570 2.4 GHz) all contain 2.4 GHz radios. Touch firmware is very unlikely to transmit, but nothing can rfkill that chip.
    - **Verdict:** new_risk
    - **Action:** Add an acceptance test: with the display powered and touch active, listen at 2402-2480 MHz (tinySA/RTL-B near the panel board) for BLE advertising. Reject the board if anything is heard.
    - **Impact:** Keeps the receive-only rule verifiable for a hidden radio SoC.
    - **Sources:**
      - https://forums.raspberrypi.com/viewtopic.php?t=368455
      - https://www.radioelementy.ru/upload/iblock/152/9ou2vfv7dygvpbnvxteb4i5eanrwdasi.pdf
      - https://www.cnx-software.com/?p=147052
  24.
    - **Claim in stack:** If Wisecoco touch is bare I2C only: budget an I2C-to-USB-HID bridge or use the header-I2C goodix/edt-ft5x06 fallback (display_market)
    - **Finding:** The Pico itself could host the touch IC. I2C0 already runs at 3.3 V with VEML7700 (0x10) and PCA9555 (0x20); common touch addresses are 0x14/0x5D (Goodix) and 0x38 (FocalTech). GP22 and one freed pin can serve INT and RST. Touches would travel in the existing UART7 frame protocol to labinput, which injects them through uinput. That avoids a second USB device and its VBUS question, and avoids a Q6A DT overlay. It does not apply if the touch is in-cell TDDI that needs host firmware.
    - **Verdict:** new_option
    - **Action:** Keep it as plan B for an I2C-only answer from Wisecoco, once the touch IC and address are known.
    - **Impact:** Saves a bridge board and removes the touch VBUS and back-power path.
    - **Sources:**
      - https://www.vishay.com/docs/84286/veml7700.pdf
      - https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
  25.
    - **Claim in stack:** Above FHD only as a Midas MDT0700F1IHHC bring-up project (1200x1920, $364.62 = EUR 324.37 ex VAT, 12 weeks) via an HDMI-to-MIPI bridge; all other above-FHD kits are 287-706 nit
    - **Finding:** Farnell 4248109 is still listed at EUR 324.37 (IE) / GBP 272.58 (UK) ex VAT, 12-week lead time; this was seen in search results only, because Farnell returned 503. Other above-FHD parts are still dim: Midas MDT0700AC-USBC 1920x1200 at 410 cd/m2, Wisecoco 5.5in 2160x3840 at 450 cd/m2 ($159, which would also exceed the 2-lane DP pixel budget), Densitron DMT070F3NHCMU-1A 1920x1200 at 550 cd/m2. New: the Q6A has a native 4-lane MIPI DSI on a 39-pin 0.3 mm FPC, and Radxa supports its own 1200x1920 'Display 10 FHD' on it. So the Midas 1200x1920 MIPI panel could be driven directly over DSI, with no LT6911 bridge and no HDMI cable acting as a radiator. Radxa says third-party panels are 'not officially adapted', and the work needs a panel driver plus DT, an FPC adapter and an LED driver.
    - **Verdict:** new_option
    - **Action:** If the above-FHD project is ever started, evaluate native DSI before buying a bridge board: get the Midas init sequence and compare FPC pinouts.
    - **Impact:** May remove one bridge (about $30-60, estimate), the HDMI cable and their harmonics. Unverified.
    - **Sources:**
      - https://ie.farnell.com/midas-displays/mdt0700f1ihhc-mipi/lcd-tft-display-7-1200x1920p-mipi/dp/4248109
      - https://uk.rs-online.com/web/p/lcd-colour-displays/0428542
      - https://www.wisecocodisplay.com/product/5-5-inch-uhd-4k-2160x3840-high-brightness-lcd-display/
      - https://densitron.com/products/product/dmt070f3nbcmu-1a
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/mipi-dsi
  26.
    - **Claim in stack:** No 2026 candidate beats the Wisecoco on verified data (bonded, at least 1000 nit, HDMI, USB touch, 7in, at least FHD)
    - **Finding:** A search for 7in, 1920x1200, 1000 nit, bonded, HDMI, USB touch found nothing that qualifies. Xenarc 702GSH (1000 nit, bonded, USB PCAP) is 1024x600. Riverdi 7in HDMI is 1024x600 at 850 cd/m2. Newhaven NHD-7.0-HDMI-N-RSXN-CTU is 800x480 at 830 nit and non-stocked. The Newhaven 940-nit and Waveshare budget alternatives were not re-checked. Wisecoco-store eBay listings exist (ebay.de 176657492046) but could not be read (HTTP 403).
    - **Verdict:** confirmed
    - **Action:** No change of pick.
    - **Impact:** None.
    - **Sources:**
      - https://densitron.com/products/product/dmt070f3nbcmu-1a
      - https://focuscamera.com/products/xenarc-technologies-702gsh-monitors-recorders-production-monitors
      - https://riverdi.com/?p=111580
      - https://www.newhavendisplay.com/nhd70hdminrsxnctu-p-9552.html
  27.
    - **Claim in stack:** 2.6 group subtotal $221.39-244.44 (low end counts the 4D at $128.95)
    - **Finding:** The arithmetic is right: 128.95+17.77+15+10.12+17.75+5+9.90+11.90+5 = 221.39, and 132+17.77+25+10.12+17.75+10+9.90+11.90+10 = 244.44. The cable/ferrite line ($17.77) is built on a 45 cm cable and 2-3 mm ferrites, so it needs re-pricing (see the cable finding). The 4D fallback may add an OSD button board (price unknown). Shipping for Wisecoco and the 4D store is not included.
    - **Verdict:** corrected
    - **Action:** Re-price the cable line once the panel connector type is known; add the 4D button board as a fallback-only line.
    - **Impact:** About ±$5-10 (estimate).
    - **Sources:**
      - https://www.adafruit.com/product/2420
      - https://www.digikey.com/en/products/result?keywords=74271140
- **Current status oct 2026:** Wisecoco 7in 1920x1080 kit (SKU 4681): $132 (list $135); schema InStock; 0 reviews; page last modified 2026-09-17. It still says 'I2C Capacitive Touch' and lists -20 to 70 C operating. It still gives no input voltage, no bonding statement, no package contents and no USB-HID statement, so the D5 gate is still open.
  
  4D Systems: 4DHDMI datasheet Rev 1.0 (08/08/2025) is still the current public revision. DigiKey: $128.95, 13 in stock, 4-week lead time, status Active. 4D store: $141.85, available; product record updated 2026-10-02. No EOL or NRND notice found.
  
  Midas MDT0700F1IHHC-MIPI: Farnell EUR 324.37 / GBP 272.58 ex VAT, 12-week lead time (search-level only).
  
  Raspberry Pi Pico: from $4, in production to at least Jan 2036; The Pi Hut GBP 3.80, in stock. Pico datasheet build 03/07/2026. Pico SDK 2.3.1 (4 Sep, 2026 inferred); RP2040 default clock is still 125 MHz.
  
  Parts: PEC11R-4215F-S0024 Active, 13,117 at $2.95. KSC641J LFS Active, 30,086 at $0.82/$0.70. Adafruit 2055 and 2420 in stock. Wurth 74271140 $3.91. VEML7700 datasheet Rev 1.8 (28-Nov-2024).
  
  Software: Radxa 6.18.2-4-qcom config has DRM_MSM=y, DRM_LOAD_EDID_FIRMWARE=y, DRM_SIMPLE_BRIDGE=y, HID_MULTITOUCH=m. The newer 7.0.11-7 kernel switches DRM_MSM to a module and has the same RA620 HDMI-A/2-lane DP topology. Upstream msm DP trains at the sink's maximum link rate, with 0.5% SSC if the sink allows it. kanshi 1.5.1-1 is available in noble universe; labwc itself has no output-mode setting.
- **Notes:** Method: primary pages fetched or curled on 18 Oct 2026 (Wisecoco WooCommerce HTML and schema, 4D datasheet PDF and Shopify product JSON, DigiKey listings, Raspberry Pi pages and datasheet, Vishay datasheet, Wurth catalog, labwc man page, Ubuntu packages, upstream Linux source). Also used: local Radxa DTS and the packaged kernel configs already in the scratchpad. 10 WebSearch calls in total.
  
  Not reachable: the 4D product HTML page (429/404; its JSON was used instead), Farnell (503), RS and eBay (403), Grayhill 62SG (503), Newhaven (404), and the Goodix GT928 datasheet.
  
  All harmonic, line-rate and contrast numbers are models from my own scripts, not measurements. The band list was rebuilt from STACK sections 4 and 5.7, with a 0.5 MHz guard and harmonics up to 2.5 GHz. Scripts:
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/disp_hmi_r2/calc/scan.py
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/disp_hmi_r2/calc/win.py
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/disp_hmi_r2/calc/win4d.py
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/disp_hmi_r2/calc/other.py
  
  Downloads are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/disp_hmi_r2/dl/.
  
  Main fixes for stage 2:
  1. Mode pinning: use kanshi or wlr-randr, not a labwc config.
  2. HDMI cable and ferrite line: 2420 is 45 cm A-A; 74271140 is a NiZn part for 2-3 mm cable, not Mix-31/61; the 4D needs Mini-HDMI.
  3. HDMI pin 18: use a series diode, not a cut (HPD risk).
  4. The 4D fallback needs its own field-clock plan (only 81.5-82.0 MHz is clean for 1280x800) and an OSD button board for dimming.
  5. Extra D5 questions: backlight and dimming, bridge IC, scaler, crystal, burst lane rate, in-cell touch, cover lens, connector type, polariser axis, VBUS/HPD behaviour.
  6. RP2040 firmware rules: clk_sys stays at 125 MHz (never 200); GP23 high in Quiet profiles.
  7. A 2.4 GHz silence test for a CH57x touch bridge.
  
  Pixel clocks: 151.50 MHz and 127.90 MHz are both independently confirmed clean for the core bands. Policy compliance: nothing in this subsystem transmits on purpose. The only radio-capable part is the possible CH57x touch bridge, which the new test covers. No loops, dishes or military-aimed items are involved.

