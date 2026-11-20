# illogical-impulse-kaan-custom

Personal customization suite and declarative installer (`dotsync`) for **end-4 / illogical-impulse** on **Hyprland + Quickshell (Arch / CachyOS)**.

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/KaanAlper/illogical-impulse-kaan-custom/main/install.sh | bash
```

Or clone and bootstrap manually:

```bash
git clone https://github.com/KaanAlper/illogical-impulse-kaan-custom.git ~/kaan-dots
~/kaan-dots/bootstrap.sh
```

On boot/setup, `dotsync` opens a GUI where each bundle can be expanded (`▸` / `▾`) to pick individual sub-features, along with a collapsible **Already installed** section at the bottom.

### CLI Commands

```bash
dotsync setup              # Open the full installer UI (including declined items)
dotsync status --sync      # Sync from GitHub and print JSON status
dotsync apply <id...>      # Install specific items from CLI
```

---

## Feature Tree (What You Can Select & What Each Item Does)

```text
illogical-impulse-kaan-custom
├── qs-custom — Quickshell ii customizations
│   ├── bar-widgets
│   │   ├── app-volume-mixer        # Per-app PipeWire volume mixer popup in the top bar
│   │   ├── audio-mono-toggle       # One-click Mono/Stereo audio downmix toggle in the bar
│   │   ├── audio-output-switcher   # Quick audio output device switcher popup in the bar
│   │   └── sleep-inhibit-toggle    # Top bar toggle to inhibit idle sleep, DPMS, and lid-close
│   ├── screensaver                 # Screensaver (DVD, Matrix, Starfield, Mystify, XANA, Color, Custom/GIF/Video/.scr),
│   │                               # per-monitor settings, deferred lock (keeps running until input), + 14-lang translations
│   ├── lock-power                  # Settings -> General -> Lock (idle lock, DPMS, Suspend toggles/timeouts,
│   │                               # conditional Plymouth xana logo picker), hypridle sync, + 14-lang translations
│   ├── ai-sidebar                  # Left sidebar tabs: Claude | Agy | Codex | Anime, model/effort & config pickers,
│   │                               # floating anime image viewer, startup auth safety, + 14-lang translations
│   ├── everything-search           # Everything (#) file search via plocate + systemd timer, sort/filter toolbar,
│   │                               # Super+B (files #) and Super+P (all apps A-Z !)
│   ├── workspace-split             # Per-monitor workspace splitting in Bar Settings, dims unfocused monitor
│   │                               # workspace indicator, Ctrl+Super+Left/Right (+Shift) cross-monitor navigation
│   └── icon-cache                  # Fixes Zen Browser & ArtCraft icons and refreshes hicolor icon-theme.cache
│
├── hypr-custom — Hyprland custom configuration (~/.config/hypr/custom, non-destructive)
│   ├── rules                       # Window & floating rules (Flameshot, Everything, etc.)
│   ├── alttab                      # Custom Alt+Tab window switcher + Alt+Tab / Alt+Shift+Tab keybinds
│   ├── hypridle                    # Idle & lock listener defaults
│   ├── bootsplash                  # Custom boot splash watermark assets
│   └── execs-env                   # Startup execs, environment variables, general settings, and overrides
│
├── flameshot                       # Installs flameshot, configures Wayland-compatible INI, wires Print keybind
├── fish-settings                   # Bash compatibility helpers for Fish ($?, !!, b, bp)
│
├── howdy — Infrared (IR) face unlock (runs in terminal, requires sudo)
│   ├── howdy-packages              # Builds & installs python-dlib (CPU) and howdy-git
│   ├── howdy-config                # Detects IR camera, configures /etc/howdy/config.ini, fixes cv2
│   ├── howdy-stub                  # Installs ~/.local/bin/howdy-gtk to suppress floating auth popups
│   └── howdy-lock                  # Adds face-scan status & retry UI to the ii lock screen
│
├── autologin-lock                  # (Optional, default off, sudo) Disables display managers and sets greetd
│                                   # tty1 autologin directly into Hyprland + ii lock screen
├── default-file-manager            # Sets Dolphin as the default handler for folders (inode/directory)
└── agy-cli                         # (Terminal) Installs Antigravity CLI via paru if ~/.local/bin/agy is missing
```
