"""
A Django extension for Open edX that provides a webhook API for integration with external systems. This application facilitates real-time communication between the Open edX platform and third-party services, enabling automatic notifications when specific events occur in the LMS, such as completing a course, submitting an assignment, or passing an assessment. It includes JWT authentication, signature handling for verifying requests, retry capabilities for failed webhooks, and an admin dashboard for monitoring the status of sent notifications.
"""

__version__ = '0.1.0'
