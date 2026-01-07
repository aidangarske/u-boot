// SPDX-License-Identifier: GPL-2.0+
/*
 * Tests for wolfTPM commands
 *
 * Copyright (C) 2025 wolfSSL Inc.
 * Author: Aidan Garske <aidan@wolfssl.com>
 *
 * Based on test/py/tests/test_tpm2.py and test/dm/tpm.c
 */

#include <command.h>
#include <dm.h>
#include <dm/test.h>
#include <test/cmd.h>
#include <test/test.h>
#include <test/ut.h>

/**
 * Test wolfTPM autostart command
 *
 * This initializes the TPM, performs startup and self-test
 */
static int cmd_test_wolftpm_autostart(struct unit_test_state *uts)
{
	/* Initialize and autostart the TPM */
	ut_assertok(run_command("wolftpm autostart", 0));
	ut_assert_console_end();

	return 0;
}
CMD_TEST(cmd_test_wolftpm_autostart, UTF_CONSOLE);

/**
 * Test wolfTPM init command
 */
static int cmd_test_wolftpm_init(struct unit_test_state *uts)
{
	ut_assertok(run_command("wolftpm init", 0));
	ut_assert_console_end();

	return 0;
}
CMD_TEST(cmd_test_wolftpm_init, UTF_CONSOLE);

/**
 * Test wolfTPM self_test command
 */
static int cmd_test_wolftpm_self_test(struct unit_test_state *uts)
{
	/* First autostart to ensure TPM is ready */
	ut_assertok(run_command("wolftpm autostart", 0));

	/* Run full self test */
	ut_assertok(run_command("wolftpm self_test full", 0));
	ut_assert_console_end();

	return 0;
}
CMD_TEST(cmd_test_wolftpm_self_test, UTF_CONSOLE);

/**
 * Test wolfTPM self_test continue command
 */
static int cmd_test_wolftpm_self_test_continue(struct unit_test_state *uts)
{
	/* First autostart to ensure TPM is ready */
	ut_assertok(run_command("wolftpm autostart", 0));

	/* Run continue self test */
	ut_assertok(run_command("wolftpm self_test continue", 0));
	ut_assert_console_end();

	return 0;
}
CMD_TEST(cmd_test_wolftpm_self_test_continue, UTF_CONSOLE);

/**
 * Test wolfTPM caps command (get capabilities)
 *
 * Display TPM capabilities and vendor info
 */
static int cmd_test_wolftpm_caps(struct unit_test_state *uts)
{
	/* First autostart to ensure TPM is ready */
	ut_assertok(run_command("wolftpm autostart", 0));

	/* Get TPM capabilities */
	ut_assertok(run_command("wolftpm caps", 0));

	/* Check for expected output patterns */
	console_record_readline(uts->actual_str, sizeof(uts->actual_str));
	/* Should contain manufacturer info */
	ut_assert(strstr(uts->actual_str, "Mfg") ||
		  strstr(uts->actual_str, "Vendor") ||
		  strstr(uts->actual_str, "wolfTPM"));

	return 0;
}
CMD_TEST(cmd_test_wolftpm_caps, UTF_CONSOLE);

/**
 * Test wolfTPM clear command
 *
 * Reset TPM internal state using LOCKOUT hierarchy
 */
static int cmd_test_wolftpm_clear(struct unit_test_state *uts)
{
	/* First autostart to ensure TPM is ready */
	ut_assertok(run_command("wolftpm autostart", 0));

	/* Clear using LOCKOUT hierarchy */
	ut_assertok(run_command("wolftpm clear TPM2_RH_LOCKOUT", 0));
	ut_assert_console_end();

	return 0;
}
CMD_TEST(cmd_test_wolftpm_clear, UTF_CONSOLE);

/**
 * Test wolfTPM pcr_read command
 *
 * Read PCR value from a specific index
 */
static int cmd_test_wolftpm_pcr_read(struct unit_test_state *uts)
{
	/* First autostart to ensure TPM is ready */
	ut_assertok(run_command("wolftpm autostart", 0));

	/* Read PCR 0 with SHA256 */
	ut_assertok(run_command("wolftpm pcr_read 0 sha256", 0));

	/* Check for PCR output */
	console_record_readline(uts->actual_str, sizeof(uts->actual_str));
	ut_assert(strstr(uts->actual_str, "PCR") ||
		  strstr(uts->actual_str, "digest") ||
		  strstr(uts->actual_str, "sha256"));

	return 0;
}
CMD_TEST(cmd_test_wolftpm_pcr_read, UTF_CONSOLE);

/**
 * Test wolfTPM pcr_extend command
 *
 * Extend a PCR with a digest value
 */
static int cmd_test_wolftpm_pcr_extend(struct unit_test_state *uts)
{
	/* First autostart to ensure TPM is ready */
	ut_assertok(run_command("wolftpm autostart", 0));

	/* Clear to start fresh */
	run_command("wolftpm clear TPM2_RH_LOCKOUT", 0);

	/* Extend PCR 16 (resettable PCR) with a test digest
	 * PCR 16-23 are typically available for debug/testing
	 */
	ut_assertok(run_command("wolftpm pcr_extend 16 $loadaddr sha256", 0));

	/* Check output indicates success */
	console_record_readline(uts->actual_str, sizeof(uts->actual_str));
	ut_assert(strstr(uts->actual_str, "PCR") ||
		  strstr(uts->actual_str, "extended") ||
		  strstr(uts->actual_str, "16"));

	return 0;
}
CMD_TEST(cmd_test_wolftpm_pcr_extend, UTF_CONSOLE);

/**
 * Test wolfTPM pcr_print command
 *
 * Print all PCR values
 */
static int cmd_test_wolftpm_pcr_print(struct unit_test_state *uts)
{
	/* First autostart to ensure TPM is ready */
	ut_assertok(run_command("wolftpm autostart", 0));

	/* Print all PCRs */
	ut_assertok(run_command("wolftpm pcr_print", 0));

	/* Should have PCR output */
	console_record_readline(uts->actual_str, sizeof(uts->actual_str));
	ut_assert(strstr(uts->actual_str, "PCR") ||
		  strstr(uts->actual_str, "Assigned"));

	return 0;
}
CMD_TEST(cmd_test_wolftpm_pcr_print, UTF_CONSOLE);

/**
 * Test wolfTPM dam_reset command
 *
 * Reset Dictionary Attack Mitigation counter
 */
static int cmd_test_wolftpm_dam_reset(struct unit_test_state *uts)
{
	/* First autostart to ensure TPM is ready */
	ut_assertok(run_command("wolftpm autostart", 0));

	/* Reset DAM counter */
	ut_assertok(run_command("wolftpm dam_reset", 0));
	ut_assert_console_end();

	return 0;
}
CMD_TEST(cmd_test_wolftpm_dam_reset, UTF_CONSOLE);

/**
 * Test wolfTPM dam_parameters command
 *
 * Set Dictionary Attack Mitigation parameters
 */
static int cmd_test_wolftpm_dam_parameters(struct unit_test_state *uts)
{
	/* First autostart to ensure TPM is ready */
	ut_assertok(run_command("wolftpm autostart", 0));

	/* Set DAM parameters:
	 * - max_tries: 3
	 * - recovery_time: 10 seconds
	 * - lockout_recovery: 0 seconds
	 */
	ut_assertok(run_command("wolftpm dam_parameters 3 10 0", 0));

	/* Check for parameter output */
	console_record_readline(uts->actual_str, sizeof(uts->actual_str));
	ut_assert(strstr(uts->actual_str, "maxTries") ||
		  strstr(uts->actual_str, "recovery") ||
		  strstr(uts->actual_str, "DAM") ||
		  strstr(uts->actual_str, "3"));

	return 0;
}
CMD_TEST(cmd_test_wolftpm_dam_parameters, UTF_CONSOLE);

/**
 * Test wolfTPM change_auth command
 *
 * Change hierarchy authorization password
 */
static int cmd_test_wolftpm_change_auth(struct unit_test_state *uts)
{
	/* First autostart and clear to ensure clean state */
	ut_assertok(run_command("wolftpm autostart", 0));
	run_command("wolftpm clear TPM2_RH_LOCKOUT", 0);

	/* Change LOCKOUT password to "testpw" */
	ut_assertok(run_command("wolftpm change_auth TPM2_RH_LOCKOUT testpw", 0));
	ut_assert_console_end();

	/* Clear with new password to verify it worked */
	ut_assertok(run_command("wolftpm clear TPM2_RH_LOCKOUT testpw", 0));
	ut_assert_console_end();

	return 0;
}
CMD_TEST(cmd_test_wolftpm_change_auth, UTF_CONSOLE);

/**
 * Test wolfTPM info command
 *
 * Display TPM device information
 */
static int cmd_test_wolftpm_info(struct unit_test_state *uts)
{
	/* First autostart to ensure TPM is ready */
	ut_assertok(run_command("wolftpm autostart", 0));

	/* Get TPM info */
	ut_assertok(run_command("wolftpm info", 0));

	return 0;
}
CMD_TEST(cmd_test_wolftpm_info, UTF_CONSOLE);

/**
 * Test wolfTPM state command
 *
 * Display TPM internal state
 */
static int cmd_test_wolftpm_state(struct unit_test_state *uts)
{
	/* First autostart to ensure TPM is ready */
	ut_assertok(run_command("wolftpm autostart", 0));

	/* Get TPM state */
	ut_assertok(run_command("wolftpm state", 0));

	return 0;
}
CMD_TEST(cmd_test_wolftpm_state, UTF_CONSOLE);

/**
 * Cleanup test - ensure TPM is cleared after tests
 */
static int cmd_test_wolftpm_cleanup(struct unit_test_state *uts)
{
	/* Clear TPM to reset any passwords or test state */
	run_command("wolftpm autostart", 0);
	run_command("wolftpm clear TPM2_RH_LOCKOUT", 0);
	run_command("wolftpm clear TPM2_RH_PLATFORM", 0);

	return 0;
}
CMD_TEST(cmd_test_wolftpm_cleanup, UTF_CONSOLE);
