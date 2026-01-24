wolfTPM Support For Das U-Boot
==============================

wolfTPM provides experimental support for U-Boot with the following key features:

- Utilizes SOFT SPI driver in U-Boot for TPM communication
- Implements TPM 2.0 driver functionality through its internal TIS layer
- Provides native API access to all TPM 2.0 commands
- Includes wrapper API for common TPM 2.0 operations
- Supports two integration paths:
  - ``__linux__``: Uses existing tpm interface via tpm2_linux.c
  - ``__UBOOT__``: Direct SPI communication through tpm_io_uboot.c

wolfTPM U-Boot Commands
----------------------

The following commands are available through the ``wolftpm`` interface:

Basic Commands
~~~~~~~~~~~~~~

- ``help`` - Show help text
- ``device [num device]`` - Show all devices or set the specified device
- ``info`` - Show information about the TPM
- ``state`` - Show internal state from the TPM (if available)
- ``autostart`` - Initialize the TPM, perform a Startup(clear) and run a full selftest sequence
- ``init`` - Initialize the software stack (must be first command)
- ``startup <mode> [<op>]`` - Issue a TPM2_Startup command
  - ``<mode>``: TPM2_SU_CLEAR (reset state) or TPM2_SU_STATE (preserved state)
  - ``[<op>]``: optional shutdown with "off"
- ``self_test <type>`` - Test TPM capabilities
  - ``<type>``: "full" (all tests) or "continue" (untested tests only)

PCR Operations
~~~~~~~~~~~~~~

- ``pcr_extend <pcr> <digest_addr> [<digest_algo>]`` - Extend PCR with digest
- ``pcr_read <pcr> <digest_addr> [<digest_algo>]`` - Read PCR to memory
- ``pcr_allocate <algorithm> <on/off> [<password>]`` - Reconfig PCR bank algorithm
- ``pcr_setauthpolicy | pcr_setauthvalue <pcr> <key> [<password>]`` - Change PCR access key
- ``pcr_print`` - Print current PCR state

Security Management
~~~~~~~~~~~~~~~~~~~

- ``clear <hierarchy>`` - Issue TPM2_Clear command
  - ``<hierarchy>``: TPM2_RH_LOCKOUT or TPM2_RH_PLATFORM
- ``change_auth <hierarchy> <new_pw> [<old_pw>]`` - Change hierarchy password
  - ``<hierarchy>``: TPM2_RH_LOCKOUT, TPM2_RH_ENDORSEMENT, TPM2_RH_OWNER, or TPM2_RH_PLATFORM
- ``dam_reset [<password>]`` - Reset internal error counter
- ``dam_parameters <max_tries> <recovery_time> <lockout_recovery> [<password>]`` - Set DAM parameters
- ``caps`` - Show TPM capabilities and info

Firmware Management
~~~~~~~~~~~~~~~~~~~

- ``firmware_update <manifest_addr> <manifest_sz> <firmware_addr> <firmware_sz>`` - Update TPM firmware
- ``firmware_cancel`` - Cancel TPM firmware update

Infineon TPM Firmware Update Guide
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**WARNING: Firmware updates are risky. A failed update can brick your TPM.
Only proceed if you have a valid reason to update (security patches, new features)
and understand the risks.**

The firmware update commands are for Infineon SLB9672/SLB9673 TPMs only. The process
requires extracting manifest and firmware data from Infineon's combined ``.BIN`` file.

**Prerequisites:**

- Infineon firmware file (e.g., ``TPM20_16.13.17733.0_R1.BIN``)
- wolfTPM's ``ifx_fw_extract`` tool (in ``lib/wolftpm/examples/firmware/``)
- Your TPM's KeyGroupId (shown by ``wolftpm caps`` command)

**Step 1: Get your TPM's KeyGroupId**

Run ``wolftpm caps`` to find your TPM's KeyGroupId::

    U-Boot> wolftpm caps
    Mfg IFX (1), Vendor SLB9672, Fw 16.13 (0x4545), FIPS 140-2 1, CC-EAL4 1
    Operational mode: Normal TPM operational mode (0x0)
    KeyGroupId 0x5, FwCounter 1255 (255 same)
    ...

In this example, KeyGroupId is ``0x5``.

**Step 2: Build the extraction tool (on host machine)**

::

    cd lib/wolftpm/examples/firmware
    gcc -o ifx_fw_extract ifx_fw_extract.c

**Step 3: List available key groups in firmware file**

::

    ./ifx_fw_extract TPM20_16.13.17733.0_R1.BIN
    Found group 00000005

Verify your TPM's KeyGroupId matches one in the firmware file.

**Step 4: Extract manifest and firmware data**

Use your KeyGroupId (0x5 in this example)::

    ./ifx_fw_extract TPM20_16.13.17733.0_R1.BIN 0x5 manifest.bin firmware.bin
    Found group 00000005
    Chosen group found: 00000005
    Manifest size is 3229
    Data size is 925539
    Wrote 3229 bytes to manifest.bin
    Wrote 925539 bytes to firmware.bin

**Step 5: Copy files to SD card**

Copy ``manifest.bin`` and ``firmware.bin`` to your boot partition (FAT)::

    cp manifest.bin firmware.bin /Volumes/bootfs/   # macOS
    cp manifest.bin firmware.bin /boot/firmware/     # Linux

**Step 6: Load files into memory**

In U-Boot, load the files from SD card into RAM::

    U-Boot> fatload mmc 0:1 0x10000000 manifest.bin
    3229 bytes read in 32 ms (97.7 KiB/s)

    U-Boot> fatload mmc 0:1 0x10100000 firmware.bin
    925539 bytes read in 86 ms (10.3 MiB/s)

**Step 7: Perform firmware update (CAUTION!)**

Convert file sizes to hex:

- manifest.bin: 3229 bytes = 0xC9D
- firmware.bin: 925539 bytes = 0xE1F63

Run the firmware update::

    U-Boot> wolftpm firmware_update 0x10000000 0xC9D 0x10100000 0xE1F63
    TPM2 Firmware Update
    Infineon Firmware Update Tool
        Manifest Address: 0x10000000 (size: 3229)
        Firmware Address: 0x10100000 (size: 925539)
    tpm2 init: rc = 0 (Success)
    Mfg IFX (1), Vendor SLB9672, Fw 16.13 (0x4545)
    Operational mode: Normal TPM operational mode (0x0)
    KeyGroupId 0x5, FwCounter 1255 (255 same)
    Firmware Update (normal mode):
    Mfg IFX (1), Vendor SLB9672, Fw 16.13 (0x4545)
    Operational mode: Normal TPM operational mode (0x0)
    KeyGroupId 0x5, FwCounter 1255 (255 same)
    tpm2 firmware_update: rc=0 (Success)

**DO NOT power off or reset during the update!**

**Step 8: Verify update**

After the update completes, verify with::

    U-Boot> wolftpm caps

The firmware version should show the new version.

**Recovery Mode:**

If the TPM enters recovery mode (opMode shows 0x02 or 0x8x), the firmware update
command will automatically use recovery mode. You may need to run the update again
to complete the process.

Canceling a Firmware Update
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If an update is in progress and needs to be abandoned (opMode 0x01), use::

    U-Boot> wolftpm firmware_cancel
    tpm2 init: rc = 0 (Success)
    tpm2 firmware_cancel: rc=0 (Success)

**IMPORTANT: After running firmware_cancel, you MUST reboot/power cycle the system
before running any other TPM commands.** If you attempt to run commands without
rebooting, you will get ``TPM_RC_REBOOT`` (error 304)::

    U-Boot> wolftpm firmware_update ...
    tpm2 init: rc = 304 (TPM_RC_REBOOT)
    Infineon firmware update failed 0x130: TPM_RC_REBOOT

After rebooting, the TPM will return to normal operation and you can retry the
firmware update or continue with normal TPM operations.

**Note:** If no firmware update is in progress, ``firmware_cancel`` returns
``TPM_RC_COMMAND_CODE`` (0x143), which is expected and harmless::

    U-Boot> wolftpm firmware_cancel
    tpm2 firmware_cancel: rc=323 (TPM_RC_COMMAND_CODE)

Enabling wolfTPM in U-Boot
--------------------------

Enable wolfTPM support in U-Boot by adding these options to your board's defconfig::

  CONFIG_TPM=y
  CONFIG_TPM_V2=y
  CONFIG_TPM_WOLF=y
  CONFIG_CMD_WOLFTPM=y

  if with __LINUX__:
    CONFIG_TPM_LINUX_DEV=y

Or use ``make menuconfig`` and enable:

Enabling Debug Output
~~~~~~~~~~~~~~~~~~~~~

wolfTPM commands use U-Boot's logging system (``log_debug()``). To enable debug
output, you must first enable the logging subsystem in your board's defconfig::

    CONFIG_LOG=y
    CONFIG_LOG_MAX_LEVEL=7
    CONFIG_LOG_DEFAULT_LEVEL=7

Or via ``make menuconfig``:

- Console → Enable logging support
- Console → Maximum log level to record = 7
- Console → Default logging level to display = 7

Log levels:
- 7 = DEBUG (to show wolfTPM command debug output)

**Note:** Without ``CONFIG_LOG=y``, the ``log level`` command will not exist
and ``log_debug()`` calls will produce no output.

wolfTPM Library Debug
^^^^^^^^^^^^^^^^^^^^^

For lower-level wolfTPM library debug output (TPM protocol messages), edit
``include/configs/user_settings.h`` and uncomment::

    #define DEBUG_WOLFTPM           /* Basic wolfTPM debug messages */
    #define WOLFTPM_DEBUG_VERBOSE   /* Verbose debug messages */
    #define WOLFTPM_DEBUG_IO        /* IO-level debug (SPI transfers) */

After enabling, rebuild U-Boot::

    make clean
    make -j4

Menuconfig Paths
^^^^^^^^^^^^^^^^

The following menuconfig paths are useful for wolfTPM:

- Device Drivers → TPM → TPM 2.0 Support
- Device Drivers → TPM → wolfTPM Support
- Command line interface → Security commands → Enable wolfTPM commands
- Console → Enable logging support (for ``log_debug()`` output)

Building and Running wolfTPM with U-Boot using QEMU
---------------------------------------------------

To build and run wolfTPM with U-Boot using QEMU and a TPM simulator, follow these steps:

1. Install swtpm::

     git clone https://github.com/stefanberger/swtpm.git
     cd swtpm
     ./autogen.sh
     make

2. Build U-Boot::

     make distclean
     export CROSS_COMPILE=aarch64-linux-gnu-
     export ARCH=aarch64
     make qemu_arm64_defconfig
     make -j4

3. Create TPM directory::

     mkdir -p /tmp/mytpm1

4. Start swtpm (in first terminal)::

     swtpm socket --tpm2 --tpmstate dir=/tmp/mytpm1 --ctrl type=unixio,path=/tmp/mytpm1/swtpm-sock --log level=20

5. Start QEMU (in second terminal)::

     qemu-system-aarch64 -machine virt -nographic -cpu cortex-a57 -bios u-boot.bin -chardev socket,id=chrtpm,path=/tmp/mytpm1/swtpm-sock -tpmdev emulator,id=tpm0,chardev=chrtpm -device tpm-tis-device,tpmdev=tpm0

6. Example output::

     U-Boot 2025.07-rc1-ge15cbf232ddf-dirty (May 06 2025 - 16:25:56 -0700)
     ...
     => tpm2 help
     tpm2 - Issue a TPMv2.x command
     Usage:
     tpm2 <command> [<arguments>]
     ...
     => tpm2 info
     tpm_tis@0 v2.0: VendorID 0x1014, DeviceID 0x0001, RevisionID 0x01 [open]
     => tpm2 startup TPM2_SU_CLEAR
     => tpm2 get_capability 0x6 0x20e 0x200 1
     Capabilities read from TPM:
     Property 0x6a2e45a9: 0x6c3646a9
     => tpm2 pcr_read 10 0x100000
     PCR #10 sha256 32 byte content (20 known updates):
      20 25 73 0a 00 56 61 6c 75 65 3a 0a 00 23 23 20
      4f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 23

7. Example commands::

     => tpm2 info
     tpm_tis@0 v2.0: VendorID 0x1014, DeviceID 0x0001, RevisionID 0x01 [open]
     ...
     => tpm2 pcr_read 10 0x100000
     PCR #10 sha256 32 byte content (20 known updates):
      20 25 73 0a 00 56 61 6c 75 65 3a 0a 00 23 23 20
      4f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 23

8. Exiting the QEMU:
   Press Ctrl-A followed by X

Testing wolfTPM
---------------

wolfTPM includes a comprehensive test suite based on the existing TPM2 tests.
The tests are located in:

- ``test/cmd/wolftpm.c`` - C unit tests (based on ``test/dm/tpm.c`` and ``test/cmd/hash.c``)
- ``test/py/tests/test_wolftpm.py`` - Python integration tests (based on ``test/py/tests/test_tpm2.py``)

Running C Unit Tests
~~~~~~~~~~~~~~~~~~~~

The C unit tests use the U-Boot test framework and can be run in sandbox mode
or on real hardware. To run all wolfTPM tests::

    # Build sandbox with tests enabled
    make sandbox_defconfig
    # Enable wolfTPM in menuconfig
    make menuconfig
    make -j4

    # Run U-Boot sandbox
    ./u-boot -T

    # In U-Boot sandbox, run the unit tests
    => ut cmd

Individual tests can be run by name::

    => ut cmd cmd_test_wolftpm_autostart
    => ut cmd cmd_test_wolftpm_init
    => ut cmd cmd_test_wolftpm_self_test
    => ut cmd cmd_test_wolftpm_caps
    => ut cmd cmd_test_wolftpm_clear
    => ut cmd cmd_test_wolftpm_pcr_read
    => ut cmd cmd_test_wolftpm_pcr_extend

Running Python Tests
~~~~~~~~~~~~~~~~~~~~

The Python tests require pytest and can be run against real hardware or QEMU
with swtpm. First, ensure swtpm is running (see QEMU instructions above).

To run all wolfTPM Python tests::

    # From the U-Boot root directory
    ./test/py/test.py --bd qemu_arm64 -k test_wolftpm

To run individual Python tests::

    ./test/py/test.py --bd qemu_arm64 -k test_wolftpm_autostart
    ./test/py/test.py --bd qemu_arm64 -k test_wolftpm_caps
    ./test/py/test.py --bd qemu_arm64 -k test_wolftpm_pcr_read

To skip wolfTPM tests (e.g., when no TPM hardware is available), set the
environment variable in your board configuration::

    env__wolftpm_device_test_skip = True

Running Tests Manually in QEMU
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also test wolfTPM commands manually in QEMU:

1. Start swtpm::

     mkdir -p /tmp/mytpm
     swtpm socket --tpm2 --tpmstate dir=/tmp/mytpm \
       --ctrl type=unixio,path=/tmp/mytpm/swtpm-sock --log level=20

2. Start QEMU with TPM::

     qemu-system-aarch64 -machine virt -cpu cortex-a57 -m 1024 \
       -bios u-boot.bin \
       -chardev socket,id=chrtpm,path=/tmp/mytpm/swtpm-sock \
       -tpmdev emulator,id=tpm0,chardev=chrtpm \
       -device tpm-tis-device,tpmdev=tpm0 \
       -nographic

3. Run wolfTPM commands at the U-Boot prompt::

     => wolftpm autostart
     => wolftpm caps
     => wolftpm pcr_read 0 sha256
     => wolftpm pcr_print
     => wolftpm self_test full
     => wolftpm clear TPM2_RH_LOCKOUT
     => wolftpm dam_parameters 3 10 0

Test Coverage
~~~~~~~~~~~~~

The test suite covers the following wolfTPM functionality:

+---------------------------+------------------------------------------+
| Test Name                 | Description                              |
+===========================+==========================================+
| wolftpm_autostart         | TPM initialization and startup           |
+---------------------------+------------------------------------------+
| wolftpm_init              | TPM device initialization                |
+---------------------------+------------------------------------------+
| wolftpm_self_test         | Full TPM self-test                       |
+---------------------------+------------------------------------------+
| wolftpm_self_test_continue| Continue incomplete self-tests           |
+---------------------------+------------------------------------------+
| wolftpm_caps              | Read TPM capabilities                    |
+---------------------------+------------------------------------------+
| wolftpm_clear             | Clear TPM state                          |
+---------------------------+------------------------------------------+
| wolftpm_pcr_read          | Read PCR values                          |
+---------------------------+------------------------------------------+
| wolftpm_pcr_extend        | Extend PCR with digest                   |
+---------------------------+------------------------------------------+
| wolftpm_pcr_print         | Print all PCR values                     |
+---------------------------+------------------------------------------+
| wolftpm_pcr_allocate      | Reconfigure PCR bank algorithm           |
+---------------------------+------------------------------------------+
| wolftpm_dam_reset         | Reset DAM counter                        |
+---------------------------+------------------------------------------+
| wolftpm_dam_parameters    | Set DAM parameters                       |
+---------------------------+------------------------------------------+
| wolftpm_change_auth       | Change hierarchy password                |
+---------------------------+------------------------------------------+
| wolftpm_info              | Display TPM info                         |
+---------------------------+------------------------------------------+
| wolftpm_state             | Display TPM state                        |
+---------------------------+------------------------------------------+
| wolftpm_device            | Show/set TPM device                      |
+---------------------------+------------------------------------------+
| wolftpm_startup_clear     | TPM2_Startup with CLEAR mode             |
+---------------------------+------------------------------------------+
| wolftpm_startup_state     | TPM2_Startup with STATE mode             |
+---------------------------+------------------------------------------+
| wolftpm_startup_shutdown  | TPM2_Shutdown command                    |
+---------------------------+------------------------------------------+
| wolftpm_get_capability    | Read TPM capabilities by property        |
+---------------------------+------------------------------------------+

TODO: Commands Not Yet Tested
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following commands are implemented in ``cmd/wolftpm.c`` but do not yet have
test coverage due to special requirements:

+---------------------------+------------------------------------------+------------------+
| Command                   | Description                              | Notes            |
+===========================+==========================================+==================+
| pcr_setauthpolicy         | Set PCR authorization policy             | Requires         |
|                           |                                          | wolfCrypt        |
+---------------------------+------------------------------------------+------------------+
| pcr_setauthvalue          | Set PCR authorization value              | Requires         |
|                           |                                          | wolfCrypt        |
+---------------------------+------------------------------------------+------------------+
| firmware_update           | Update TPM firmware (Infineon only)      | Requires         |
|                           |                                          | Infineon HW      |
+---------------------------+------------------------------------------+------------------+
| firmware_cancel           | Cancel firmware update (Infineon only)   | Requires         |
|                           |                                          | Infineon HW      |
+---------------------------+------------------------------------------+------------------+

**Note:** The ``pcr_setauthpolicy`` and ``pcr_setauthvalue`` commands require
``WOLFTPM2_NO_WOLFCRYPT`` to be undefined (i.e., wolfCrypt must be enabled).
The ``firmware_update`` and ``firmware_cancel`` commands require Infineon
SLB9672/SLB9673 hardware.

To add tests for these commands:

1. Add C unit test in ``test/cmd/wolftpm.c``::

     static int cmd_test_wolftpm_<command>(struct unit_test_state *uts)
     {
         ut_assertok(run_command("wolftpm autostart", 0));
         ut_assertok(run_command("wolftpm <command> <args>", 0));
         return 0;
     }
     CMD_TEST(cmd_test_wolftpm_<command>, 0);

2. Add Python test in ``test/py/tests/test_wolftpm.py``::

     @pytest.mark.buildconfigspec('tpm_wolf')
     def test_wolftpm_<command>(ubman):
         force_init(ubman)
         ubman.run_command('wolftpm <command> <args>')
         output = ubman.run_command('echo $?')
         assert output.endswith('0')

TODO: Testing on Raspberry Pi Hardware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For testing with real TPM hardware (e.g., Infineon SLB9672 TPM HAT on Raspberry Pi):

1. Build U-Boot for Raspberry Pi::

     make distclean
     export CROSS_COMPILE=aarch64-linux-gnu-
     export ARCH=aarch64
     make rpi_arm64_defconfig
     make -j$(nproc)

2. Backup current boot configuration::

     sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.backup

3. Copy U-Boot to boot partition::

     sudo cp u-boot.bin /boot/firmware/

4. Edit ``/boot/firmware/config.txt`` and add::

     # U-Boot for wolfTPM testing
     enable_uart=1
     kernel=u-boot.bin
     arm_64bit=1

5. Connect serial console (recommended) - USB-to-serial adapter on GPIO 14/15
   (pins 8/10) at 115200 baud.

6. Reboot and test at U-Boot prompt::

     U-Boot> wolftpm device
     U-Boot> wolftpm info
     U-Boot> wolftpm autostart
     U-Boot> wolftpm caps
     U-Boot> wolftpm pcr_read 0 0x1000000 SHA256

7. To restore normal Linux boot::

     sudo cp /boot/firmware/config.txt.backup /boot/firmware/config.txt
     sudo reboot

**Note:** The Raspberry Pi build uses GPIO-based soft SPI for TPM communication.
Standard SPI0 pins are used: GPIO 11 (SCLK), GPIO 10 (MOSI), GPIO 9 (MISO),
GPIO 7 (CE1 for TPM). Adjust ``arch/arm/dts/bcm2711-rpi-4-b-u-boot.dtsi`` if
your TPM HAT uses different GPIO pins.

TODO: Python Test Framework
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Python tests in ``test/py/tests/test_wolftpm.py`` require additional setup
for QEMU boards (external ``u-boot-test-flash``, ``u-boot-test-console``, etc.
scripts). The C unit tests (``test/cmd/wolftpm.c``) provide equivalent coverage
and work directly with ``ut cmd`` in U-Boot.

**Status:** Python tests need verification with proper QEMU test infrastructure
or deprecation in favor of C unit tests which are fully functional.

Testing wolfTPM SPI Path in Sandbox
-----------------------------------

The sandbox build includes a TPM SPI emulator that tests the complete wolfTPM
SPI communication path without requiring hardware. This validates the SPI HAL
code path in ``lib/wolftpm/hal/tpm_io_uboot.c``.

SPI Code Path
~~~~~~~~~~~~~

When testing in sandbox, the following code path is exercised::

    wolftpm commands (cmd/wolftpm.c)
           ↓
    wolfTPM library (lib/wolftpm/)
           ↓
    SPI HAL (lib/wolftpm/hal/tpm_io_uboot.c)
           ↓
    U-Boot SPI API (spi_get_bus_and_cs, spi_xfer)
           ↓
    Sandbox SPI Master (drivers/spi/sandbox_spi.c)
           ↓
    TPM SPI Emulator (drivers/tpm/tpm_spi_sandbox.c)

The TPM SPI emulator implements the TPM TIS (Trusted Platform Module Interface
Specification) over SPI protocol:

- 4-byte SPI header: ``[R/W|len-1][0xD4][addr_hi][addr_lo]``
- Wait-state handling with ready byte
- TIS register emulation (ACCESS, STS, FIFO, DID/VID, RID)
- TIS state machine (IDLE → READY → RECEPTION → COMPLETION)

Building Sandbox with SPI Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To build sandbox with TPM SPI emulator support::

    make sandbox_defconfig
    make -j$(nproc)

The following configs are enabled by default in sandbox:

- ``CONFIG_TPM=y``
- ``CONFIG_TPM_V2=y``
- ``CONFIG_TPM_WOLF=y``
- ``CONFIG_CMD_WOLFTPM=y``
- ``CONFIG_TPM2_SPI_SANDBOX=y``

Running SPI Tests
~~~~~~~~~~~~~~~~~

**Important:** The sandbox TPM SPI device requires the ``-D`` flag to load the
full device tree. Without this flag, the SPI bus will not be available.

Run wolfTPM commands via SPI::

    # Build sandbox
    make sandbox_defconfig && make -j$(nproc)

    # Run with full device tree
    ./u-boot -D

    # At U-Boot prompt, test wolfTPM SPI path
    => wolftpm autostart
    => wolftpm caps
    => wolftpm info
    => wolftpm pcr_read 0 0x1000000 SHA256
    => wolftpm pcr_print

Non-interactive testing::

    # Single command
    ./u-boot -D -c "wolftpm autostart"

    # Multiple commands
    ./u-boot -D -c "wolftpm autostart; wolftpm caps; wolftpm info"

Expected output::

    TPM SPI initialized: bus 0, cs 1
    TPM2: Caps 0x30000697, Did 0x001d, Vid 0x15d1, Rid 0x36
    TPM2_Startup pass
    wolfTPM2_Reset complete
    TPM2_SelfTest pass

Enabling Debug Output
~~~~~~~~~~~~~~~~~~~~~

To see SPI-level debug messages, enable logging before running::

    # At U-Boot prompt
    => log level 7

Or enable in defconfig::

    CONFIG_LOG=y
    CONFIG_LOG_MAX_LEVEL=7
    CONFIG_LOG_DEFAULT_LEVEL=7

For wolfTPM library-level SPI debug, edit ``include/configs/user_settings.h``::

    #define DEBUG_WOLFTPM
    #define WOLFTPM_DEBUG_IO    /* Shows SPI transfer details */

Device Tree Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

The sandbox SPI TPM is defined in ``arch/sandbox/dts/sandbox.dtsi``::

    &spi0 {
        tpm_spi: tpm@1 {
            reg = <1>;
            compatible = "sandbox,tpm-spi";
            spi-max-frequency = <10000000>;
            sandbox,emul = <&tpm_spi_emul>;
        };
    };

    tpm_spi_emul: tpm-spi-emul {
        compatible = "sandbox,tpm-spi-emul";
    };

The emulator driver is in ``drivers/tpm/tpm_spi_sandbox.c``.
