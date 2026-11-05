# VGA8088

A source-built Windows 3.0 **real-mode** VGA driver for 8086/8088-class CPUs at **640 × 480, 16 colors**.

## A very serious institution

**The Chad Doebelin Center for Video Card Drivers Who Can’t Do 16-Bit Data Buses Good and Wanna Fetch Instructions Good Too.**

The driver has to be at least… three bytes smaller than this!

## Why this exists

Windows 3.0 can run in real mode on an 8088, but its VGA display-driver sources contain later-CPU instructions. Fixing visible instructions alone is insufficient: the BitBlt compiler also emits immediate-count rotates at runtime. The original 8088 additionally needs care when interrupts restart repeated string instructions with more than one prefix.

This project fixes and assembles the source, including the runtime code generator. It uses the retail Windows 3.0 DDK and matching Windows 3.0 SDK macros. The genuine VGA backend is retained: BIOS mode 12h, VGA DAC programming, 480-line cursor limits, 96-DPI metrics, VGA state/save-bitmap modules and RC-HIGH resources. This is not the EGA 640×350 build renamed as VGA.

The protected-mode-only 386 text renderer is omitted, and protected-mode physical enablement is explicitly rejected. **Use Windows real mode (`WIN /R`).**

![Actual Windows 3.0 running the source-built VGA driver](evidence/VGA88-source-built-working.png)

The screenshot is the actual emulated Windows display surface.

## Status

The candidate is 58,128 bytes, SHA-256:

`d4ca7b06604a1bb106cf63ea44333e9ae375696ada8d6ed1a559211d5326accc`

- All 39 linked object modules are rebuilt from source. The clean portable build reproduces the exact candidate binary.
- Static instruction audit covers 14,814 emitted rows, with no unsupported encoding.
- OMF/MAP closure accounts for every linked CODE/DATA contribution, including alignment. Import libraries add no executable or data bytes.
- All ten overridden REP-copy sites use 8088-safe loops. Forty-four ordinary single-prefix REP instructions remain; no multi-prefix REP is emitted.
- Seventy-four matching high-resolution resource records are rebuilt and roundtrip-checked.
- Windows 3.0 real-mode GUI tests complete with zero reported failures on DOSBox-X's `8086_prefetch` and 386 models. All eight complete four-plane captures match one another and the stock VGA driver on the 386 model, byte for byte.

**Emulator-tested, not physical-8088 hardware-qualified.** DOSBox-X's experimental 8086-prefetch model is not a true or cycle-accurate 8088. Physical interrupt restart behavior, boards/BIOS variants, timing and broader application coverage remain to be tested.

## Build

The source, resources, build/audit tools and [candidate binary](dist/VGA88.DRV) are supplied. Historical compiler executables and Windows installation files are not included.

Requirements:

- Python 3 and an existing DOSBox-X installation.
- MASM 5.10 (`MASM.EXE`).
- Microsoft Segmented-Executable Linker 5.01.17 (`LINK4.EXE`).
- `EXE2BIN.EXE` and Windows 3.0 DDK `SWINLIBC.LIB`.
- The same existing, nonempty emulator lease used by other emulator work on your machine. The script never creates/replaces it and refuses to run beside another live emulator.

The script finds the required toolchain files by name under the supplied directory and builds a fresh output tree. Compatible tools and source edits are supported without fixed checksum requirements. Compiler, linker and resource-packing errors stop the build.

```sh
python tools/build.py \
  --toolchain /path/to/historical-toolchain \
  --dosbox /path/to/dosbox-x \
  --lease /path/to/existing-shared-emulator.lock \
  --out /path/to/new-build-directory
```

The new directory contains `VGA88.DRV`, `VGA.RES`, full MASM listings, linker MAP and compiler logs. The compiler runs on an emulated 386 for speed; `.8086` guards constrain the emitted driver instructions. Runtime-generated instructions are handled separately by the source changes and validation.

`BUILD.BAT` also supports a period DOS setup with the prepared tree on drive R:, containing SRC, INC, RES, BIN and LIB. The Python script prepares that tree and packs the resources afterward. Existing audit scripts remain available separately under `tools/`.

## Try it

Use a disposable Windows 3.0 installation configured for standard VGA 640×480, 16 colors, with matching VGASYS.FON, VGAFIX.FON and VGAOEM.FON. Exit Windows completely, place VGA88.DRV in the SYSTEM directory, set `display.drv=VGA88.DRV` under `[boot]` in SYSTEM.INI and start `WIN /R`. This driver intentionally refuses protected-mode Windows.

## Validation and details

![Actual display during the GDI suite](evidence/VGA88-GDI-suite-running.png)

- [GUI source](tests/EGAQA.C)

Inspired by Tony814's VGAon8088 work.

## The Center

> Chad Doebelin's Video Card Drivers For Computers Who Can't Do 8-bit external data buses and want to Queue better too?

**The Chad Doebelin Center for Video Card Drivers Who Can’t Do 16-Bit Data Buses Good and Wanna Fetch Instructions Good Too.**

The driver has to be at least… three bytes smaller than this!
