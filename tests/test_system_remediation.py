import subprocess

from videotrans.diagnostics.remediation import (
    KIND_OPEN_URL,
    KIND_WINGET,
    REMEDIATION_REGISTRY,
    STATUS_CANCELLED,
    STATUS_INSTALLER_FAILED,
    STATUS_LINK_OPENED,
    STATUS_NOT_ALLOWED,
    STATUS_POST_CHECK_FAILED,
    STATUS_REBOOT_REQUIRED,
    STATUS_SUCCESS,
    STATUS_UAC_DENIED,
    STATUS_UNAVAILABLE,
    _is_verified_https_url,
    execute_remediation,
    get_remediation,
)


def _completed(argv, returncode=0):
    return subprocess.CompletedProcess(list(argv), returncode, stdout="", stderr="")


def test_verified_remediation_urls_require_https_host_without_credentials():
    assert _is_verified_https_url("https://aka.ms/vs/17/release/vc_redist.x64.exe") is True
    assert _is_verified_https_url("http://aka.ms/vs/17/release/vc_redist.x64.exe") is False
    assert _is_verified_https_url("https://user:secret@example.com/installer.exe") is False
    assert _is_verified_https_url("https:///installer.exe") is False


def test_cancellation_has_no_external_effect():
    calls = []

    result = execute_remediation(
        "install_vc_runtime",
        confirmed=False,
        command_runner=lambda argv, timeout: calls.append((argv, timeout)),
        url_opener=lambda url: calls.append(url) or True,
        post_checker=lambda code: calls.append(code) or True,
        executable_finder=lambda name: calls.append(name) or "winget.exe",
    )

    assert result.status == STATUS_CANCELLED
    assert calls == []


def test_unknown_or_hostile_action_code_cannot_become_command_or_url():
    effects = []
    hostile = "install_vc_runtime && calc.exe --id Evil.Package"

    result = execute_remediation(
        hostile,
        confirmed=True,
        command_runner=lambda argv, timeout: effects.append(list(argv)),
        url_opener=lambda url: effects.append(url) or True,
        executable_finder=lambda name: effects.append(name) or "winget.exe",
    )

    assert result.status == STATUS_NOT_ALLOWED
    assert get_remediation(hostile) is None
    assert effects == []


def test_winget_uses_only_exact_allowlisted_package_and_safe_flags():
    commands = []
    checks = []

    def runner(argv, timeout):
        commands.append((list(argv), timeout))
        return _completed(argv)

    result = execute_remediation(
        "install_vc_runtime",
        confirmed=True,
        command_runner=runner,
        executable_finder=lambda name: r"C:\Windows\winget.exe",
        post_checker=lambda code: checks.append(code) or True,
    )

    assert result.status == STATUS_SUCCESS
    assert commands == [(
        [
            r"C:\Windows\winget.exe",
            "install",
            "--id",
            "Microsoft.VCRedist.2015+.x64",
            "--exact",
            "--source",
            "winget",
            "--disable-interactivity",
        ],
        900.0,
    )]
    assert checks == ["runtime.vc_redist"]
    flattened = commands[0][0]
    assert "--accept-source-agreements" not in flattened
    assert "--accept-package-agreements" not in flattened
    assert "--ignore-security-hash" not in flattened


def test_missing_winget_uses_only_verified_official_fallback():
    opened = []
    result = execute_remediation(
        "install_vc_runtime",
        confirmed=True,
        executable_finder=lambda name: None,
        url_opener=lambda url: opened.append(url) or True,
    )

    assert result.status == STATUS_LINK_OPENED
    assert opened == ["https://aka.ms/vs/17/release/vc_redist.x64.exe"]


def test_offline_or_unavailable_official_link_has_readable_failure():
    result = execute_remediation(
        "install_vc_runtime",
        confirmed=True,
        executable_finder=lambda name: None,
        url_opener=lambda url: False,
    )

    assert result.status == STATUS_UNAVAILABLE
    assert "network" in result.message.lower()


def test_uac_denial_reboot_and_installer_failure_are_distinct():
    finder = lambda name: "winget.exe"

    denied = execute_remediation(
        "install_vc_runtime",
        confirmed=True,
        executable_finder=finder,
        command_runner=lambda argv, timeout: _completed(argv, 1223),
    )
    reboot = execute_remediation(
        "install_vc_runtime",
        confirmed=True,
        executable_finder=finder,
        command_runner=lambda argv, timeout: _completed(argv, 3010),
    )
    failed = execute_remediation(
        "install_vc_runtime",
        confirmed=True,
        executable_finder=finder,
        command_runner=lambda argv, timeout: _completed(argv, 87),
    )

    assert denied.status == STATUS_UAC_DENIED
    assert reboot.status == STATUS_REBOOT_REQUIRED
    assert failed.status == STATUS_INSTALLER_FAILED


def test_zero_exit_code_is_not_success_without_post_condition():
    result = execute_remediation(
        "install_vc_runtime",
        confirmed=True,
        executable_finder=lambda name: "winget.exe",
        command_runner=lambda argv, timeout: _completed(argv),
        post_checker=lambda code: False,
    )

    assert result.status == STATUS_POST_CHECK_FAILED


def test_gpu_driver_actions_never_execute_winget_or_generic_shell():
    effects = []
    gpu_codes = {
        "use_cpu_or_install_nvidia_driver",
        "install_or_update_nvidia_driver",
        "retry_gpu_detection",
    }

    for code in gpu_codes:
        action = REMEDIATION_REGISTRY[code]
        assert action.kind == KIND_OPEN_URL
        assert action.kind != KIND_WINGET
        result = execute_remediation(
            code,
            confirmed=True,
            command_runner=lambda argv, timeout: effects.append(list(argv)),
            executable_finder=lambda name: effects.append(name) or "winget.exe",
            url_opener=lambda url: effects.append(url) or True,
        )
        assert result.status == STATUS_LINK_OPENED

    assert all(item == "https://www.nvidia.com/Download/index.aspx" for item in effects)


def test_structured_log_payload_contains_no_process_output_or_paths():
    result = execute_remediation(
        "install_vc_runtime",
        confirmed=True,
        executable_finder=lambda name: r"C:\Users\Alice\Secret\winget.exe",
        command_runner=lambda argv, timeout: subprocess.CompletedProcess(
            list(argv),
            87,
            stdout="token=super-secret",
            stderr=r"C:\Users\Alice\Private\installer.log",
        ),
    )
    payload = result.to_log_dict()

    assert set(payload) == {"action_code", "status", "method", "returncode"}
    assert "Alice" not in str(payload)
    assert "token" not in str(payload).lower()
