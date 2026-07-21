<div align="center">

<img src="Manager.png" alt="Truck Manager logo" width="120">

# Truck Manager

### ES: Gestor moderno de mods, perfiles y presets para Euro Truck Simulator 2 y American Truck Simulator.
### EN: A modern mod, profile and preset manager for Euro Truck Simulator 2 and American Truck Simulator.

[![Status](https://img.shields.io/badge/Status-Active-22c55e?style=for-the-badge)]()
[![Version](https://img.shields.io/badge/Version-v4.0.0-60a5fa?style=for-the-badge)]()
[![Platform](https://img.shields.io/badge/Platform-Windows-111827?style=for-the-badge)]()

[GitHub](https://github.com/cortexstudiosinfo/ETS2-MOD-MANAGER-UI) | [Discord](https://discord.gg/UUfsc89HNv) | [Email](mailto:cortex.studios.info@gmail.com)

</div>

---

## ES | Que es

Truck Manager es una interfaz visual para gestionar perfiles, mods, orden de carga y presets de ETS2 y ATS desde una app limpia, rapida y facil de entender.

La idea es que no tengas que tocar archivos manualmente: eliges juego, eliges perfil, revisas tus mods y guardas el orden directamente en el perfil del juego.

## EN | What It Is

Truck Manager is a visual interface for managing profiles, mods, load order and presets for ETS2 and ATS in a clean, fast and easy-to-understand app.

The goal is to avoid manual file editing: choose the game, choose the profile, review your mods and save the load order directly into the game profile.

---

## ES | Funciones principales

| Funcion | Descripcion |
|---|---|
| Seleccion de juego | Permite trabajar con Euro Truck Simulator 2 o American Truck Simulator. |
| Deteccion de perfiles | Encuentra perfiles locales y perfiles de Steam automaticamente. |
| Escaneo de mods | Lee mods descargados y mods de Steam Workshop. |
| Vista previa | Muestra informacion visual de los mods cuando esta disponible. |
| Orden de carga | Permite ordenar mods de forma visual y guardar el resultado en el perfil. |
| Presets | Guarda, importa, renombra y elimina presets de orden de carga. |
| Ajustes por juego | Cada juego tiene su propia configuracion de rutas y carpetas. |
| Editor de perfil | Permite revisar y editar datos utiles del perfil y de la partida. |
| Modo claro/oscuro | Interfaz adaptable al estilo que prefieras. |
| Espanol e ingles | La interfaz puede usarse en ambos idiomas. |

## EN | Main Features

| Feature | Description |
|---|---|
| Game selection | Work with Euro Truck Simulator 2 or American Truck Simulator. |
| Profile detection | Automatically finds local and Steam profiles. |
| Mod scanning | Reads downloaded mods and Steam Workshop mods. |
| Preview support | Shows visual mod information when available. |
| Load order | Sort mods visually and save the result into the selected profile. |
| Presets | Save, import, rename and delete load order presets. |
| Per-game settings | Each game keeps its own path and folder configuration. |
| Profile editor | Review and edit useful profile and save-game values. |
| Light/Dark mode | Interface adapts to your preferred style. |
| Spanish and English | The interface can be used in both languages. |

---

## ES | Como usarlo

1. Abre Truck Manager.
2. Elige ETS2 o ATS.
3. Selecciona el perfil que quieres gestionar.
4. Escanea tus mods.
5. Ordena los mods activos.
6. Guarda el orden en el juego.
7. Usa presets para guardar o compartir configuraciones.

## EN | How To Use It

1. Open Truck Manager.
2. Choose ETS2 or ATS.
3. Select the profile you want to manage.
4. Scan your mods.
5. Sort active mods.
6. Save the load order into the game.
7. Use presets to save or share configurations.

---

## ES | Credenciales y funciones cloud

La version publica no incluye credenciales privadas. Esto es intencionado para que el proyecto pueda subirse a GitHub de forma segura.

Truck Manager puede funcionar sin credenciales, pero las funciones cloud como compartir o descargar presets online necesitan Firebase configurado.

Para activar Firebase en tu copia privada:

1. Crea un proyecto en Firebase.
2. Activa Firestore Database en ese proyecto.
3. Crea una cuenta de servicio desde la configuracion del proyecto.
4. Descarga el archivo de credenciales de esa cuenta de servicio.
5. Renombra ese archivo como `firebase_credentials.json`.
6. Colocalo en la carpeta principal de Truck Manager, junto a `main.py`.
7. Mantén ese archivo siempre fuera de GitHub. Ya esta incluido en `.gitignore`.

Si el archivo no existe, la app simplemente desactiva las funciones cloud y sigue funcionando para la gestion local de mods y perfiles.

## EN | Credentials And Cloud Features

The public version does not include private credentials. This is intentional so the project can be published safely on GitHub.

Truck Manager can run without credentials, but cloud features such as sharing or downloading online presets require Firebase to be configured.

To enable Firebase in your private copy:

1. Create a Firebase project.
2. Enable Firestore Database in that project.
3. Create a service account from the project settings.
4. Download the credentials file for that service account.
5. Rename that file to `firebase_credentials.json`.
6. Place it in the main Truck Manager folder, next to `main.py`.
7. Keep that file out of GitHub at all times. It is already included in `.gitignore`.

If the file does not exist, the app simply disables cloud features and keeps working for local mod and profile management.

---

## ES | Ajustes

Truck Manager puede detectar carpetas automaticamente, pero tambien permite configurar rutas manuales si usas una instalacion especial, un directorio personalizado o parametros como homedir.

Los ajustes son independientes por juego. Si estas en ETS2, veras ajustes de ETS2. Si estas en ATS, veras ajustes de ATS.

## EN | Settings

Truck Manager can detect folders automatically, but it also allows manual paths if you use a custom installation, a custom directory or homedir-style setups.

Settings are independent per game. If you are inside ETS2, you see ETS2 settings. If you are inside ATS, you see ATS settings.

---

## ES | Requisitos

- Windows.
- Euro Truck Simulator 2 o American Truck Simulator instalado.
- Un perfil local del juego ya creado.
- Python y las dependencias del proyecto si se ejecuta desde el codigo fuente.
- Conexion a internet para funciones en la nube o contenido remoto.

## EN | Requirements

- Windows.
- Euro Truck Simulator 2 or American Truck Simulator installed.
- An existing local game profile.
- Python and the project dependencies when running from source.
- Internet connection for cloud features or remote content.

---

## ES | Contacto

- GitHub: [cortexstudiosinfo/ETS2-MOD-MANAGER-UI](https://github.com/cortexstudiosinfo/ETS2-MOD-MANAGER-UI)
- Discord: [discord.gg/UUfsc89HNv](https://discord.gg/UUfsc89HNv)
- Email: [cortex.studios.info@gmail.com](mailto:cortex.studios.info@gmail.com)

## EN | Contact

- GitHub: [cortexstudiosinfo/ETS2-MOD-MANAGER-UI](https://github.com/cortexstudiosinfo/ETS2-MOD-MANAGER-UI)
- Discord: [discord.gg/UUfsc89HNv](https://discord.gg/UUfsc89HNv)
- Email: [cortex.studios.info@gmail.com](mailto:cortex.studios.info@gmail.com)

---

<div align="center">

**Truck Manager v4.0.0**

ES: Creado para hacer la gestion de mods mas clara, rapida y comoda.

EN: Built to make mod management cleaner, faster and easier.

</div>
