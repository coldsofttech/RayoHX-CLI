; NSIS installer for the RayoHX command line (rayohx.exe), built by scripts/build.py --setup into
; rayohx-cli-<version>-windows-x64-setup.exe. Windows only.
;
; The behavior is in common.nsh (pages, per-user or all-users install, PATH, silent use,
; uninstaller). This file holds only what is specific to the command line; everything else (GUID,
; APP_NAME, APP_VERSION, STAGE_DIR, CLI_EXE, INSTALL_DIR, ...) is passed with /D by scripts/build.py,
; see the list in common.nsh.

!include "${__FILEDIR__}\common.nsh"
