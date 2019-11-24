# Changelog

### 0.5.0
- Reworked zip exclusion list to control matches better
- Added build exe to clean, not just cpython prep
- Small improvements to arch handling, will add flag soon
- Re-enabled compressed builds
- Moved dep install to the prep CPython after copy, not before
- Fixed a bug in unpack and install on first launch, was running on every launch
- Created a flag file `requirements_installed.txt` to indicate completed installation
- Automated the build step in a new command, `python`, including checkout
- Added -o flag to control output name
