Change Log
##########

..
   All enhancements and patches to openedx_pok will be documented
   in this file.  It adheres to the structure of https://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (https://semver.org/).

Unreleased
******************

Changed
=======

* Enhanced language tag resolution with user preferences and normalization.

1.0.1 - 2025-11-05
******************

Changed
=======

* Added support for language tag resolution based on user profile, HTTP Accept-Language, and thread language.

0.2.0 - 2025-06-03
******************

Added
=====

* Documentation: Detailed technical README explaining how the plugin integrates with POK API using Open edX filters.
* Support: Initial Django admin support for managing templates and generated certificates.
* Integration: `PokApiClient` for managing communication with POK (creation, rendering, preview, etc.).
* Filters: Hooked into `CertificateCreationRequested` and `CertificateRenderStarted` to override default behavior.
* Models: Added `PokCertificate` and `CertificateTemplate` for linking and tracking external certificate generation.
* Configuration: Introduced environment-based settings for API credentials and timeouts.

Changed
=======

* Refactored certificate generation logic to fully delegate to POK API.
* Improved error handling for API failures and rendering issues.

Fixed
=====

* Corrected integration points with Open edX to ensure compatibility with Django 4.2 and plugin architecture.

0.1.0 – 2025-03-26
******************

Added
=====

* First release on PyPI.
* Initial implementation of POK integration plugin for Open edX.