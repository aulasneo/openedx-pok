Verawood compatibility review
=============================

Reviewed on 2026-09-09 against these Open edX platform snapshots:

* Ulmo: ``e66e4ebbf7fa831c306ef2e45b8b36766b6500ed``.
* Verawood: ``259473c5dfd1c82eac5e6c4d14bf6095cb25824d``.

The certificate creation and rendering extension points remain compatible.
This review compares upstream source and exercises the installed filter library
locally; it does not replace a staging test in LMS, Studio, and LMS workers.

Dependencies
------------

The target is Python 3.12 and Django 5.2. The previous package metadata allowed
Python 3.11 even though CI already used 3.12; it now requires at least 3.12.
The exact dependency baseline comes from the `Verawood requirements snapshot`_.

.. list-table:: Shared dependencies
   :header-rows: 1

   * - Package
     - Ulmo upstream
     - Verawood upstream
   * - Django
     - 5.2.11
     - 5.2.13
   * - Django REST Framework
     - 3.16.1
     - 3.17.1
   * - openedx-filters
     - 2.1.0
     - 3.4.1
   * - edx-opaque-keys
     - 3.0.0
     - 4.0.0
   * - edx-django-utils
     - 8.0.1
     - 8.0.1
   * - django-model-utils
     - 5.0.0
     - 5.0.0
   * - openedx-atlas
     - 0.7.0
     - 0.7.0
   * - requests
     - 2.32.5
     - 2.33.1
   * - edx-organizations (provided by the platform)
     - 7.3.0
     - 8.0.0

``requirements/base.in`` declares runtime compatibility ranges. The wheel does
not embed the exact platform pins, so platform patch updates remain possible.
``requirements/constraints.txt`` pins the shared dependency subset for local
development and tests, including transitive dependencies. All generated
requirements files are rebuilt from these constraints. Django remains pinned
in the test lockfile so CI actually tests the selected platform baseline.

Regenerate requirements in a Python 3.12 virtual environment::

    python3.12 -m venv .venv
    . .venv/bin/activate
    make compile-requirements
    tox -e py312-django52,quality,docs,pii_check

Install the plugin in the platform image using that deployment's own
``requirements/edx/base.txt`` as constraints after stripping extras from package
names (pip constraints cannot contain extras). Do not install this repository's
development or test lockfiles into LMS/Studio. Refresh the local snapshot when
adopting a later platform patch release.

Integration points
------------------

* **Creation:** ``org.openedx.learning.certificate.creation.requested.v1``
  still runs in ``lms/djangoapps/certificates/generation_handler.py``. It passes
  ``user, course_key, mode, status, grade, generation_mode`` and handles
  ``PreventCertificateCreation``. Despite the filter library's float annotation,
  both platform branches pass a course-grade object. POK now reads its
  ``percent`` attribute and also accepts numeric grades. Successful POK creation
  preserves the arguments so Open edX can continue its normal certificate task.
  See the `creation call site`_.
* **Rendering:** ``org.openedx.learning.certificate.render.started.v1`` retains
  ``context`` and ``custom_template`` and handles ``RenderCustomResponse``.
  Verawood adds ``context['user_certificate']``; the existing course and learner
  fields remain available. No event name or response-exception migration is
  needed. See the `render call site`_ and `filter definitions`_.
* **Plugin discovery:** LMS and CMS retain ``lms.djangoapp`` and
  ``cms.djangoapp`` registration and ``edx_django_utils.plugins.add_plugins``.
  The existing settings and ``/api/pok/`` URL registration remain appropriate.
* **Course data:** ``openedx.core.lib.courses.get_course_by_id`` and
  ``openedx.core.djangoapps.waffle_utils.CourseWaffleFlag`` retain their interfaces.
  The ``course_overviews.CourseOverview`` model label, course-key primary key,
  and migration ``0029_alter_historicalcourseoverview_options`` remain present.
  No POK database migration is required. The app's default primary-key type now
  matches the existing ``AutoField`` migrations, correcting pre-existing drift
  toward ``BigAutoField``; CI checks for missing migrations. The local course-overview stub now
  uses a real ``CourseKeyField`` primary key instead of an integer so tests
  exercise the opaque-key upgrade and actual foreign-key lookups.
* **Organizations and language:** ``organizations.api.get_course_organizations``
  has identical API source in versions 7.3.0 and 8.0.0. The
  ``openedx.core.djangoapps.user_api.preferences.api.get_user_preference``
  interface remains available. The platform still supplies ``django-crum``.
* **Frontend URLs:** POK now uses ``COURSE_AUTHORING_MICROFRONTEND_URL`` directly
  for the Studio certificate link and ``LMS_ROOT_URL`` for downloads, instead
  of guessing the authoring host or depending on ``MFE_CONFIG['LMS_BASE_URL']``.
  These are existing platform settings, not newly introduced Verawood settings.
  Configure both to nonempty public URLs in the deployment.
* **Other frontend changes:** Verawood's new instructor dashboard and frontend-base
  configuration endpoint do not replace the certificate rendering hook. POK does
  not register the legacy instructor dashboard filter affected by that change.
  See the `operator release notes`_.

Staging verification
--------------------

1. Build LMS, Studio, and workers with the plugin and the deployment's platform
   constraints; run ``pip check`` in the resulting image.
2. Apply the normal platform migrations. Verawood adds course-catalog backfill
   migration ``course_overviews.0030``; follow the operator release notes for
   missing organization records. Keep POK's existing migration dependencies.
3. Check that both POK pipelines are present in ``OPEN_EDX_FILTERS_CONFIG`` after
   deployment settings have loaded, preserving other plugins' pipelines.
4. Configure POK credentials, a valid certificate/signatory configuration,
   a course template, the two public frontend URLs, and ``module_pok.enable``.
5. Preview from Studio, issue from LMS with a passing grade, and verify the grade
   sent to POK. Exercise a pending response, polling to emitted, the image
   download, social links, and the return-to-Studio link.
6. Confirm an API failure prevents normal certificate creation, repeat issuance
   does not create another credential, and courses with POK disabled retain
   standard Open edX behavior.

Existing review findings outside the upgrade changes
-----------------------------------------------------

* ``CertificateImageDownloadView`` has no explicit permission or ownership check:
  it accepts learner and course IDs and requests a decrypted image. Decide whether
  downloads are intentionally public; otherwise add an appropriate access policy.
  Certificate revocation is not checked by this endpoint either.
* Creation checks for an existing POK ID before making the external request but
  does not serialize concurrent requests. Database uniqueness alone cannot prevent
  duplicate remote credentials. Verify POK idempotency before relying on retries.
* Empty certificate/signatory lists can still raise indexing errors, and broad
  import fallbacks can conceal missing platform integration modules. A successful
  standalone test run does not establish that the deployed imports and settings
  loaded correctly.
* The API client logs complete issuance payloads containing learner names and
  email addresses. Review log redaction and retention before production rollout.

.. _Verawood requirements snapshot: https://github.com/openedx/edx-platform/blob/259473c5dfd1c82eac5e6c4d14bf6095cb25824d/requirements/edx/base.txt
.. _creation call site: https://github.com/openedx/edx-platform/blob/259473c5dfd1c82eac5e6c4d14bf6095cb25824d/lms/djangoapps/certificates/generation_handler.py
.. _render call site: https://github.com/openedx/edx-platform/blob/259473c5dfd1c82eac5e6c4d14bf6095cb25824d/lms/djangoapps/certificates/views/webview.py
.. _filter definitions: https://github.com/openedx/openedx-filters/blob/v3.4.1/openedx_filters/learning/filters.py
.. _operator release notes: https://docs.openedx.org/en/latest/community/release_notes/verawood/dev_op_release_notes.html
