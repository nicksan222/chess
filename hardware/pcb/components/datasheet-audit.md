# Datasheet availability audit

Checked on 2026-10-06 from the development container.

**All 49 approved purchasing products have URLs: 33 unique URLs passed; zero failed; zero missing.**
This includes 29 PCB definitions, 12 off-board products and eight wire spools.
Availability does not establish part identity, revision parity or physical correctness.

| Components | Document |
|---|---|
| FUSE_2A | [document](https://atta.szlcsc.com/upload/public/pdf/source/20171109/C48467_15102201734031103760.pdf) |
| OLED_MODULE | [document](https://cdn.shopify.com/s/files/1/1509/1638/files/0_96_Zoll_Display_Datenblatt_AZ-Delivery_Vertriebs_GmbH_241c4223-c03f-4530-a8c0-f9ef2575872f.pdf?v=1622442722) |
| POWER_SWITCH | [document](https://configured-product-images.s3.amazonaws.com/2D/specs/RA11131100.pdf) |
| TEST_POINT | [document](https://content.harwin.com/asset/e4e6a5e1-de35-4a2b-8b49-ff06562cba9d/DRG-02202-Technical-Drawing-Datasheet-S1751R-pdf.pdf) |
| PI_ZERO_2_W | [document](https://datasheets.raspberrypi.com/rpizero2/raspberry-pi-zero-2-w-product-brief.pdf) |
| BARREL_JACK | [document](https://docs.rs-online.com/33bc/0900766b8141ad6e.pdf) |
| TVS_12V0 | [document](https://docs.rs-online.com/72ea/0900766b814f6468.pdf) |
| MICRO_SD | [document](https://documents.sandisk.com/content/dam/asset-library/en_us/assets/public/sandisk/product/memory-cards/high-endurance-uhs-i-microsd/data-sheet-high-endurance-uhs-i-microsd.pdf) |
| ROCKER_RECEPTACLE | [document](https://media.distrelec.com/Web/Downloads/_t/ds/2-520275-2_eng_tds.pdf) |
| OLED_HARNESS_WIRE_BLACK, OLED_HARNESS_WIRE_BLUE, OLED_HARNESS_WIRE_RED, OLED_HARNESS_WIRE_YELLOW | [document](https://www.alphawire.com/disteAPI/SpecPDF/DownloadProductSpecPdf?productPartNumber=2842%2F7) |
| POWER_HARNESS_WIRE_BLACK, POWER_HARNESS_WIRE_ORANGE, POWER_HARNESS_WIRE_RED, POWER_HARNESS_WIRE_WHITE | [document](https://www.alphawire.com/disteAPI/SpecPDF/DownloadProductSpecPdf?productPartNumber=3055) |
| BUTTON | [document](https://www.e-switch.com/wp-content/uploads/2022/06/TL1105.pdf) |
| LED_SWITCH_DRIVER | [document](https://www.farnell.com/datasheets/1596366.pdf) |
| OLED_HARNESS_CONTACT, OLED_HARNESS_HOUSING, OLED_HEADER | [document](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf) |
| POWER_HARNESS_CONTACT, POWER_HARNESS_HOUSING, POWER_HEADER | [document](https://www.jst-mfg.com/product/pdf/eng/eVH.pdf) |
| POWER_SUPPLY | [document](https://www.meanwell.com/Upload/PDF/GST18A/GST18A-SPEC.PDF) |
| SK9822 | [document](https://www.rose-lighting.com/wp-content/uploads/sites/53/2020/05/SK9822-A-REV.01-EN-5050-RGB-27K-HZ-PWM-30M-bps-speed.pdf) |
| CAP_560U | [document](https://www.rubycon.co.jp/wp-content/uploads/catalog-aluminum/ZLJ.pdf) |
| PI_MALE_HEADER | [document](https://www.sullinscorp.com/catalogs/77_PAGE108-109_.100_MALE_HDR.pdf) |
| PI_ZERO_HEADER | [document](https://www.sullinscorp.com/pdfs/catalog.pdf) |
| HALL_SENSOR | [document](https://www.ti.com/lit/ds/symlink/drv5032.pdf) |
| AHCT125 | [document](https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf) |
| LED_ENABLE_GATE | [document](https://www.ti.com/lit/ds/symlink/sn74lvc1g97.pdf) |
| TCA9554 | [document](https://www.ti.com/lit/ds/symlink/tca9554.pdf) |
| EFUSE | [document](https://www.ti.com/lit/ds/symlink/tps25947.pdf) |
| LED_SWITCH | [document](https://www.vishay.com/docs/70094/si4403ddy.pdf) |
| RES_100K, RES_10K, RES_1K, RES_1K65, RES_261K, RES_56 | [document](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L) |
| RES_169K_PRECISION, RES_604K_PRECISION | [document](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RT_1-TO-0-01_ROHS_L) |
| CAP_1U | [document](https://www.yageogroup.com/download/specsheet/CC0603KRX7R8BB105) |
| CAP_1N | [document](https://www.yageogroup.com/download/specsheet/CC0603KRX7R9BB102) |
| CAP_10N | [document](https://www.yageogroup.com/download/specsheet/CC0603KRX7R9BB103) |
| CAP_100N | [document](https://www.yageogroup.com/download/specsheet/CC0603KRX7R9BB104) |
| CAP_10U | [document](https://www.yageogroup.com/download/specsheet/CC0805KKX5R6BB106) |

Manufacturer-authored documents are preferred. The fuse, TVS, MOSFET, barrel
jack and FASTON receptacle use distributor-hosted copies because the original
vendor endpoints block automated access or are unavailable. The accessible onsemi
copy is Rev. 6 and the TVS copy is dated 2016; existing engineering notes reference
newer revisions. Link availability does not resolve that revision review.

The approved supply was corrected, with user authorization, to GST18A05-P1J
(5 V, 3 A). Its documented voltage, ripple and cord corners now feed SPICE; the
board operating budget and fuse remain 2 A.

The OLED PDF describes 28x33 mm while the catalog records 27x27 mm; resolve
the module revision before changing geometry. E-Switch lists RA11131100 as
obsolete; its exact drawing remains linked, and purchasing needs a replacement
review before ordering. Capacitor lands still use the documented Murata land
assumption; adding exact Yageo product URLs does not close that assumption.

Re-run `just --justfile hardware/pcb/justfile datasheets`. The automatic gate
in [`harness/checks`](../harness/checks/README.md) rejects missing and failed URLs.
