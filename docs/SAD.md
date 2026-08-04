Security & Access Document (SAD)

Product Name: MedVault

Version: MVP v1.0

Status: Draft

⸻

1. Overview

Purpose

This document outlines the security model for MedVault MVP.

As MedVault stores sensitive medical records and personally identifiable information (PII), security is a foundational requirement. The MVP focuses on protecting user data through secure authentication, authorization, encrypted communication, and safe file handling while keeping the implementation straightforward.

⸻

2. Security Objectives

The application should:

* Protect user accounts.
* Protect uploaded medical documents.
* Prevent unauthorized access.
* Ensure users can only access their own data.
* Secure communication between client and server.
* Protect sensitive information from common web vulnerabilities.

⸻

3. Authentication

Login

Users authenticate using:

* Email
* Password

Passwords are never stored in plain text.

⸻

Password Storage

Passwords are:

* Salted
* Hashed using a strong password hashing algorithm (e.g., Argon2 or bcrypt)

Only password hashes are stored in the database.

⸻

Session Management

Authentication consists of:

* Short-lived JWT Access Token
* Long-lived HTTP-only Refresh Token Cookie

The access token is used to authenticate API requests.

The refresh token is used to obtain a new access token without requiring the user to log in again.

⸻

Logout

Logging out should:

* Invalidate the refresh token
* Clear authentication cookies
* Remove any client-side session state

⸻

4. Authorization

MedVault follows a simple ownership-based access model.

A user may only access:

* Their own account
* Their own family members
* Their own uploaded documents
* AI summaries generated from their documents
* Search results from their documents
* Chat responses generated from their documents

Cross-user access is never permitted.

⸻

5. Family Member Access

Each family member belongs to exactly one user account.

Only the account owner can:

* Create family members
* Update family members
* Delete family members
* Upload documents
* View documents

There are no shared accounts or collaborative access in the MVP.

⸻

6. File Upload Security

Supported Formats

Allowed file types:

* PDF
* JPG
* JPEG
* PNG

All other file types are rejected.

⸻

File Size Limit

Maximum upload size:

* 25 MB per file

Large files are rejected before processing.

⸻

File Validation

Before saving:

* Validate file extension.
* Validate MIME type.
* Reject corrupted uploads.

⸻

File Naming

Uploaded files should not retain their original filenames.

Instead, generate unique filenames.

Example:

f82d9d1d-7e3f-4e8b-bdb0.pdf

This prevents filename collisions and information leakage.

⸻

7. File Storage

Uploaded files are stored outside the publicly accessible web directory.

Users cannot directly access files using predictable URLs.

All document access must go through authenticated API endpoints.

⸻

8. Data Protection

Sensitive information includes:

* Name
* Email
* Medical records
* Prescriptions
* Test reports
* Hospital information
* Doctor information

All data is transmitted over HTTPS.

Medical records are never exposed publicly.

⸻

9. AI Data Handling

AI processing is limited to the user’s uploaded documents.

The AI should:

* Extract metadata
* Generate summaries
* Generate embeddings
* Answer user questions

The AI must never:

* Invent medical history
* Recommend treatments
* Provide diagnoses
* Modify uploaded records

AI responses should always be grounded in retrieved documents.

⸻

10. AI Response Safety

Every AI-generated answer should include references to the documents used.

Example:

Answer
↓
Supporting Documents
↓
Prescription
Apollo Hospital
12 Jan 2025
Blood Report
ABC Diagnostics
15 Jan 2025

If sufficient information cannot be found, the AI should clearly state that no relevant records were identified rather than guessing.

⸻

11. API Security

All protected endpoints require authentication.

Protected resources include:

* Dashboard
* Documents
* Timeline
* Search
* AI Chat
* Family Members

Unauthenticated requests receive an authorization error.

⸻

12. Input Validation

All incoming requests are validated.

Validation includes:

* Required fields
* Data types
* File formats
* Maximum lengths
* Invalid values

Invalid requests return descriptive error messages.

⸻

13. Error Handling

Error responses should never expose:

* Database structure
* Stack traces
* Server file paths
* Internal implementation details

Instead, users receive generic, user-friendly messages.

⸻

14. Rate Limiting

To reduce abuse, rate limiting should be applied to:

* Login requests
* Registration requests
* Password reset requests (future)
* AI Chat requests
* Search requests

This helps protect against brute-force attacks and excessive API usage.

⸻

15. Logging

The application should log important system events such as:

* User login
* User logout
* Document upload
* Document deletion
* AI processing status
* Processing failures

Logs should never contain:

* Passwords
* Access tokens
* Refresh tokens
* Full medical document contents

⸻

16. Privacy Principles

Users retain ownership of their medical records.

The platform should:

* Store only the information required for its functionality.
* Never expose one user’s data to another.
* Allow users to permanently delete uploaded documents.
* Respect user privacy throughout the application.

⸻

17. Security Limitations (MVP)

The MVP intentionally excludes advanced security features such as:

* Multi-Factor Authentication (MFA)
* Role-Based Access Control (RBAC)
* Audit trails
* End-to-end encryption
* Hardware Security Modules (HSM)
* Security Information and Event Management (SIEM)
* Document watermarking
* Virus scanning
* Data Loss Prevention (DLP)

These features can be introduced in future releases as the platform matures.

⸻

18. Future Security Enhancements

Potential improvements include:

* Multi-Factor Authentication
* OAuth (Google, Apple)
* Email verification
* Device management
* Session management dashboard
* Encrypted cloud storage
* Malware scanning for uploads
* Audit logs
* Document version history
* Automatic backup and recovery
* Compliance with HIPAA, GDPR, and other healthcare privacy regulations (as applicable)

⸻

19. Security Principles

The MedVault MVP follows these guiding principles:

* Secure by default.
* Authenticate every protected request.
* Authorize access based on resource ownership.
* Keep uploaded files private.
* Encrypt all communication.
* Never trust client-provided input.
* Ground AI responses in user documents.
* Favor simplicity over unnecessary security complexity while maintaining strong protection for sensitive medical data.