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
│   ├── live-wallpaper              # Wallpaper group (each part selectable on its own)
│   │   ├── live-video              # Native live (video/GIF) wallpapers via QtMultimedia + Live Store (motionbgs.com);
│   │   │                           # installs ffmpeg, qt6-multimedia-ffmpeg and jq
│   │   └── wallpaper-settings      # Settings -> Wallpaper page, per-monitor wallpapers, drag-to-reorder monitor
│   │                               # pills, main-monitor star + 14-lang translations
│   ├── screensaver                 # Screensaver (DVD, Matrix, Starfield, Mystify, XANA, Color, Custom/GIF/Video/.scr),
│   │                               # per-monitor settings, deferred lock (keeps running until input), + 14-lang translations
│   ├── lock-power                  # Settings -> General -> Lock (idle lock, DPMS, Suspend toggles/timeouts,
│   │                               # conditional Plymouth xana logo picker), hypridle sync, + 14-lang translations
│   ├── startup-apps                # Settings -> General -> Startup Apps (responsive scrollable grid for autostart & Hyprland execs)
│   ├── ai-sidebar                  # Left sidebar AI (Claude | Agy | Codex | Anime), + 14-lang translations
│   │   ├── ai-panel                # The tabs, model/effort & config pickers, floating anime image viewer
│   │   ├── cli-agy                 # Installs the Antigravity CLI (~/.local/bin/agy)
│   │   ├── cli-claude              # Installs claude-code
│   │   └── cli-codex               # Installs openai-codex
│   │                               # (CLIs you skip are offered inside Super+A when you open that tab)
│   ├── everything-search           # Everything (#) file search via plocate + systemd timer, sort/filter toolbar,
│   │                               # Super+B (files #) and Super+P (all apps A-Z !)
│   ├── workspace-split             # Per-monitor workspace splitting in Bar Settings, dims unfocused monitor
│   │                               # workspace indicator, Ctrl+Super+Left/Right (+Shift) cross-monitor navigation
│   └── icon-cache                  # Fixes Zen Browser & ArtCraft icons and refreshes hicolor icon-theme.cache
│
├── hypr-custom — Hyprland custom configuration (~/.config/hypr/custom, non-destructive)
│   ├── rules                       # Window & floating rules (Flameshot, Everything, etc.)
│   ├── alttab                      # Custom Alt+Tab window switcher + Alt+Tab / Alt+Shift+Tab keybinds
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
└── grub-theme                      # (Terminal, sudo) Installs Marathon-NewCascadia GRUB theme & /etc/default/grub settings
```
