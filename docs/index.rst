.. openedx-pok-webhook documentation top level file, created by
   sphinx-quickstart on Wed Mar 26 10:46:20 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

openedx-pok-webhook
===================

A Django extension for Open edX that provides a webhook API for integration with external systems. This application facilitates real-time communication between the Open edX platform and third-party services, enabling automatic notifications when specific events occur in the LMS, such as completing a course, submitting an assignment, or passing an assessment. It includes JWT authentication, signature handling for verifying requests, retry capabilities for failed webhooks, and an admin dashboard for monitoring the status of sent notifications.

Contents:

.. toctree::
   :maxdepth: 2

   readme
   getting_started
   quickstarts/index
   concepts/index
   how-tos/index
   testing
   internationalization
   modules
   changelog
   decisions
   references/index


Indices and tables
##################

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
