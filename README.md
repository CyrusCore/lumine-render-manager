# Lumine Render Manager

<p align="center">
  <img src="assets/logo.png" width="300" alt="Lumine Logo">
</p>

![Lumine Render Manager](https://img.shields.io/badge/Render-Blender-orange?style=for-the-badge&logo=blender)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-blue?style=for-the-badge&logo=qt)
![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python)

**Lumine Render Manager** is a high-end, professional desktop utility designed to automate and monitor Blender rendering workflows. Featuring a stunning **Glassmorphic** design and real-time notification system, it allows 3D artists to manage background renders with style and efficiency.

---

## ✨ Features

- **Next-Gen Glassmorphism**: A sleek, translucent UI with mesh gradient backgrounds, vibrant highlights, and rounded aesthetics.
- **Background Rendering**: Execute Blender renders in a secondary thread, keeping your UI responsive at all times.
- **Custom Themes**: Choose from 5 premium color palettes: **Purple** (Default), **Blue**, **Pink**, **Green**, and **Orange**.
- **Real-time Monitoring**:
  - Live console output with high-contrast log coloring.
  - Smooth progress bar with accurate frame-by-frame tracking and **ETA Calculation**.
- **Telegram Integration**: Get notified on your phone when renders are completed, failed, or aborted.
- **Smart Persistence**: Remembers all your settings including Blender path, render parameters, and theme preferences.
- **Drag & Drop Support**: Quickly load `.blend` files by dropping them into the window.
- **Modular Architecture**: Cleanly separated code for settings, worker threads, and UI.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Blender 4.0+** (Ensure `blender.exe` is accessible)
- **PyQt6**

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/CyrusCore/lumine-render-manager.git
   cd lumine-render-manager
   ```

2. **Install dependencies**:
   ```bash
   pip install PyQt6
   ```

3. **Run the application**:
   ```bash
   python render_manager.py
   ```

---

## 🛠 Configuration

1. **Blender Path**: Set the location of your `blender.exe`.
2. **Project File**: Select the `.blend` file you wish to render.
3. **Telegram (Optional)**: 
   - Open **Settings** (Gear icon ⚙️).
   - Enter your `Bot Token` and `Chat ID`.
   - Click "Save All Settings".
   - Use "Test Telegram Connection" to verify.

---


## 📝 About the Developer

Created by **BramszsVisual**.  
Designed for 3D animators and render farms looking for a clean, modern, and automated solution for Blender output management.

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.

---

> [!TIP]
> Use the **Abort Render** button safely at any time to kill the background process without losing your progress logs.
