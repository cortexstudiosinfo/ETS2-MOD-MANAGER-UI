<div align="center">

<img src="Manager.png" alt="Truck Manager logo" width="120">

# Truck Manager v4.0.0

<img width="1332" height="798" alt="Truck Manager v4.0.0 interface" src="https://github.com/user-attachments/assets/983cae33-91c0-4f29-bb99-956ce2452b29" />

### Comparte y gestiona el orden de tus mods de ETS2 y ATS de forma más fácil.

[![Version](https://img.shields.io/badge/Version-v4.0.0-60a5fa?style=for-the-badge)]()
[![Platform](https://img.shields.io/badge/Platform-Windows-111827?style=for-the-badge)]()

[GitHub](https://github.com/cortexstudiosinfo/ETS2-MOD-MANAGER-UI) | [Discord](https://discord.gg/UUfsc89HNv) | [Email](mailto:cortex.studios.info@gmail.com)

</div>

---

## Español

Truck Manager nace con un objetivo principal: hacer que compartir el orden de mods de Euro Truck Simulator 2 y American Truck Simulator sea mucho más sencillo.

En vez de explicar a otra persona qué mods van primero, cuáles van después o tener que tocar archivos manualmente, puedes preparar tu orden de carga desde la aplicación, guardarlo como preset y compartirlo de una forma más clara.

La aplicación está pensada para jugadores que utilizan muchos mods y quieren organizar sus perfiles sin complicarse.

## Objetivo principal

* Gestionar el orden de carga de mods de ETS2 y ATS.
* Guardar configuraciones como presets.
* Compartir presets para que otros usuarios puedan utilizar el mismo orden.
* Evitar modificar manualmente los archivos del perfil.
* Hacer que la organización de mods sea más rápida, visual y fácil de entender.

## Qué puedes hacer

* Elegir entre Euro Truck Simulator 2 y American Truck Simulator.
* Detectar perfiles locales y perfiles de Steam.
* Ver los mods instalados.
* Ordenar los mods activos de forma visual.
* Guardar el orden directamente en el perfil del juego.
* Crear, importar, renombrar y eliminar presets.
* Compartir y descargar presets mediante la base de datos.
* Utilizar ajustes separados para ETS2 y ATS.
* Configurar rutas manualmente para instalaciones personalizadas o configuraciones con `-homedir`.

## Descarga y base de datos

Los archivos de código fuente publicados en este repositorio no incluyen credenciales privadas ni archivos sensibles.

Sin embargo, el archivo `.exe` oficial disponible en la sección **Releases** ya está preparado y configurado para conectarse a la base de datos de Truck Manager.

Los usuarios que descarguen el `.exe` oficial pueden utilizar tranquilamente las funciones online, como compartir y descargar presets, sin tener que crear un proyecto de Firebase ni configurar credenciales manualmente.

### Para usuarios normales

1. Entra en la sección **Releases** del repositorio.
2. Descarga el archivo `.exe` o el paquete oficial de Truck Manager.
3. Abre la aplicación.
4. Utiliza las funciones locales y online normalmente.

No necesitas instalar Python, configurar Firebase ni añadir ningún archivo de credenciales.

### Para desarrolladores

Si descargas únicamente el código fuente y quieres ejecutarlo o modificarlo por tu cuenta, las credenciales privadas no estarán incluidas por motivos de seguridad.

En ese caso, tendrás que configurar tu propia conexión a Firebase:

1. Crea un proyecto en Firebase.
2. Activa Firestore Database.
3. Crea una cuenta de servicio.
4. Descarga sus credenciales.
5. Renombra el archivo a `firebase_credentials.json`.
6. Colócalo junto a `main.py`.
7. No publiques ni subas ese archivo a GitHub.

> Se recomienda a los usuarios descargar únicamente las versiones oficiales publicadas en la sección **Releases** de este repositorio.

---

## English

Truck Manager was created with one main goal: to make sharing mod load orders for Euro Truck Simulator 2 and American Truck Simulator much easier.

Instead of explaining which mods go first, which ones go later or manually editing profile files, you can prepare your load order inside the application, save it as a preset and share it in a clearer way.

The application is designed for players who use many mods and want to organize their profiles without making things complicated.

## Main Goal

* Manage ETS2 and ATS mod load orders.
* Save configurations as presets.
* Share presets so other users can use the same load order.
* Avoid editing profile files manually.
* Make mod organization faster, visual and easier to understand.

## What You Can Do

* Choose between Euro Truck Simulator 2 and American Truck Simulator.
* Detect local and Steam profiles.
* View installed mods.
* Sort active mods visually.
* Save the load order directly to the game profile.
* Create, import, rename and delete presets.
* Share and download presets through the database.
* Use separate settings for ETS2 and ATS.
* Configure manual paths for custom installations or `-homedir` setups.

## Download and Database Access

The source-code files published in this repository do not include private credentials or sensitive files.

However, the official `.exe` available in the **Releases** section is already prepared and configured to connect to the Truck Manager database.

Users who download the official `.exe` can safely use online features, including sharing and downloading presets, without creating a Firebase project or manually configuring credentials.

### For Regular Users

1. Open the repository's **Releases** section.
2. Download the official Truck Manager `.exe` or release package.
3. Open the application.
4. Use its local and online features normally.

You do not need to install Python, configure Firebase or add any credential files.

### For Developers

If you download only the source code and want to run or modify it yourself, private credentials are not included for security reasons.

In that case, you will need to configure your own Firebase connection:

1. Create a Firebase project.
2. Enable Firestore Database.
3. Create a service account.
4. Download its credentials.
5. Rename the file to `firebase_credentials.json`.
6. Place it next to `main.py`.
7. Never publish or upload this file to GitHub.

> Users are advised to download only official versions published in the **Releases** section of this repository.

---

<div align="center">

**Truck Manager v4.0.0**

GitHub: [cortexstudiosinfo/ETS2-MOD-MANAGER-UI](https://github.com/cortexstudiosinfo/ETS2-MOD-MANAGER-UI)
Discord: [discord.gg/UUfsc89HNv](https://discord.gg/UUfsc89HNv)
Email: [cortex.studios.info@gmail.com](mailto:cortex.studios.info@gmail.com)

</div>
