#!/usr/bin/env bash
# Unified Howdy IR face-unlock setup (packages + IR camera/cv2 config + howdy-gtk popup stub + lock UI).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FEATS="${DOTSYNC_FEATURES:-all}"

has_feat() {
    [ "$FEATS" = "all" ] && return 0
    case ",$FEATS," in
        *,"$1",*) return 0 ;;
        *) return 1 ;;
    esac
}

if has_feat "howdy-packages"; then
    bash "$REPO/items/howdy-packages/install.sh"
fi
if has_feat "howdy-config"; then
    sudo bash "$REPO/items/howdy-config/setup.sh"
fi
if has_feat "howdy-stub"; then
    install -Dm755 "$REPO/items/howdy-stub/howdy-gtk" "$HOME/.local/bin/howdy-gtk"
fi
if has_feat "howdy-lock" && [ -f "$REPO/items/qs-custom/patch-lock-howdy.py" ]; then
    python3 "$REPO/items/qs-custom/patch-lock-howdy.py" || true
fi

echo "✓ Howdy IR yüz tanıma kurulumu tamamlandı."
