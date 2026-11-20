-- Fix blank white WebKitGTK views (BambuStudio, OrcaSlicer, Tauri, etc.) on NVIDIA + Wayland
hl.env("WEBKIT_DISABLE_DMABUF_RENDERER", "1")
hl.env("SSL_CERT_FILE", "/etc/ssl/certs/ca-certificates.crt")
