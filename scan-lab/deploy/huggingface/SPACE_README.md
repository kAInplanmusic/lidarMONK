---
title: lidarMONK private scan lab
emoji: 🔎
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
---

# lidarMONK

Private experimental RGB-D scan processing. Deployment requires a private Space, CPU Basic hardware, and a Space secret named `LIDARMONK_ACCESS_TOKEN` containing at least 32 random characters. Access the app through the Space while signed in; enter that secret in the app. Outputs and uploads are stored on ephemeral disk and disappear on restart or sleep. Download outputs promptly. Source repository: https://github.com/kAInplanmusic/lidarMONK.

Do not publish this as a public Space: its shared token and processing design are intended for a single owner, not multi-user public hosting. This is experimental software; no real iPhone capture or hosted deployment has been validated.
