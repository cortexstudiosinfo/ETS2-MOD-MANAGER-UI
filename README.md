# ETS2 Mod Manager

A modern, fast, and feature-rich mod manager for Euro Truck Simulator 2, built with Python.

## Features
- Deep integration with `profile.sii` load orders (no manual file editing).
- Automatic `.sii` decryption via bundled tools (downloaded on runtime).
- Supports local `mod/` folder and Steam Workshop mods.
- Cloud sharing using Firebase.

## Setup for Development
1. Double-click `run.cmd` to automatically configure a Virtual Environment, install dependencies, and launch the app.
2. If Firebase is needed, read below.

## Firebase Setup (Cloud Presets)
1. Go to Firebase Console -> Project Settings -> Service Accounts.
2. Generate a new private key JSON.
3. Place the JSON file in the project root and name it exactly: `firebase_credentials.json`.
4. Ensure your Firestore database is created with a `presets` collection.

## Compilation to .EXE
Double-click `build.cmd` to build a production bundle.
The compiled `.exe` will be located inside `dist/ETS2ModManager/`.
