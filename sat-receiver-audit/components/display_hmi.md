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

## Адверсаріальна перевірка (`verify`)

_Run `wf_d9388111-e66`_

- **Subsystem:** display_hmi (stage 3, adversarial verification): Wisecoco 7in FHD 2000-nit kit (gated) + 4D Systems 4DHDMI-70-1280-800-CT-EAR-1000 fallback, field EDID / pixel clock / harmonic scan, kanshi mode pinning, sun/thermal, glove touch, RP2040 Pico HMI (encoders, keys, VEML7700)
- **Verdict:** The subsystem holds up, with corrections. Things I re-checked against primary sources on 18 Oct 2026 and that stand: both field pixel clocks (151.50 / 127.90 MHz) for integer harmonics, the line rates, the EDID build rules, kanshi pinning with exact mHz strings, the 4D fallback data (now datasheet Rev 1.5), the Pico clock rules and the HMI parts and prices.
  
  Three things change the plan:
  1. Wisecoco's own listing images, which stages 1 and 2 never read, answer part of the D5 gate. The board has a "Type-C(5V 2A) Touch+Power" port, a "USB TP" header, a "DC(5-24V)" barrel, full-size HDMI, a keypad header, its own backlight boost and audio outputs, and is "landscape by default". USB touch is therefore designed in, the 5 V converter is not needed, and the "native portrait" risk is mostly void. However, the board is very likely a scaler with its own backlight driver. That means: the Pico GP17 "analog dimming" has no defined point to connect to, and the panel-side clocks, the LED driver and the audio amplifier are outside the EDID plan.
  2. A model of the HDMI 1.4 TMDS encoding (no scrambling) shows that flat colours produce content-dependent combs at f_pix/P, with P = 3, 5, 7 or 9. These land in GNSS, H1, HRPT and sonde bands for every possible pixel clock. A harmonic-clean pixel clock is necessary but not sufficient. A cheap UI palette rule (only TMDS period-1 byte values in large fills) plus flat-field A/B tests cover it.
  3. The vendor's "2000+ cd/m2" proof photo is a lux-meter reading (2424 lx). For a Lambertian screen, that only shows at least about 770 cd/m2 (model), so the 1800-nit acceptance test is load-bearing.
  
  My web-search budget was already used up by other agents, so this round used WebFetch and curl on primary pages and source tarballs only. Farnell (Midas) returned 503 and is not re-verified.
- **Confirmed:**
  - Wisecoco SKU 4681: schema price 132.00 USD (list 135.00), InStock, dateModified 2026-09-17T01:11:25Z, 0 reviews. Text: 'I2C Capacitive Touch'; table 'Interface Type I2C', 'TFT Active Area 86.832X154.368mm', LTPS, 2000cd/m2, 1000:1, operating -20~70 and storage -30~80. Summary: 155.82x87.83 mm active, 164.22x97.98 mm outline, 'MIPI (4 data lanes)'. https://www.wisecocodisplay.com/product/7-inch-1920x1080-high-brightness-2500nits-lcd-panel-with-hdmi-in-board-ips-mipi-interface-tft-lcd-screen/
  - Youritech ET070FH01-HT (likely twin glass): active 154.368x86.832 mm, outline 164.19x97.87 mm, 2000 cd/m2 typ, -20~70 / -30~80 C, 'in-cell touch' plus a marketing line on 'glove compatibility', optical bonding only as customisation. https://www.youritech.com/products/7-inch-tft-lcd-display-1920x1080-mipi-2000nits-high-brightness-lcd-display-with-in-cell-touch-for-healthcare-medical-display-solution.html
  - 4D datasheet is Rev 1.5 (10/10/2026). Rev 1.2 (03/03/2026) 'Updated models which support DDC'. The 1280-800 series lists 'Supports DDC', Mini-HDMI 19-pin HDMI 1.4, 12 V 5.5 mm barrel, and an OSD button-board port that is 'Not included as standard'. The 7in CT-EAR-1000 entry: 1000 cd/m2 'Adjustable via OSD Menu', 'Optical Bonded to LCD', 800:1, 1300 mA at 5 V USB / 540 mA at 12 V barrel, -20..+70 / -30..+80 C, no cover-glass treatment as standard, a USB-C port for both power and touch that 'parallels the power', and a 50 cm HDMI cable in the box. No touch IC is named. https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_5.pdf
  - 4D prices: DigiKey 1613-4DHDMI-70-1280-800-CT-EAR-1000-ND $128.95, 13 in stock, 4-week lead time, Active; its short description wrongly reads '9.0in ... 500CD/M2'. 4D store $141.85, with the shop currency checked as USD (Shopify meta.json), available, record updated 2026-10-18.
  - Pixel clocks: my independent integer-harmonic scan (model; 14 core windows including HRPT/LRIT/AHRPT 1686-1711; guard 0.5 MHz; up to 2.5 GHz). Clean windows are 123.89-128.04 and 148.13-153.22 MHz. 151.50 MHz has no core hit; its nearest is the fundamental, 5.5 MHz above 2 m. 127.90 MHz has no core hit; its nearest is 12x = 1534.8 MHz, 2.2 MHz below Inmarsat-C. A 0.5% downspread adds no hits. 148.5 x5 = 742.5 MHz and 128.70 x12 = 1544.4 MHz are confirmed, as is 151.5 x15 = 2272.5 MHz in the Lime S-band. Script: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dh3/calc/scan3.py
  - Line rates (model): 68.864 kHz sits 8.86 kHz from 60, 8.64 from 77.5, 8.82 from 4209.5 and 7.95 from NAVTEX 490 kHz. 58.136 kHz sits 1.86 kHz from 60 and 5.23 from 518 kHz.
  - 4D 1280x800 (model): 71.0 MHz hits H1 1420.0 (x20), 1562 (x22), 1704 (x24) and 213 (x3). The only core-clean window from 50 to 123 MHz is 81.51-82.02 MHz, e.g. 81.8 MHz with 1440x947 totals (59.985 Hz).
  - Kernel v6.18: _drm_edid_connector_add_modes adds detailed, CVT 3-byte, standard, established, CEA, alternate CEA and DisplayID modes, and inferred modes when DRM_EDID_FEATURE_CONTINUOUS_FREQ is set. drm_mode_vrefresh uses DIV_ROUND_CLOSEST, so @60 matches 59.986 Hz and @52 matches 51.677 Hz. drm_helper_probe_add_cmdline_mode only marks a matching mode USERDEF, and otherwise creates a new mode. https://raw.githubusercontent.com/torvalds/linux/v6.18/drivers/gpu/drm/drm_edid.c
  - msm DP v6.18: link rate = panel->link_info.rate (sink maximum); DP_SPREAD_AMP_0_5 and PHY SSC are set when drm_dp_max_downspread(dpcd). simple-bridge.c has 'radxa,ra620' with DRM_MODE_CONNECTOR_HDMIA. The local Radxa 6.18.2 DTS puts RA620 on QMP PHY DP lanes <0 1> (USB3 on lanes 2/3).
  - Held kernel config-6.18.2-4-qcom: DRM_MSM=y (EDID file must be in the initramfs), DRM_LOAD_EDID_FIRMWARE=y, DRM_SIMPLE_BRIDGE=y, HID_MULTITOUCH=m, HID_GENERIC=y, USB_HID=y, I2C_CHARDEV=y, DRM_DISPLAY_DP_AUX_CHARDEV=y, INPUT_UINPUT=m, TOUCHSCREEN_GOODIX=m, EDT_FT5X06=m.
  - kanshi 1.5.1 (noble orig tarball): match_refresh accepts |delta| < 50 mHz and picks the lowest delta; the refresh string is parsed as float x1000. wlroots 0.17.1 (libwlroots12t64, used by noble labwc 0.7.1): calculate_refresh_rate gives 59986 mHz for 151.5 MHz/2200x1148 and 51677 mHz for 127.9 MHz/2200x1125; custom modes go through generate_cvt_mode.
  - labwc NEWS: reuseOutputMode since 0.6.1; wlr-output-management and wlr-output-power-management long before 0.7.1; <touch mapToOutput> in 0.7.1; touch on SSD headerbar in 0.7.2 (#1550); touch mouse emulation in 0.8.2; autoEnableOutputs in 0.8.3. Issue #2615 (opened Mar 2025, still open): video=DP-1:...@60 plus reuseOutputMode was ignored, and the maintainer suggested kanshi.
  - Radxa forum: 7.0.11-4-qcom HDMI regression (#31304, from Aug 2026; 'HDMI works now after the latest kernel updates' on 9 Sep). 'Radxa Team' member chenchongbiao (1 Sep): 7.0 needs clk_ignore_unused (#31288). Community Ubuntu 26.04.1 v1.3.0 on 7.2.9 with Armbian patches (#31574, 7 Oct). HDMI and SPI12 display cannot both be active, with no plans to support it (#30490, Radxa Team, Mar 2026). 8HD shows backlight only, with an AD001 vs AD002 overlay mismatch (#30822).
  - RPi forum t=368455 (Apr 2024): a Wisecoco 7in kit, cabled to its '5V + Touch' connector, enumerated as 1a86:e5e3 'wch.cn CH57x', first under hid-generic and then hid-multitouch. The unit later failed on a Pi 3 too (n=1).
  - Radxa ships qcs6490-radxa-dragon-q6a-uart7.dtso ('pin 32(tx), 29(rx)', qcom,enable-gsi-dma, disables spi7/i2c7). The application-UART TX report (#31422) is a single user with unclear wiring and no resolution.
  - Raspberry Pi Pico: 'available from $4'; 'Pico 1 series will remain in production until at least January 2036'. Datasheet build 03/07/2026: GPIO23 drives the RT6150 PS pin (PFM by default; PWM 'reduces the output ripple considerably'), GPIO24 is VBUS sense, VSYS is 1.8-5.5 V. pico-sdk master: SYS_CLK_HZ 125 MHz default, PICO_USE_FASTEST_SUPPORTED_CLOCK=0; PLL_SYS VCO 1500 MHz /6/2; PLL_USB VCO 1200 MHz /5/5 = 48 MHz; the 200 MHz option uses a 1200 MHz VCO /6/1. SDK 2.3.1 (4 Sep) and 2.3.0 (3 Jul) are the latest releases.
  - Pico pin map in STACK 5.2 is function-valid: UART0 GP0/1, UART1 GP8/9, I2C0 GP4/5, encoder pairs GP2/3 and GP6/7 consecutive for quadrature_encoder.pio (which must load at offset 0, '.origin 0'), ADC GP26-28. 23 GPIO plus 3 ADC are used; only GP22 is free.
  - VEML7700 datasheet Rev 1.8 (28-Nov-2024): 0 to about 140 klx, 0.0042 lx/step at gain x2 / IT 800 ms, fixed 7-bit address 0x10 (8-bit 0x20), so no clash with the PCA9555 at 7-bit 0x20. The Adafruit Arduino library still has MAX_RES 0.0036; the CircuitPython driver uses 0.0042.
  - Bourns PEC11R datasheet REV D04/26: IP40, contact bounce 2.0 ms max at 15 RPM, 60 RPM max, 30k cycles, suggested 10k/10k/0.01 uF filter, 'use within 6 months'. DigiKey PEC11R-4215F-S0024-ND: $2.95, 13,117 in stock, Active, 24 PPR, detents, switch. KSC641J LFS: $0.82 for 1 / $0.70 for 10, 30,086 in stock, Active, IP67, 340 gf, 7.70 mm actuator, SMT. Adafruit 2055 knob $0.95. Total $17.75 is correct.
  - Adafruit: 2420 is 'Slim HDMI Cable - 450mm' at $9.95, so it cannot be the 10-15 cm run. 3548 straight HDMI plug $6.50; 3550 right-angle HDMI plug $6.50; 3552 straight Mini-HDMI plug $6.50; 3560 10 cm ribbon $1.50; 3561 20 cm ribbon $1.95; 5997 CH334F $4.95. Wurth 74271140 is WE-STAR-TEC for 2-3 mm cable, 92/178 ohm at 25/100 MHz, NiZn '4 W 620', $3.91 at DigiKey; it is not a Mix-31/61 part.
  - Sun contrast model (model): 2000 cd/m2 and 1000:1 at 100 klx give 6.2:1 at about 1.2% reflectance (bonded + AR) and 1.5:1 at about 12% (air gap). At a sustained 1000 nit, bonded + AR gives about 3.6:1. Bonded without AR (about 4.5%) gives only about 1.7:1, so the AR film is required on either panel.
  - Design principle stands: every critical action must work with keys and encoders. Neither vendor documents glove touch.
- **Corrections:**
  1.
    - **Claim in stack:** D5/C5/2.6: Wisecoco touch must be USB-HID (gate); stage 1: 'USB is not mentioned anywhere' on the listing
    - **Finding:** The listing's own images label the driver board (96.2x82 mm, sticker 2023-05-10): 'Type-C(5V 2A) Touch+Power', 'Type-C(5V 2A) Power', a 4-pin 'USB TP' header, an 'I2C for touch' (TP) header, 'DC(5-24V)', 'hdmi-Compatible'/'HDMI IN' (full-size A), 'keypad' (KEY), 'Backlight', 'Speaker', 'Earphone'. The text panel still says 'Capacitive touch - With I2C interface'. So the touch panel is I2C into the board, and the board exposes it over USB. HID class, VID:PID and behaviour without VBUS are still unconfirmed.
    - **Verdict:** corrected
    - **Action:** Keep the gate, reworded: 'confirm USB-HID VID:PID, and that touch enumerates from the USB TP header with VBUS open'. Wire D+, D- and GND from the USB TP header (or a cut Type-C lead) to FE1.1s P2. Never connect hub VBUS to the board.
    - **Impact:** The gate is likely to pass; the remaining risk is enumeration without VBUS.
    - **Sources:**
      - https://www.wisecocodisplay.com/wp-content/uploads/2025/05/7-inch-2000-nits-lcd-7.webp
      - https://www.wisecocodisplay.com/wp-content/uploads/2025/05/7-1.jpg
      - https://www.wisecocodisplay.com/wp-content/uploads/2025/05/7-inch-2000-nits-lcd-4.webp
      - https://forums.raspberrypi.com/viewtopic.php?t=368455
  2.
    - **Claim in stack:** D4/2.11/5.1: 'If the board is 5 V only, a separate Pololu D36V28F5 #2 ($23.95)'; D5 asks for input voltage
    - **Finding:** The listing image states DC 5-24 V on a barrel jack. The 4D also takes 12 V on a 5.5 mm barrel. DISP12 (SYS12 -> LC -> eFuse 1.5 A) can feed either panel directly.
    - **Verdict:** corrected
    - **Action:** Drop D36V28F5 #2 from the optional list. Remove 'input voltage' from D5, but still ask for the current at 12 V at 25/50/100% and the barrel size. Keep the 11.0 V stability test.
    - **Impact:** One fewer converter; $23.95 leaves the optional list.
    - **Sources:**
      - https://www.wisecocodisplay.com/wp-content/uploads/2025/05/7-inch-2000-nits-lcd-7.webp
      - https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_5.pdf
  3.
    - **Claim in stack:** D4 / Pico GP17: backlight dimming is analog/DC from the Pico (24.0 kHz only if PWM is unavoidable); NTC derating above 60 C to 50% and above 68 C to 20%
    - **Finding:** The Wisecoco board has its own LED boost (8R2 inductor, VLED/LED+/LED- 'Backlight' connector) and a KEY header, so brightness is set by the board's driver or OSD. GP17 has no defined point to connect to. The 4D is the same: OSD only, with an optional button board, and DDC per Rev 1.5. Without a working control path, the thermal derating cannot act. The thermal model already shows 71 C at 35 C ambient, 100%, in sun.
    - **Verdict:** new_risk
    - **Action:** Make the dimming path a D5 question and a bench item, in this priority: (1) DDC/CI via 'ddcutil detect' / 'setvcp 10' through the RA620 AUX; (2) KEY-header emulation from the Pico with open-drain lines (needs the pinout); (3) own constant-current LED driver on the Backlight connector, fed from DISP12, with true DC dimming (needs LED string Vf/If and the string count). Ask for the board's PWM dimming frequency.
    - **Impact:** Without it, the 60/68 C derating and VEML7700 auto-brightness do nothing on either panel.
    - **Sources:**
      - https://www.wisecocodisplay.com/wp-content/uploads/2025/05/7-1.jpg
      - https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_5.pdf
  4.
    - **Claim in stack:** C12/5.7.4: the field pixel clock (EDID) keeps display lines out of the core bands; ask Wisecoco for the DSI mode and lane rate
    - **Finding:** The board's keypad, OSD-capable layout, two heatsinked ICs and audio outputs point to a scaler-type board (inference from the photo; the chips cannot be read). In that case the panel-side DSI clock, the board crystal(s), the LED boost switching and a class-D speaker amplifier are all set by the board, not by the EDID. The EDID cleans only the RA620 -> board HDMI segment. Upside: scalers usually accept non-standard input timings, which eases the stage-2 'timing-picky LT6911' risk.
    - **Verdict:** new_risk
    - **Action:** Add to D5: scaler or bridge part number; pass-through or rescale; panel-side pixel clock and DSI lane rate; crystal frequencies; LED-driver switching frequency; whether the audio amp is present and can be disabled. A/B: board powered with HDMI unplugged vs plugged, so board-only lines are found and logged in the 5.7 table.
    - **Impact:** Lines from the board 1-2 cm behind the glass that no EDID choice can move.
    - **Sources:**
      - https://www.wisecocodisplay.com/wp-content/uploads/2025/05/7-1.jpg
  5.
    - **Claim in stack:** Stage 2: native orientation not settled; if portrait, every DTD and the LF line-rate analysis are void
    - **Finding:** Listing text: 'landscape orientation by default' and 'Landscape by Default - Pre-configured widescreen orientation'. The drawing labels 155.82 (H) x 87.83 (V) mm. Only the table's 86.832X154.368 is in portrait order. If the board is a scaler, any native-portrait glass would be rotated on the board side.
    - **Verdict:** corrected
    - **Action:** Reduce this to one D5 question: 'native panel DTD and the input timing range the board accepts'. Keep the vstretch fallback (native htotal, longer VFP).
    - **Impact:** The field DTDs stay 1920x1080 landscape.
    - **Sources:**
      - https://www.wisecocodisplay.com/product/7-inch-1920x1080-high-brightness-2500nits-lcd-panel-with-hdmi-in-board-ips-mipi-interface-tft-lcd-screen/
      - https://www.wisecocodisplay.com/wp-content/uploads/2025/05/7-inch-2000-nits-lcd-1.webp
  6.
    - **Claim in stack:** 2.6/D4: Wisecoco '2000+ cd/m2 typ'; acceptance at least 1800 nit on full white
    - **Finding:** The vendor's 'More than 2000+cd/m2' image shows a handheld lux meter reading 2424 (and 562 for the '500+' screen). Illuminance at contact with a Lambertian screen is E = pi x L, so 2424 lx means at least about 770 cd/m2 (model). The photo does not substantiate 2000 cd/m2.
    - **Verdict:** new_risk
    - **Action:** Keep the 1800-nit acceptance test and measure in cd/m2 (luminance meter). As a rough on-device check, place the VEML7700 flush on a full-white field, take L = E/pi (model, roughly ±25%), and reject below 1800 cd/m2 within 30 days.
    - **Impact:** Without a measurement the choice of the Wisecoco over the 4D (1000 nit) could be wrong.
    - **Sources:**
      - https://www.wisecocodisplay.com/wp-content/uploads/2025/05/7-inch-2000-nits-lcd-2.webp
  7.
    - **Claim in stack:** C12: 'video=HDMI-A-1:...@60 or @52, mode pinned in the labwc output config'; stage 2: kanshi with '@59.986Hz'/'@51.677Hz'; 'kanshi custom modes are a TODO'
    - **Finding:** kanshi 1.5.1 matches |delta| < 50 mHz. wlroots 0.17.1 reports 59986 and 51677 mHz. '@60Hz' would also match a 148.5 MHz mode (60000 mHz, delta 0) and prefer it, so only the exact mHz strings are safe. kanshi 1.5.1 does support 'mode --custom' (parser.c:325, set_custom_mode), but wlroots turns it into a CVT timing (generate_cvt_mode), so it must never be used. The kernel video= only affects fbcon: it marks DTD1 USERDEF, while wlroots uses the preferred DTD.
    - **Verdict:** corrected
    - **Action:** Ship kanshi profiles 'output HDMI-A-1 mode 1920x1080@59.986Hz' and '...@51.677Hz', started from labwc autostart. Never use '@60Hz', '@52Hz' or '--custom'. Keep video=HDMI-A-1:1920x1080@60 for the console only.
    - **Impact:** The 127.9 MHz profile applies reliably, and a stray 148.5 MHz mode can never be chosen.
    - **Sources:**
      - http://archive.ubuntu.com/ubuntu/pool/universe/k/kanshi/kanshi_1.5.1.orig.tar.gz
      - http://archive.ubuntu.com/ubuntu/pool/universe/w/wlroots/wlroots_0.17.1.orig.tar.gz
      - https://raw.githubusercontent.com/torvalds/linux/v6.18/drivers/gpu/drm/drm_probe_helper.c
  8.
    - **Claim in stack:** HDMI cable line: Adafruit 2420 (short shielded) + 2x Wurth 74271140, 10-15 cm, Mix-31/61; budget FPC kit 3548+3560 $14.50
    - **Finding:** The Wisecoco input is full-size HDMI (photo, about 14 mm wide connector), so the run is A-A. 2420 is 450 mm long. 74271140 fits only 2-3 mm cable. On the WE-STAR-TEC page, 74271112 fits 4.5-6 mm (175/316 ohm at 25/100 MHz) and 74271131 fits 6-7.5 mm (125/235 ohm); their prices are not verified. The FPC kit is 2x3548 + 3560 = $14.50 (3550 if a right angle is needed). For the 4D: 3552 + 3548 + 3560 = $14.50, and a 50 cm cable ships in the box.
    - **Verdict:** corrected
    - **Action:** Spec: 10-15 cm shielded A-A cable (part chosen at assembly to its outer diameter), plus a WE-STAR-TEC ferrite sized to that diameter. Or the FPC kit with a grounded copper-tape wrap. Move the 74271140 to the touch USB lead (2-3 mm).
    - **Impact:** Cable line is about $14.50-25 (estimate) instead of $17.77.
    - **Sources:**
      - https://www.adafruit.com/product/2420
      - https://www.adafruit.com/product/3548
      - https://www.adafruit.com/product/3550
      - https://www.adafruit.com/product/3552
      - https://www.adafruit.com/product/3560
      - https://www.we-online.com/en/components/products/WE-STAR-TEC
  9.
    - **Claim in stack:** HMI MCU: Raspberry Pi Pico x2, 10.12 (2 x GBP 3.80), 'not verified'
    - **Finding:** World list price is $4.00 ('available from $4'). The Pi Hut is GBP 3.80. Production is guaranteed to at least Jan 2036. It must be the plain Pico (SC0915); the Pico W/2 W carry a radio.
    - **Verdict:** corrected
    - **Action:** Line becomes $8.00 for 2 plus shipping, marked verified. Note 'Pico (no radio), not Pico W'.
    - **Impact:** -$2.12
    - **Sources:**
      - https://www.raspberrypi.com/products/raspberry-pi-pico/
      - https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
  10.
    - **Claim in stack:** Stage 2: Adafruit VEML7700 Arduino library 'reads about 16.7% low'
    - **Finding:** 0.0036/0.0042 = 0.857, so the library reads 14.3% low (the true value is 16.7% higher than reported).
    - **Verdict:** corrected
    - **Action:** Use our own driver with 0.0042 lx/ct, gain 1/8 and IT 25 ms above about 20 klx, i2c timeouts, 9-clock bus recovery, watchdog, and 100 ohm + TVS at the bezel.
    - **Impact:** Wording only.
    - **Sources:**
      - https://raw.githubusercontent.com/adafruit/Adafruit_VEML7700/master/Adafruit_VEML7700.h
      - https://www.vishay.com/docs/84286/veml7700.pdf
  11.
    - **Claim in stack:** Stage 2: Bourns RC filter 'removes detent jitter and miscounts'
    - **Finding:** Full quadrature decoding in the PIO is inherently tolerant of single-channel bounce, because a +1/-1 pair cancels. The datasheet's specifications assume the 10k/10k/0.01 uF filter. The filter is cheap insurance against EMI and ESD, not the primary fix.
    - **Verdict:** corrected
    - **Action:** Keep the filter ($0.10). Count 4 edges per detent (24 PPR / 24 detents). Run two state machines on one PIO, loaded at offset 0.
    - **Impact:** None on cost.
    - **Sources:**
      - https://www.bourns.com/docs/Product-Datasheets/PEC11R.pdf
      - https://raw.githubusercontent.com/raspberrypi/pico-examples/master/pio/quadrature_encoder/quadrature_encoder.pio
  12.
    - **Claim in stack:** Stage 2: labwc #3352 blank/unblank failure applies here (use wlopm plus kanshi stop/start)
    - **Finding:** The report is from an RPi 5 on RaspiOS with labwc 0.9.2 and libseat 'Permission denied' / session-timeout errors. It is still open; RPi reproduced it and a wlroots update helped. Its transfer to Q6A/msm/RA620 with labwc 0.7.1 is unproven.
    - **Verdict:** unverified
    - **Action:** Keep the 20x wlopm off/on cycle as a test. The kanshi stop/start pattern is the default; never use wlr-randr --off.
    - **Impact:** Low.
    - **Sources:**
      - https://github.com/labwc/labwc/issues/3352
  13.
    - **Claim in stack:** Stage 1: Pico GP23 high (forced PWM) in HF/LF Quiet profiles
    - **Finding:** The datasheet confirms that PWM 'reduces the output ripple considerably'. But forced PWM turns load-dependent PFM bursts into a fixed-frequency comb (the frequency is not given in the Pico datasheet), which may land on HF channels. No RF measurement exists.
    - **Verdict:** unverified
    - **Action:** Treat GP23 low/high as a measured A/B state only (HF+ at the RBR list plus a 0.1-30 MHz sweep), and choose per profile.
    - **Impact:** None until measured.
    - **Sources:**
      - https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
  14.
    - **Claim in stack:** Above-FHD: Midas MDT0700F1IHHC $364.62 = EUR 324.37, 12 weeks; stage 2 downgraded native DSI to research-only
    - **Finding:** Farnell returned 503 again and the search budget is exhausted, so price and lead time are not re-verified. The Radxa 8HD 'backlight only' threads (#30822: AD001 panel vs AD002 overlay, 6.18.2-3) support the downgrade.
    - **Verdict:** unverified
    - **Action:** Keep it as research-only and out of the totals. Re-check the Farnell price before any order.
    - **Impact:** None on the core BOM.
    - **Sources:**
      - https://forum.radxa.com/t/30822
      - https://ie.farnell.com/midas-displays/mdt0700f1ihhc-mipi/lcd-tft-display-7-1200x1920p-mipi/dp/4248109
  15.
    - **Claim in stack:** 2.6 subtotal $221.39-244.44
    - **Finding:** Arithmetic matches the lines as written, but: Pico -$2.12; the cable line is re-priced at about $14.50-25; the 4D OSD button board (fallback only) has no price; D36V28F5 #2 drops out of the optional list; shipping from Wisecoco and the 4D store is excluded.
    - **Verdict:** corrected
    - **Action:** Re-total after the cable and ferrite part is fixed. Add the '4D button board (price on request)' fallback line.
    - **Impact:** About ±$10 (estimate).
    - **Sources:**
      - https://www.raspberrypi.com/products/raspberry-pi-pico/
      - https://www.adafruit.com/product/3548
- **New risks:**
  - TMDS content combs (model, my encoder per the DVI 1.0/HDMI 1.4 algorithm): flat fills repeat every P characters, with P = 1 (100 of 256 byte values), 3, 5, 7 or 9. Black 0x00 has P = 9 and white 0xFF has P = 7, giving lines at k x f_pix/P. At 151.5 MHz: black -> 1565.50, 1582.33, 1599.17 (GNSS), 1700.17 (HRPT) and 404.0 (sondes); white -> 1579.93, 1601.57, 1536.64, 1688.14 and 1709.79. At 127.9 MHz: black -> 1421.11 (H1) and 1563.2, 1577.4, 1591.6, 1605.9. No pixel clock avoids them. The DP link is scrambled; HDMI 1.4 is not, so this affects the RA620 -> board cable. Mitigation: UI palette rule in which large flat fills use only period-1 bytes per channel (e.g. near-black 0x10/0x08, mid 0x84/0x88, near-white 0xEF/0xEE, red-night R 0xC8 with G/B 0x10), never 0x00 or 0xFF. This assumes RGB full range with no dithering in the msm DPU or RA620; check it on the bench. Scripts: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dh3/calc/tmds.py and scan3.py.
  - The Wisecoco board is probably a scaler with its own LED boost, crystal(s) and a class-D speaker amplifier. These lines and that hash are independent of the field EDID and sit about 1-2 cm behind the glass.
  - There is no software dimming path on either panel until DDC/CI through the RA620 (I2C 0x37 over AUX, untested), KEY or button-board emulation, or an own LED driver is proven. Without one, there is no thermal derating above 60/68 C.
  - The vendor's brightness proof is a lux reading (2424 lx, i.e. at least about 770 cd/m2 for a Lambertian screen; model). The 2000-nit claim is unsubstantiated until it is measured.
  - The 'Touch+Power' USB-C port probably ties the touch VBUS to the board's 5 V rail. If hub VBUS is connected, the board and LAB5/hub back-feed each other. If it is left open, the touch MCU may not attach. Only a bench test settles this.
  - A 2.4 GHz-capable touch bridge (WCH CH57x seen on another Wisecoco 7in kit) cannot be rfkilled. The receive-only rule needs the BLE-silence test.
  - If the measured msm pixel clock (from M/N rounding) lands above about 128.05 MHz, 12x enters the Inmarsat-C guard (only 0.11% headroom). In that case use 151.50 only.
  - The polariser axis is unknown. Polarised sunglasses could black out the screen in landscape.
  - An unpowered device left face-up in sun may exceed the 80 C storage rating of both panels (inference). Close the hood as a lid and add a label.
  - If the RA620 advertises only RBR, the 162.000 MHz link symbol clock falls between the AIS channels (low probability; check the link rate).
- **Refuted findings:**
  1.
    - **Finding:** Stage 1: 'USB is not mentioned anywhere' on the Wisecoco listing; the gate is fully unmet
    - **Why:** The listing's own product images label a 'Type-C(5V 2A) Touch+Power' port and a 'USB TP' header. Only the text says I2C, which describes the touch panel's interface into the board.
  2.
    - **Finding:** D5/stage 1: Wisecoco input voltage is unknown (5 V-only path may need D36V28F5 #2)
    - **Why:** The listing image labels 'DC(5-24V)' on a barrel jack.
  3.
    - **Finding:** Stage 2: the kit's native orientation is unsettled, and a portrait kit would void the DTDs and the LF analysis
    - **Why:** The listing states 'landscape orientation by default' / 'Landscape by Default', and the drawing gives 155.82 (H) x 87.83 (V) mm. Only the table lists the dimensions in portrait order.
  4.
    - **Finding:** Stage 2: kanshi 'custom modes are a TODO'
    - **Why:** kanshi 1.5.1 parses 'mode --custom' (parser.c:325) and calls zwlr_output_configuration_head_v1_set_custom_mode (main.c:290). The conclusion still holds, because wlroots 0.17.1 turns custom modes into CVT timings.
  5.
    - **Finding:** Stage 2: Adafruit VEML7700 library 'reads about 16.7% low'
    - **Why:** 0.0036/0.0042 means it reads 14.3% low; 16.7% is the inverse ratio.
  6.
    - **Finding:** Implicit in C12 and stage 1: a harmonic-clean pixel clock keeps the display out of the core bands
    - **Why:** Model: the TMDS data channels produce content-dependent combs at f_pix/P (P = 3-9) that hit GNSS, H1, HRPT and sondes at both 151.5 and 127.9 MHz. On a scaler board, the panel-side clocks are not set by the EDID at all.
- **Corrected spec:** The DISPLAY (primary, gated) is Wisecoco SKU 4681, '7 Inch 1920x1080 High Brightness 2500Nits LCD Panel with HDMI in Board': $132.00 (list $135.00, ex shipping), InStock, page modified 2026-09-17. Its data:
  - 6.97in LTPS IPS, 1920x1080, landscape by default.
  - Active area 154.368x86.832 mm (table) or 155.82x87.83 mm (drawing): measure it. Outline 164.22x97.98 mm.
  - Claimed 2000+ cd/m2 typ (unsubstantiated) and 1000:1. Rated -20..70 C operating, -30..80 C storage.
  - Driver board 96.2x82 mm: full-size HDMI IN, DC 5-24 V barrel, USB-C 'Touch+Power' 5V/2A, USB-C 'Power' 5V/2A; headers USB TP, TP (I2C), KEY, Backlight, Speaker, Earphone.
  - Pay by PayPal only after written answers to the D5 questions:
    1. USB-HID VID:PID, and whether touch enumerates from USB TP with VBUS open; touch IC, in-cell or CTP, glove mode.
    2. Optical bonding plus AR, and cover-lens thickness.
    3. Scaler or bridge part, pass-through or rescale, panel DSI clock and lane rate, crystal frequencies.
    4. EDID dump, and whether 2200x1148@151.50 and 2200x1125@127.90 are accepted with an RGB/DVI-only source.
    5. Backlight: LED string Vf/If, driver IC and switching frequency, dimming method (PWM frequency, KEY pinout, DDC/CI).
    6. Audio amp present, and can it be disabled.
    7. Polariser axis.
    8. Current at 12 V at 25/50/100%; barrel size; package contents.
  - No clear answer in about 7 days means switching to the fallback.
  - Acceptance within 30 days: at least 1800 cd/m2 measured on full white; at most 14 W at 100% and at most 7.5 W at 50% at 11.0 V; touch enumerates in 20/20 cold boots; 2.4 GHz silent.
  
  The FALLBACK is 4D Systems 4DHDMI-70-1280-800-CT-EAR-1000. Price: DigiKey 1613-4DHDMI-70-1280-800-CT-EAR-1000-ND at $128.95 (13 in stock, then 4 weeks; check the MPN on the order line), or $141.85 USD at the 4D store. Datasheet Rev 1.5 (10/10/2026):
  - 1000 cd/m2, 800:1, optically bonded CTP, no AR as standard.
  - 12 V 540 mA (barrel) or 5 V 1300 mA (USB).
  - Mini-HDMI 1.4. USB-C carries power and touch, with the power in parallel.
  - 'Supports DDC'. OSD button board on request.
  - 50 cm HDMI cable included. Touch IC not named.
  - Field clock if it passes timing through: about 81.8 MHz (window 81.51-82.02, e.g. 1440x947 at 59.985 Hz). Otherwise rely on shielding and A/B, watching H1 1420.0.
  
  POWER:
  - DISP12 runs SYS12 -> LC -> eFuse 1.5 A (EN = Pico GP16, off whenever the Q6A is off) -> DC barrel on either panel. D36V28F5 #2 is not used.
  - Touch USB: only D+/D-/GND go to FE1.1s P2 (Wurth 74271140 on that 2-3 mm lead). Hub VBUS is never connected to the panel board.
  - HDMI pin 18 goes through a series Schottky (anode on the Q6A side), never cut.
  
  CABLE: 10-15 cm shielded HDMI A-A (Wisecoco), with a Wurth WE-STAR-TEC ferrite sized to its outer diameter (74271112 for 4.5-6 mm, 74271131 for 6-7.5 mm). Budget alternative: Adafruit 3548x2 + 3560 ($14.50; 3550 for a right angle), or 3552+3548+3560 for the 4D, always with a grounded copper-tape wrap.
  
  FIELD EDID (edid/field.bin, inside the initramfs, loaded with drm.edid_firmware=HDMI-A-1:edid/field.bin):
  - EDID 1.4 base block only. No CTA extension. Established timings 0x00 0x00 0x00, all Standard Timings 0x01 0x01, no CVT 3-byte descriptor, continuous-frequency feature bit cleared.
  - DTD1 (preferred): 151.50 MHz, H 1920/88/44/148 (htotal 2200), V 1080/27/5/36 (vtotal 1148). That gives 68.864 kHz and 59.986 Hz (wlroots 59986 mHz).
  - DTD2: 127.90 MHz, htotal 2200, V 1080/4/5/36 (vtotal 1125). That gives 58.136 kHz and 51.677 Hz (51677 mHz).
  - Acceptance: modetest/kmsprint lists exactly these two 1920x1080 modes.
  - 148.5 MHz is for bring-up only; 128.70 MHz is banned.
  - If the measured pixel clock is above about 128.0 MHz, use 151.50 only.
  - If 2200-wide totals are rejected, use native-htotal DTDs with a stretched VFP at the same clocks.
  
  KERNEL AND COMPOSITOR:
  - Kernel cmdline: video=HDMI-A-1:1920x1080@60. This affects the console only; no 'e' flag as a safety net.
  - Path B (7.x) adds clk_ignore_unused. Hold linux-image-6.18.2-4-qcom.
  - labwc 0.7.1 autostart starts kanshi 1.5.1 with profile field60 'output HDMI-A-1 mode 1920x1080@59.986Hz' and field52 '...@51.677Hz'. Never '@60Hz', '@52Hz', '--custom' or wlr-randr custom modes.
  - rc.xml: <touch mapToOutput="HDMI-A-1"/>. Expert GUIs run fullscreen and undecorated via windowRules, with hand-back by key.
  - Blanking uses wlopm with kanshi stopped and restarted around it.
  
  UI PALETTE: large flat fills use only TMDS period-1 bytes per channel (e.g. 0x10/0x08 near-black, 0x84/0x88 mid, 0xEF/0xEE near-white, red-night 0xC8/0x10/0x10). Never 0x00 or 0xFF fills.
  
  SUN AND THERMAL:
  - Bonded glass plus AR film (required), IR film, light bezel, 30 mm hinged hood that closes as a lid, and a 'do not leave face-up in sun' label.
  - Sustained about 1000 nit at noon. NTC derating: above 60 C go to 50%, above 68 C go to 20%. It acts through the proven dimming path, in this order: DDC/CI 'ddcutil setvcp 10' -> Pico open-drain emulation of KEY/OSD -> own CC LED driver from DISP12 on the Backlight connector, with GP17 driving it.
  - Glove touch is a bonus only; every critical action works by keys and encoders.
  
  HMI:
  - Raspberry Pi Pico (RP2040, no radio) x2 (1 spare), $4.00 each ($8.00; The Pi Hut GBP 3.80), on LAB5 via VSYS. Pin map as in STACK 5.2.
  - Firmware rules: clk_sys 125 MHz (never SYS_CLK_MHZ=200 or PICO_USE_FASTEST_SUPPORTED_CLOCK). Option to stop clk_usb/PLL_USB (1200 MHz VCO) when UART7 works, with the ADC on XOSC; re-enable it only in the H1 USB-fallback build. GP23 (PFM/PWM) is chosen by A/B. TX pins stay high-Z until the Q6A 3.3 V is present. Hardware watchdog.
  - Encoders: Bourns PEC11R-4215F-S0024 x3 (2 fitted, 1 spare), $2.95 each, IP40 with a panel O-ring or boot, 10k/10k/10 nF filter per channel. quadrature_encoder.pio is loaded at offset 0, with two state machines on one PIO and 4 counts per detent.
  - Keys: C&K KSC641J LFS x10 ($0.70 at qty 10; IP67, 340 gf, SMT) on a keypad PCB with 12 mm caps.
  - Knobs: Adafruit 2055 x2 ($0.95).
  - Pico I2C0 at 3.3 V carries PCA9555 at 0x20 (6 keys + 2 encoder pushes, INT on GP10) and VEML7700 at 0x10 (Rev 1.8; 0.0042 lx/ct; gain 1/8 and IT 25 ms above about 20 klx; own driver; i2c timeouts; 9-clock recovery; 100 ohm + TVS at the bezel, mounted outside the hood).
  - Pico UART0 runs to Q6A UART7 (pins 32/29, Radxa overlay qcs6490-radxa-dragon-q6a-uart7.dtso), with the H1 USB-CDC fallback wired.
  - No SPI status display (HDMI and SPI12 conflict).
  
  BOM: Pico line $8.00; cable line re-priced at about $14.50-25; 4D button board 'price on request' (fallback only); D36V28F5 #2 removed from the optional list.
- **Bench tests:**
  - Touch enumeration, USB TP header with D+/D-/GND only (VBUS open): lsusb VID:PID, hid-multitouch binding and evtest in 20/20 cold boots. If it fails, try VBUS from the board's own 5 V side only, then retest. Check with the FNB58 that 0 V back-feeds into LAB5 and the Q6A in every power state.
  - BLE silence: with the panel board powered and touch active, run tinySA or RTL-B with an E-probe over 2400-2483.5 MHz, dwell on 2402/2426/2480 MHz for 5 min. Reject the board on any advertising burst.
  - HPD/EDID with the pin-18 Schottky: HPD high, card1-HDMI-A-1 'connected', EDID override applied in 20/20 cold boots and 20 wlopm off/on cycles (kanshi stop/start pattern).
  - Modes: modetest/kmsprint lists exactly two 1920x1080 modes. Read the actual pixel clock in /sys/kernel/debug/clk/clk_summary (DP pixel clock) for both profiles and check that 12 x f(127.9 profile) is below 1536.5 MHz. kanshi applies '@59.986Hz' and '@51.677Hz'.
  - DP link: with drm.debug=0x1ff, log the link rate, lane count and DOWNSPREAD (SSC). If the link is RBR, add 162.000 MHz to the known-lines table and to the AIS A/B. Measure the TMDS line at 151.5 MHz and its width with an E-probe at the cable (SSC smear about 0.76 MHz).
  - TMDS content test (model check): full-screen fills 0x000000, 0xFFFFFF, 0x101010 and 0xEFEFEF at 151.5 and 127.9 MHz. Record average GNSS C/N0 of the top 8 SVs, and RTL-B / E-probe spectra at the predicted lines (151.5 MHz black: 1565.50/1582.33/1599.17/1700.17/404.0 MHz; white: 1579.93/1601.57/1536.64/1688.14 MHz; 127.9 MHz black: 1421.11/1591.64 MHz). Adopt the palette rule if 0x10/0xEF are cleaner.
  - Board-only emissions: board powered with HDMI unplugged, then plugged; HF+ 0.1-30 MHz at RBW 1 Hz on the 5.7 LF list, and tinySA 1-1800 MHz. Identify the board crystal(s), panel DSI clock, LED-boost frequency and audio-amp switching. Add them to the 5.7 table.
  - Brightness and power: luminance on full white (meter; or VEML7700 flush, L = E/pi as a rough check). Reject below 1800 cd/m2. Input power at 25/50/100% at 11.0 and 12.0 V (limits 7.5 W at 50% and 14 W at 100%).
  - Dimming path: 'ddcutil detect' and 'ddcutil setvcp 10 50' through the RA620 AUX (I2C 0x37), on Wisecoco and on the 4D. If that fails, Pico open-drain KEY/OSD emulation. If that fails, an own CC driver on the Backlight connector. Then a 45-min noon-sun run with the hood: NTC derating reaches 50% at 60 C and 20% at 68 C, and the glass stays at or below 65 C.
  - Polarised sunglasses at 0 and 90 deg in landscape. Touch through the AR film, bare-hand and gloved; the full menu walk-through by keys and encoders alone (CI acceptance).
  - Pico A/B: GP23 low vs high, clk_usb on vs off, and 125 MHz only. Measure the HF+ floor and lines at 144/432/1584/1704 MHz with the HMI board in its final position.
  - UART7: loopback both directions at 115200 with the shipped overlay, and check the UEFI QUPV3 SE7 mode. If TX is dead, try FIFO mode (no qcom,enable-gsi-dma) or fall back to H1 USB-CDC.
  - Encoders: 60 RPM spin and gloved detent stepping, 1000 detents with 0 miscounts, with and without the RC filter. VEML7700 in direct sun (about 100 klx) not saturated at gain 1/8 / IT 25 ms. SDA shorted for 1 s: the keys still work after bus recovery.
- **Confidence:** medium

