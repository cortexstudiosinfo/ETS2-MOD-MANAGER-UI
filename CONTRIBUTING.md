# Contributing to Truck Manager

Thank you for your interest in contributing to **Truck Manager**.

Truck Manager is an open-source tool for managing **Euro Truck Simulator 2 (ETS2)** and **American Truck Simulator (ATS)** mod load orders, presets, profiles, and related features.

We welcome bug reports, feature ideas, documentation improvements, translations, code changes, and other contributions that can make Truck Manager better for the community.

> **Note:** This repository contains the open-source version of Truck Manager. The current v5.0.0 release is closed source; the latest open-source version available in this repository is v4.0.0.

---

## Before You Contribute

Before opening an issue or pull request, please:

1. Check the existing issues to see whether the problem or idea has already been reported.
2. Make sure you are working against the version of Truck Manager contained in this repository.
3. Test your changes before submitting them.
4. Keep contributions focused on Truck Manager and its supported ETS2/ATS functionality.
5. Do not include copyrighted game or mod files in your contribution unless you have permission to redistribute them.

---

## Reporting Bugs

If you find a bug, please open an issue and provide as much useful information as possible.

A good bug report should include:

* A clear description of the problem.
* The steps required to reproduce it.
* What you expected to happen.
* What actually happened.
* The Truck Manager version you are using.
* Whether you are using ETS2 or ATS.
* Relevant game version information.
* Relevant mod or load-order information, if applicable.
* Screenshots, logs, or other diagnostic information when available.

### Example

```text
Title: Preset import fails with a large mod list

Truck Manager version:
v4.0.0

Game:
Euro Truck Simulator 2

Steps to reproduce:
1. Create a preset containing a large number of mods.
2. Export the preset.
3. Import the preset on another profile.

Expected:
The preset should be imported successfully.

Actual:
The import operation fails and the preset is not created.

Additional information:
The issue appears to occur with approximately 100+ mods.
```

Please avoid including personal information, authentication credentials, or other sensitive data in issues and logs.

---

## Suggesting Features

Feature suggestions are welcome.

Before proposing a new feature, consider whether it:

* Solves a real problem for ETS2/ATS players.
* Fits the purpose of Truck Manager.
* Can be implemented without unnecessarily complicating the application.
* Does not require distributing third-party mods or copyrighted game content.
* Would be useful to more than one specific setup or user.

When suggesting a feature, explain:

1. What you would like Truck Manager to do.
2. Why the feature would be useful.
3. How you expect it to work.
4. Any examples or use cases that demonstrate the idea.

For larger features, discussing the idea in an issue before starting implementation is recommended.

---

## Pull Requests

Pull requests are the preferred way to contribute code or other changes.

Before opening a pull request:

* Make sure your changes are based on the appropriate branch.
* Keep the pull request focused on one feature, bug fix, or improvement where possible.
* Test the changes locally.
* Make sure existing functionality has not been unnecessarily broken.
* Update documentation when your changes affect user-facing functionality.
* Include relevant screenshots when they help explain UI changes.

A pull request description should explain:

* What was changed.
* Why it was changed.
* How it was tested.
* Any known limitations or areas that require additional testing.

### Keep Pull Requests Focused

Avoid combining unrelated changes into a single pull request.

For example, a pull request that fixes a preset-import bug should not also contain unrelated UI redesigns, dependency updates, and formatting changes.

Smaller pull requests are easier to review, test, and maintain.

---

## Code Contributions

When contributing code:

* Follow the existing structure and conventions of the project.
* Prefer clear and maintainable code over unnecessarily complex solutions.
* Avoid introducing dependencies unless they provide a clear benefit.
* Do not remove existing functionality without discussing the change first.
* Handle errors appropriately rather than silently ignoring them.
* Avoid hard-coding paths that only work on one computer.
* Consider both ETS2 and ATS when modifying functionality that supports both games.

If you are unsure how an existing part of the application works, open an issue or discussion before making a large architectural change.

---

## Game and Mod Compatibility

Truck Manager interacts with ETS2/ATS profiles, mod configurations, load orders, and related game data.

Changes that modify game or profile data should be treated carefully.

In particular:

* Do not assume that a change affecting ETS2 will automatically work correctly with ATS.
* Test profile-related functionality with appropriate backups.
* Avoid destructive changes to user data.
* Preserve existing backup and recovery mechanisms.
* Do not include third-party mods in the repository simply to make a feature work.

Truck Manager presets are intended to describe and share load orders. They do **not** download or distribute the mods themselves. Users must already have the required local or Steam Workshop mods installed.

---

## Third-Party Content

Please do not submit copyrighted third-party content without permission.

This includes, but is not limited to:

* ETS2/ATS game files.
* Third-party mods.
* Mod assets.
* Textures.
* Models.
* Sounds.
* Logos or other copyrighted assets.
* Content copied from another project without permission.

If your contribution depends on a third-party library, asset, or project, clearly identify it and make sure its license permits the intended use.

---

## Documentation and Translations

Documentation improvements are welcome.

You can contribute by:

* Fixing incorrect information.
* Improving explanations.
* Adding examples.
* Improving setup instructions.
* Correcting spelling or grammar.
* Improving the English or Spanish documentation.
* Adding translations where appropriate.

Documentation changes can be submitted through pull requests just like code changes.

---

## Commit Messages

Please use clear and descriptive commit messages.

Good examples:

```text
Fix preset import validation
Add ATS profile detection
Improve mod load-order handling
Update profile editor documentation
```

Avoid vague messages such as:

```text
fix
changes
update
stuff
```

There is no requirement to use a specific commit-message format unless the maintainers introduce one in the future.

---

## Review Process

All pull requests may be reviewed by the project maintainers before being merged.

Reviewers may request:

* Code changes.
* Additional testing.
* Documentation updates.
* Changes to the scope of the pull request.
* Clarification about implementation decisions.

Please treat review comments as part of the collaboration process. The goal is to maintain a stable and useful project for the community.

Not every contribution will necessarily be accepted. A contribution may be declined if it does not fit the project's goals, introduces unacceptable risks, duplicates existing functionality, or cannot be reasonably maintained.

---

## Security Issues

Please do not publicly disclose sensitive security issues before they can be reviewed by the maintainers.

If you discover a potential security vulnerability, follow the project's security reporting process if one is available. If no private security reporting mechanism is currently available, contact the project maintainers privately before publishing detailed exploit information in a public issue.

Do not include passwords, tokens, personal information, or other sensitive credentials in issues or pull requests.

---

## Questions and Discussions

If you are unsure whether an idea or contribution fits the project, it is better to ask before spending significant time implementing it.

For general questions, ideas, and community discussion, use the project's available community channels.

The project currently provides a Discord community for communication.

---

## Recognition

Contributors who provide meaningful improvements to Truck Manager are appreciated and may be recognized in the project where appropriate.

Contributing does not guarantee that a contribution will be merged, but every constructive contribution helps improve the project.

---

## Thank You

Thank you for helping improve Truck Manager and for contributing to the ETS2 and ATS community.
