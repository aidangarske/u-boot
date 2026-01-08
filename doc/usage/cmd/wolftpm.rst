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

TODO: Python Test Framework
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Python tests in ``test/py/tests/test_wolftpm.py`` require additional setup
for QEMU boards (external ``u-boot-test-flash``, ``u-boot-test-console``, etc.
scripts). The C unit tests (``test/cmd/wolftpm.c``) provide equivalent coverage
and work directly with ``ut cmd`` in U-Boot.

**Status:** Python tests need verification with proper QEMU test infrastructure
or deprecation in favor of C unit tests which are fully functional.
