# Security Policy

## Supported Versions

Security fixes are generally considered for the open-source versions of Truck Manager that are actively maintained by the project.

At the time of writing, the latest open-source version available in this repository is **v4.0.0**.

The **v5.0.0** release is closed source and is not part of the source code contained in this repository.

| Version | Supported |
| :-----: | :-------: |
|  v5.0.x |     No    |
|  v4.0.x |    Yes    |
|  < v4.0 |     No    |

Support status may change as the project evolves.

---

## Reporting a Vulnerability

If you discover a potential security vulnerability in Truck Manager, please **do not disclose the vulnerability publicly through a GitHub issue, pull request, or other public forum** before the maintainers have had an opportunity to investigate it.

Please report security issues privately to:

**[cortex.studios.info@gmail.com](mailto:cortex.studios.info@gmail.com)**

When reporting a vulnerability, please provide as much information as possible, including:

* A clear description of the vulnerability.
* The affected version of Truck Manager.
* Steps required to reproduce the issue.
* The expected behavior.
* The actual behavior.
* Any relevant screenshots, logs, or proof-of-concept information.
* Information about the environment in which the issue occurs.

Please do not include passwords, authentication tokens, personal information, or other unrelated sensitive information in your report.

---

## What Should Be Reported?

Security reports may include, but are not limited to:

* Unauthorized access to user data.
* Unauthorized modification or deletion of files.
* Unsafe handling of user-controlled files or data.
* Arbitrary code execution.
* Authentication or authorization vulnerabilities.
* Insecure network communication.
* Sensitive information being exposed or stored improperly.
* Vulnerabilities introduced through third-party dependencies.
* Other behavior that could compromise the security of users or their systems.

If you are unsure whether an issue qualifies as a security vulnerability, please report it privately rather than publishing potentially sensitive details.

---

## What Should Not Be Reported as a Security Vulnerability?

The following should generally be reported through the normal GitHub issue process instead:

* General bugs that do not have a security impact.
* Feature requests.
* UI or usability problems.
* Game compatibility issues.
* Mod compatibility problems.
* Performance issues without a security impact.
* Incorrect documentation.

See `CONTRIBUTING.md` for information about normal bug reports and contributions.

---

## Disclosure Process

After receiving a security report, the maintainers will attempt to:

1. Acknowledge the report.
2. Reproduce and assess the reported issue.
3. Determine the affected versions and severity.
4. Develop and test an appropriate fix where necessary.
5. Release the fix when appropriate.
6. Communicate relevant information to affected users when appropriate.

The timing of investigation and fixes may vary depending on the severity and complexity of the issue.

Please allow the maintainers reasonable time to investigate and address a vulnerability before publicly disclosing technical details.

---

## Responsible Disclosure

We ask security researchers and contributors to follow responsible disclosure practices.

Please:

* Report vulnerabilities privately.
* Give the maintainers reasonable time to investigate and address the issue.
* Avoid accessing, modifying, deleting, or exposing other users' data.
* Avoid disrupting services or users unnecessarily.
* Do not use a vulnerability for malicious purposes.
* Do not publicly disclose exploit details before coordinating with the maintainers.

Security researchers who responsibly report valid vulnerabilities are appreciated for helping improve Truck Manager.

---

## Scope

This security policy applies to the open-source Truck Manager code contained in this repository.

Third-party software, Steam Workshop content, ETS2/ATS themselves, and third-party mods are outside the direct scope of this repository's security policy.

If a vulnerability appears to involve a third-party component, please provide enough information for the maintainers to determine whether Truck Manager is affected.

---

## Security Updates

Security fixes may be communicated through appropriate project channels, including GitHub releases, repository announcements, or other official project communication channels.

Users are encouraged to keep Truck Manager updated when security fixes or important maintenance releases become available.
