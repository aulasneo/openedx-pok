openedx-pok
############

Introduction
************

This repository contains a plugin for Open edX that replaces the standard certificate generation system with a custom integration using the POK API. The main goal is to enable the issuance of personalized and advanced certificates, managed via the POK API, while maintaining interoperability with the Open edX ecosystem.

The plugin uses Open edX-provided `filters` to intercept events related to certificate creation and rendering, redirecting these processes to the POK API. This allows for a seamless and transparent integration for end users.

Architecture and Operation
****************************

### 1. Event Interception Using Filters

The plugin leverages Open edX filters to intercept the following key events:

- **CertificateCreationRequested**: This filter is triggered when a certificate creation request is made. The plugin redirects this request to the POK API to generate the certificate.
- **CertificateRenderStarted**: This filter is triggered when a certificate is about to be rendered. The plugin redirects the rendering process to the POK API to display the generated certificate or an intermediate status (e.g., processing, error).

### 2. Integration with the POK API

The POK API client (`PokApiClient`) handles all communication with the external API. This includes:

- Requesting custom certificates.
- Retrieving details of existing certificates.
- Generating previews of certificate templates.
- Managing custom parameters defined in POK templates.

### 3. Database Models

The plugin defines two main models:

- **PokCertificate**: Stores information about certificates generated via POK, including status, viewing URL, and additional metadata.
- **CertificateTemplate**: Links an Open edX course to a specific POK template, enabling per-course certificate customization.

### 4. Administration and Configuration

The plugin includes a Django admin interface to manage certificates and templates. Additionally, plugin settings are defined in `settings.common.py`, where parameters such as the POK API URL, authentication keys, and timeout values are configured.

Workflow
*********

1. **Certificate Creation**:
   - When a certificate is requested, the `CertificateCreationRequested` filter intercepts the request.
   - The POK API client is used to send user, course, and custom parameter data.
   - The POK API generates the certificate and returns a unique identifier, which is stored in the `PokCertificate` model.

2. **Certificate Rendering**:
   - When a user attempts to view a certificate, the `CertificateRenderStarted` filter intercepts the request.
   - Depending on the certificate status (issued, in progress, etc.), the plugin redirects the user to the appropriate URL or displays an intermediate status page.

3. **Error Handling**:
   - If an error occurs during certificate generation or rendering, the plugin displays a custom error page.

Configuration
*************

### Prerequisites

- A working Open edX installation.
- Valid credentials for accessing the POK API.
- Certificate templates configured in the POK platform.

### Configuration Variables

The following variables must be set in the `settings.common.py` file:

- `POK_API_URL`: Base URL of the POK API.
- `POK_API_KEY`: Authentication key for the API.
- `POK_TEMPLATE_ID`: Default template ID.
- `POK_TIMEOUT`: Timeout value for API requests.

### Installation

1. Clone this repository into the Open edX extensions directory.
2. Add `openedx_pok` to the `INSTALLED_APPS` list in the Django settings.
3. Configure the required variables in the Open edX settings file.
4. Run migrations to create the required database tables:

python manage.py migrate openedx_pok

### Usage

- **Admin Panel**: Use the Django admin interface to manage certificates and templates.
- **Preview**: Use the preview functionality to check how a certificate will appear before issuing it.
- **Monitoring**: Check logs to debug issues or monitor the status of POK API requests.

Support
*******

This Open edX plugin was developed by Aulasneo. Feel free to reach out to us if you need a custom version of it.
Also, If you encounter issues or have questions, you can open an issue in this repository or join discussions in the Open edX community.

https://aulasneo.com/

License
*******

This project is licensed under the terms specified in the `LICENSE.txt` file.

Contributions
*************

Contributions are welcome. Please read the contribution guidelines before submitting a pull request.
