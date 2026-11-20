# illogical-impulse-kaan-custom

Personal customization suite and declarative installer (`dotsync`) for **end-4 / illogical-impulse** on **Hyprland + Quickshell (Arch / CachyOS)**.

## Quick Install

```bash
gh api repos/KaanAlper/illogical-impulse-kaan-custom/contents/install.sh -H "Accept: application/vnd.github.raw" | bash
```

Or clone manually:

```bash
gh auth login
gh repo clone KaanAlper/illogical-impulse-kaan-custom ~/kaan-dots
~/kaan-dots/bootstrap.sh
```

`dotsync` opens a Quickshell GUI where every bundle can be expanded (`▸` / `▾`) to select or deselect individual sub-features, plus a collapsible **Already installed** section at the bottom.

### Useful Commands

```bash
dotsync setup              # Open the full installer UI (including previously declined items)
dotsync status --sync      # Sync manifest from GitHub and print JSON status
dotsync apply <id...>      # Install specific items from CLI
```

---

## Repository Structure

```text
illogical-impulse-kaan-custom/
├── bootstrap.sh                         # Installs ~/.local/bin/dotsync and local repo cache
├── install.sh                           # One-line bootstrap + GUI launcher
├── manifest.json                        # Declarative catalog of items, sub-features, and checks
├── dotsync/
│   ├── dotsync.py                       # Core engine (status, file/pkg checks, terminal batching, DOTSYNC_FEATURES)
│   └── ui/
│       └── shell.qml                    # Quickshell GUI with 2-level expandable feature selection
├── items/
│   ├── qs-custom/                       # Quickshell ii widgets, patches, scripts, and translations
│   │   ├── apply.sh                     # Idempotent patcher (respects DOTSYNC_FEATURES)
│   │   ├── patch-agy-ai.py              # Patches Ai, SidebarLeft, Settings, Config, Workspaces, AppSearch
│   │   ├── patch-everything.py          # Patches Overview & Search for Everything (#) file search
│   │   ├── patch-lock-howdy.py          # Patches LockContext & LockSurface for Howdy face unlock
│   │   ├── AppVolumeMixer.qml           # Per-app PipeWire volume mixer bar popup
│   │   ├── AudioMonoToggle.qml          # Mono/Stereo downmix toggle bar button
│   │   ├── AudioOutputSwitcher.qml      # Audio output sink switcher bar popup
│   │   ├── SleepInhibitToggle.qml       # Sleep/idle inhibit toggle bar button
│   │   ├── ScreensaverOverlay.qml       # Per-monitor Wayland overlay (DVD, Matrix, Starfield, Mystify, XANA, Color, Custom)
│   │   ├── ScreensaverConfig.qml        # Settings -> Screensaver page (per-monitor, color palette, custom media)
│   │   ├── apply-screensaver-idle.py    # Generates ~/.config/hypr/hypridle.conf from config.json
│   │   ├── apply-plymouth-logo.sh       # Updates Plymouth xana watermark & rebuilds initrd
│   │   ├── AgyModelPicker.qml           # Antigravity CLI model & effort selector
│   │   ├── AgyConfigPicker.qml          # Antigravity CLI config & slash command picker
│   │   ├── CliChatPanel.qml             # Native Claude & Codex CLI chat tabs
│   │   ├── CliSlashList.qml             # Shared slash-command popup for AI & Anime tabs
│   │   ├── AnimeImageViewer.qml         # Floating full-size image viewer for Anime tab
│   │   ├── FileSearch.qml               # Everything (#) & All Apps (!) search backend
│   │   ├── EverythingToolbar.qml        # Sort & file-type filter toolbar in Overview
│   │   ├── EverythingMenus.qml          # Context menus for Everything results
│   │   ├── translations/                # 14-language JSON overlays merged into illogical-impulse/translations
│   │   └── ...                          # Helper scripts (fetch-agy-*, fetch-cli-meta.py, everything-*, etc.)
│   ├── hypr-custom/                     # Installed to ~/.config/hypr/custom (existing files preserved)
│   │   ├── alttab/                      # Custom Alt+Tab window switcher (shell.qml)
│   │   ├── bootsplash/                  # Custom Plymouth / boot splash watermark assets
│   │   ├── scripts/                     # Wallpaper restore helper
│   │   ├── keybinds.lua                 # Feature keybinds (Alt+Tab, Everything, cross-monitor workspaces, Print)
│   │   ├── rules.lua & rules.conf       # Floating / window rules (Flameshot, Everything, etc.)
│   │   ├── hypridle.conf                # Idle listener configuration
│   │   └── env.lua, execs.lua, general.lua, variables.lua
│   ├── flameshot/                       # Installs flameshot + Wayland-compatible ~/.config/flameshot/flameshot.ini
│   ├── fish-config/                     # Installed to ~/.config/fish (Bash compatibility: $?, !!, b, bp)
│   ├── howdy/                           # Unified Howdy IR face unlock installer
│   ├── howdy-packages/                  # Builds/installs python-dlib (CPU) and howdy-git
│   ├── howdy-config/                    # Detects IR camera, configures /etc/howdy/config.ini, fixes cv2
│   ├── howdy-stub/                      # Installs ~/.local/bin/howdy-gtk to suppress popup windows
│   ├── autologin-lock/                  # Optional greetd tty1 autologin directly into ii lock screen
│   └── plymouth-xana/                   # Custom Plymouth xana theme assets
└── tests/
    └── test_dotsync.py                  # Unit tests for dotsync manifest & state logic
```

---

## Items & Sub-Features

### 1. `qs-custom` — Quickshell Customizations
Copies assets to `~/.config/quickshell-custom` and runs `apply.sh` (respecting `DOTSYNC_FEATURES`):

- **`bar-widgets`** *(expandable)*:
  - **`app-volume-mixer`**: Installs `AppVolumeMixer.qml` + `pw-app-ancestry.py` and adds a per-app volume mixer popup to `BarContent.qml`.
  - **`audio-mono-toggle`**: Installs `AudioMonoToggle.qml` + `audio-mono-toggle.sh` for one-click Mono/Stereo output toggling.
  - **`audio-output-switcher`**: Installs `AudioOutputSwitcher.qml` for quick default sink switching from the bar.
  - **`sleep-inhibit-toggle`**: Installs `SleepInhibitToggle.qml` + `sleep-inhibit-toggle.sh` to hold a `systemd-inhibit` lock on idle/lid-close.
- **`screensaver`**:
  - Installs `ScreensaverOverlay.qml`, `ScreensaverConfig.qml`, `xana-logo.png`, `apply-screensaver-idle.py`, registers the **Screensaver** settings page, and merges its 14-language translations.
  - Supports **DVD**, **Matrix**, **Starfield**, **Mystify**, **XANA**, **Solid Color** (with swatches + `ColorDialog`), and **Custom** media (image, GIF, video, Windows `.scr`), **per-monitor overrides**, and **deferred session lock** (keeps screensaver running until mouse/keyboard input, then immediately shows the lock screen).
- **`lock-power`**:
  - Adds **General -> Lock** in Settings (`enableLock`, `enableDpms`, `enableSuspend` with minute timeouts), integrates `apply-screensaver-idle.py` with `hypridle.conf`, installs `apply-plymouth-logo.sh` (conditional Plymouth `xana` watermark picker), and merges its 14-language translations.
- **`ai-sidebar`**:
  - Replaces/extends `SidebarLeft` with **`Claude | Agy | Codex | Anime`** tabs (`CliChatPanel.qml`, `AgyModelPicker.qml`, `AgyConfigPicker.qml`, `AnimeImageViewer.qml`, `fetch-agy-*`, `fetch-cli-meta.py`), prevents background `agy` fetchers from opening browser OAuth at boot, falls back `Ai.getModel()` cleanly to show the Sign-in banner when logged out, and merges its 14-language translations.
- **`everything-search`**:
  - Installs `FileSearch.qml`, `EverythingToolbar.qml`, `EverythingMenus.qml`, `everything-query.py`, `everything-update.sh`, enables the `everything-index.timer` systemd user unit (`plocate`), and wires `Super+B` (`#` file search) and `Super+P` (`!` all apps A-Z).
- **`workspace-split`**:
  - Patches `Config.qml`, `BarConfig.qml`, and `Workspaces.qml` for per-monitor workspace splitting, dims the active workspace indicator on unfocused monitors, and pairs with `Ctrl+Super+Left/Right` (+`Shift`) cross-monitor navigation.
- **`icon-cache`**:
  - Maps `zen` -> `zen-browser` in `AppSearch.qml`, symlinks Zen Browser and ArtCraft icons into `~/.local/share/icons/hicolor/128x128/apps/`, and refreshes `gtk-update-icon-cache`.

### 2. `hypr-custom` — Hyprland Customizations
Copies missing files into `~/.config/hypr/custom` (requires `flameshot`):
- **`rules`**: `rules.lua` & `rules.conf` (floating/window rules).
- **`alttab`**: `alttab/` custom Alt+Tab window switcher + `Alt+Tab` / `Alt+Shift+Tab` binds.
- **`hypridle`**: `hypridle.conf` idle listener config.
- **`bootsplash`**: `bootsplash/` watermark assets.
- **`execs-env`**: `execs.lua`, `env.lua`, `general.lua`, `variables.lua`.

### 3. `flameshot`
- Installs `flameshot` (`sudo`/`pkexec`/`paru`), writes `~/.config/flameshot/flameshot.ini` for Wayland, and pairs with the `Print` keybind.

### 4. `fish-settings`
- Copies `~/.config/fish/conf.d/` helpers providing Bash compatibility (`$?` -> `$status`, `!!`, `b '...'`, `bp`).

### 5. `howdy` — Infrared Face Unlock *(terminal, sudo)*
Unified installer (`items/howdy/install.sh`, respects `DOTSYNC_FEATURES`):
- **`howdy-packages`**: Builds/installs `python-dlib` (CPU) and `howdy-git`.
- **`howdy-config`**: Detects the IR camera, updates `/etc/howdy/config.ini`, and patches `/usr/lib/howdy/cv2`.
- **`howdy-stub`**: Installs `~/.local/bin/howdy-gtk` to suppress floating auth popups.
- **`howdy-lock`**: Runs `patch-lock-howdy.py` to add face-scan status/retry UI to the `ii` lock screen.

### 6. `autologin-lock` *(optional, default off, terminal, sudo)*
- Configures `greetd` tty1 autologin directly into Hyprland + `ii` lock screen (`Super+L`).

### 7. `default-file-manager`
- Sets Dolphin (`org.kde.dolphin.desktop`) as default handler for `inode/directory`.

### 8. `agy-cli` *(terminal)*
- Installs `antigravity` CLI via `paru` if `~/.local/bin/agy` is not present.
