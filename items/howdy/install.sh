#!/usr/bin/env bash
# Unified Howdy IR face-unlock setup (packages + IR camera/cv2 config + howdy-gtk popup stub).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

bash "$REPO/items/howdy-packages/install.sh"
sudo bash "$REPO/items/howdy-config/setup.sh"
install -Dm755 "$REPO/items/howdy-stub/howdy-gtk" "$HOME/.local/bin/howdy-gtk"

echo "✓ Howdy IR yüz tanıma kurulumu tamamlandı."
