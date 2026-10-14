# Asset maintenance

These tools maintain the generated assets shipped in `workshop/`; they are not part of add-in startup or the release archive.

- `build-preview-profiles.py` derives 2D outlines from `source/original-profiles.json`.
- `build-command-icon.py` and `build-styled-catalog-art.py` regenerate icons and styled model captures.
- `prepare-model-illustrations.py` captures actual models in Fusion.
- `prepare-bin-presets.py` rebuilds standard interfaces using the retained legacy `lib/` geometry helpers and `config.py`.
- `prepare-generator-presets.py` uses the captured socket and section fixtures in `source/`.
- `parameterize-clasp.py` and `prepare-cartridge-template.py` are Fusion-only template maintenance tools requiring their documented disposable development context. They are not unattended build scripts.

`source/` preserves original captured geometry and the clasp reference/parameter map needed for provenance and maintenance. Scripts requiring Fusion run through its MCP/API in disposable documents. Some development scripts retain machine-specific paths and must be configured before use.

Historical benchmark results, prototype launchers, generated screenshots, and one-off cartridge jobs are retired from the source tree; Git history retains them.
