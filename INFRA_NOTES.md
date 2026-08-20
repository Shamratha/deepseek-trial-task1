# Infrastructure notes

- Setup target: macOS, Python 3.11+.
- Pinned main experimental model: `deepseek/deepseek-v4-flash-0731`.
- Installed CLI help is checked at preflight; unsupported isolation flags fail closed.
- The native control rejects proxy variables and custom-provider configuration.
- The vision daemon binds to loopback and owns the vision credential. Workspace agents receive only a local helper URL.
- Raw output is never rewritten. Missing telemetry remains JSON `null`.
- Check 3 remains intentionally blocked until the external team lock is complete.
- Local tests use synthetic files and subprocess fixtures only; they make no model calls.

