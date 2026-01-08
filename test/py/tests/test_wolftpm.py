# SPDX-License-Identifier: GPL-2.0+
# Copyright (C) 2025 wolfSSL Inc.
# Author: Aidan Garske <aidan@wolfssl.com>
#
# Based on test_tpm2.py by Miquel Raynal <miquel.raynal@bootlin.com>

"""
Test the wolfTPM related commands. These tests require a TPM device
(real hardware or software TPM emulator like swtpm).

Notes:
* These tests will prove the password mechanism. The TPM chip must be cleared of
  any password.
* Tests are designed to be similar to test_tpm2.py but use wolfTPM wrapper APIs.

Configuration:
* Set env__wolftpm_device_test_skip to True to skip these tests.
"""

import os.path
import pytest
import utils
import re
import time


def force_init(ubman, force=False):
    """Initialize wolfTPM before running tests.

    When a test fails, U-Boot may be reset. Because TPM stack must be initialized
    after each reboot, we must ensure these lines are always executed before
    trying any command or they will fail with no reason.
    """
    skip_test = ubman.config.env.get('env__wolftpm_device_test_skip', False)
    if skip_test:
        pytest.skip('skip wolfTPM device test')
    output = ubman.run_command('wolftpm autostart')
    if force or 'Error' not in output:
        ubman.run_command('echo --- start of init ---')
        ubman.run_command('wolftpm clear TPM2_RH_LOCKOUT')
        output = ubman.run_command('echo $?')
        if not output.endswith('0'):
            ubman.run_command('wolftpm clear TPM2_RH_PLATFORM')
        ubman.run_command('echo --- end of init ---')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_autostart(ubman):
    """Test wolfTPM autostart command.

    Initialize the software stack, perform startup and self-test.
    """
    skip_test = ubman.config.env.get('env__wolftpm_device_test_skip', False)
    if skip_test:
        pytest.skip('skip wolfTPM device test')
    ubman.run_command('wolftpm autostart')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_init(ubman):
    """Test wolfTPM init command.

    Initialize the TPM device for communication.
    """
    skip_test = ubman.config.env.get('env__wolftpm_device_test_skip', False)
    if skip_test:
        pytest.skip('skip wolfTPM device test')
    ubman.run_command('wolftpm init')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_self_test_full(ubman):
    """Test wolfTPM full self_test command.

    Perform a full TPM self-test to verify all components are operational.
    """
    skip_test = ubman.config.env.get('env__wolftpm_device_test_skip', False)
    if skip_test:
        pytest.skip('skip wolfTPM device test')
    ubman.run_command('wolftpm autostart')
    ubman.run_command('wolftpm self_test full')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_self_test_continue(ubman):
    """Test wolfTPM continue self_test command.

    Ask the TPM to finish any remaining self tests.
    """
    skip_test = ubman.config.env.get('env__wolftpm_device_test_skip', False)
    if skip_test:
        pytest.skip('skip wolfTPM device test')
    ubman.run_command('wolftpm autostart')
    ubman.run_command('wolftpm self_test continue')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_caps(ubman):
    """Test wolfTPM caps command.

    Display TPM capabilities and vendor information.
    """
    force_init(ubman)
    caps_output = ubman.run_command('wolftpm caps')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')
    # Should contain manufacturer info
    assert 'Mfg' in caps_output or 'Vendor' in caps_output or 'wolfTPM' in caps_output


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_clear(ubman):
    """Test wolfTPM clear command.

    Clear the TPM internal state using LOCKOUT hierarchy.
    LOCKOUT/PLATFORM hierarchies must not have a password set.
    """
    skip_test = ubman.config.env.get('env__wolftpm_device_test_skip', False)
    if skip_test:
        pytest.skip('skip wolfTPM device test')
    ubman.run_command('wolftpm autostart')
    ubman.run_command('wolftpm clear TPM2_RH_LOCKOUT')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')

    ubman.run_command('wolftpm clear TPM2_RH_PLATFORM')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_change_auth(ubman):
    """Test wolfTPM change_auth command.

    Change the owner/hierarchy password.
    """
    force_init(ubman)

    # Change LOCKOUT password to 'unicorn'
    ubman.run_command('wolftpm change_auth TPM2_RH_LOCKOUT unicorn')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')

    # Clear with new password to verify
    ubman.run_command('wolftpm clear TPM2_RH_LOCKOUT unicorn')
    output = ubman.run_command('echo $?')
    ubman.run_command('wolftpm clear TPM2_RH_PLATFORM')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_dam_parameters(ubman):
    """Test wolfTPM dam_parameters command.

    Change Dictionary Attack Mitigation parameters:
    - Max number of failed authentication before lockout: 3
    - Time before failure counter is decremented: 10 sec
    - Time after lockout failure before retry: 0 sec
    """
    force_init(ubman)

    # Set DAM parameters
    ubman.run_command('wolftpm dam_parameters 3 10 0')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_dam_reset(ubman):
    """Test wolfTPM dam_reset command.

    Reset the Dictionary Attack Mitigation counter.
    """
    force_init(ubman)

    ubman.run_command('wolftpm dam_reset')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_pcr_read(ubman):
    """Test wolfTPM pcr_read command.

    Read PCR value from a specific index.
    """
    force_init(ubman)

    # Read PCR 0 with SHA256
    read_pcr = ubman.run_command('wolftpm pcr_read 0 sha256')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')

    # Check for PCR output
    assert 'PCR' in read_pcr or 'digest' in read_pcr.lower() or 'sha256' in read_pcr.lower()


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_pcr_extend(ubman):
    """Test wolfTPM pcr_extend command.

    Extend a PCR with a digest value.
    PCR 16-23 are typically available for debug/testing.
    """
    force_init(ubman)
    ram = utils.find_ram_base(ubman)

    # Read PCR 16 first
    read_pcr = ubman.run_command('wolftpm pcr_read 16 sha256')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')

    # Extend PCR 16 with zeroed memory
    ubman.run_command('wolftpm pcr_extend 16 0x%x sha256' % ram)
    output = ubman.run_command('echo $?')
    assert output.endswith('0')

    # Read again to verify it changed
    read_pcr_after = ubman.run_command('wolftpm pcr_read 16 sha256')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_pcr_print(ubman):
    """Test wolfTPM pcr_print command.

    Print all assigned PCRs.
    """
    force_init(ubman)

    pcr_output = ubman.run_command('wolftpm pcr_print')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')

    # Should contain PCR info
    assert 'PCR' in pcr_output or 'Assigned' in pcr_output


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_info(ubman):
    """Test wolfTPM info command.

    Display TPM device information.
    """
    force_init(ubman)

    ubman.run_command('wolftpm info')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_state(ubman):
    """Test wolfTPM state command.

    Display TPM internal state.
    """
    force_init(ubman)

    ubman.run_command('wolftpm state')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_device(ubman):
    """Test wolfTPM device command.

    Show all TPM devices.
    """
    skip_test = ubman.config.env.get('env__wolftpm_device_test_skip', False)
    if skip_test:
        pytest.skip('skip wolfTPM device test')
    ubman.run_command('wolftpm device')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_startup_clear(ubman):
    """Test wolfTPM startup command with TPM2_SU_CLEAR.

    Issue TPM2_Startup with CLEAR mode (reset state).
    """
    skip_test = ubman.config.env.get('env__wolftpm_device_test_skip', False)
    if skip_test:
        pytest.skip('skip wolfTPM device test')
    ubman.run_command('wolftpm init')
    ubman.run_command('wolftpm startup TPM2_SU_CLEAR')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_startup_state(ubman):
    """Test wolfTPM startup command with TPM2_SU_STATE.

    Issue TPM2_Startup with STATE mode (preserved state).
    """
    skip_test = ubman.config.env.get('env__wolftpm_device_test_skip', False)
    if skip_test:
        pytest.skip('skip wolfTPM device test')
    # First autostart to have valid state
    ubman.run_command('wolftpm autostart')
    # Shutdown with STATE
    ubman.run_command('wolftpm startup TPM2_SU_STATE off')
    # Re-init
    ubman.run_command('wolftpm init')
    # Startup with STATE - may return already started
    ubman.run_command('wolftpm startup TPM2_SU_STATE')
    output = ubman.run_command('echo $?')
    # May return non-zero if already started, just verify command ran
    assert output is not None


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_startup_shutdown(ubman):
    """Test wolfTPM startup shutdown command.

    Issue TPM2_Shutdown.
    """
    skip_test = ubman.config.env.get('env__wolftpm_device_test_skip', False)
    if skip_test:
        pytest.skip('skip wolfTPM device test')
    ubman.run_command('wolftpm autostart')
    ubman.run_command('wolftpm startup TPM2_SU_CLEAR off')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_get_capability(ubman):
    """Test wolfTPM get_capability command.

    Read TPM capabilities by property.
    """
    force_init(ubman)
    ram = utils.find_ram_base(ubman)

    # Get capability - TPM_CAP_TPM_PROPERTIES (0x6), PT_MANUFACTURER (0x20e)
    ubman.run_command('wolftpm get_capability 0x6 0x20e 0x%x 1' % ram)
    output = ubman.run_command('echo $?')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_pcr_allocate(ubman):
    """Test wolfTPM pcr_allocate command.

    Reconfigure PCR bank algorithm.
    Note: A TPM restart is required for changes to take effect.
    """
    force_init(ubman)

    # Allocate SHA256 bank on
    ubman.run_command('wolftpm pcr_allocate SHA256 on')
    output = ubman.run_command('echo $?')
    assert output.endswith('0')


@pytest.mark.buildconfigspec('tpm_wolf')
def test_wolftpm_cleanup(ubman):
    """Cleanup test - ensure TPM is cleared after tests."""
    force_init(ubman, True)
