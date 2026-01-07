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

Enabling wolfTPM in U-Boot
--------------------------

Enable wolfTPM support in U-Boot by adding these options to your board's defconfig::

  CONFIG_TPM=y
  CONFIG_TPM_V2=y
  CONFIG_TPM_WOLF=y
  CONFIG_CMD_WOLFTPM=y

Or use ``make menuconfig`` and enable:

Enabling Debug Output
~~~~~~~~~~~~~~~~~~~~~

wolfTPM commands use U-Boot's logging system. To see debug output at runtime,
use the ``log level`` command at the U-Boot prompt::

    => log level 7

Log levels:

- 4 = WARNING (default)
- 6 = INFO
- 7 = DEBUG (shows wolfTPM command debug output)
- 9 = DEBUG_IO (very verbose)

Example with debug enabled::

    => log level 7
    => wolftpm autostart
    tpm2 init: rc = 0 (Success)
    wolfTPM2_Reset: rc = 0 (Success)
    wolfTPM2_SelfTest: rc = 0 (Success)

To make debug level persistent, add to your board's environment::

    => setenv loglevel 7
    => saveenv

wolfTPM Library Debug
^^^^^^^^^^^^^^^^^^^^^

For lower-level wolfTPM library debug output, edit
``include/configs/user_settings.h`` and uncomment::

    #define DEBUG_WOLFTPM           /* Basic wolfTPM debug messages */
    #define WOLFTPM_DEBUG_VERBOSE   /* Verbose debug messages */
    #define WOLFTPM_DEBUG_IO        /* IO-level debug (SPI transfers) */

After enabling, rebuild U-Boot::

    make clean
    make -j4

- Device Drivers → TPM → TPM 2.0 Support
- Device Drivers → TPM → wolfTPM Support
- Command line interface → Security commands → Enable wolfTPM commands

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
    => ut cmd wolftpm

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
