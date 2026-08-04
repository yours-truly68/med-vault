Frontend Specification Document (FSD)

Product Name: MedVault

Version: MVP v1.0

Status: Draft

⸻

1. Overview

Purpose

This document defines the frontend architecture, application structure, pages, layouts, components, and user flows for the MedVault MVP.

The frontend should prioritize:

* Simplicity
* Accessibility
* Fast navigation
* Responsive design
* Clear information hierarchy

The application should feel approachable for users of all technical backgrounds.

⸻

2. Design Goals

The interface should make users feel that their medical records are:

* Safe
* Organized
* Easy to access
* Easy to understand

The product should minimize cognitive load and surface the most relevant information without overwhelming the user.

⸻

3. Navigation Structure

Landing
    │
    ├── Login
    └── Register
Authenticated
Dashboard
│
├── Documents
├── Upload
├── Timeline
├── AI Assistant
├── Family Members
└── Settings

⸻

4. Application Layout

Authenticated pages share a common layout.

+---------------------------------------------------------+
| Navbar                                                  |
+----------------------+----------------------------------+
| Sidebar              |                                  |
|                      |                                  |
| Dashboard            |                                  |
| Documents            |          Main Content            |
| Upload               |                                  |
| Timeline             |                                  |
| AI Assistant         |                                  |
| Family Members       |                                  |
| Settings             |                                  |
|                      |                                  |
+----------------------+----------------------------------+

⸻

5. Pages

5.1 Landing Page

Purpose

Introduce MedVault and encourage users to register.

Sections

* Hero
* Product Features
* How It Works
* Benefits
* Call To Action
* Footer

Primary Action

Create Account

⸻

5.2 Login Page

Components

* Email
* Password
* Login Button
* Forgot Password (Future)
* Register Link

⸻

5.3 Register Page

Components

* Full Name
* Email
* Password
* Confirm Password
* Register Button

⸻

5.4 Dashboard

Purpose

Provide a quick overview of the user’s medical records.

Cards

* Total Documents
* Family Members
* Recent Uploads
* Recently Processed Files

Sections

* Recent Documents
* Medical Timeline Preview
* AI Summary
* Quick Actions

Quick Actions:

* Upload Documents
* Open AI Assistant
* View Timeline

⸻

5.5 Documents Page

Purpose

Display every uploaded document.

Features

* Search
* Filter
* Sort
* Grid View
* List View

Filters

* Family Member
* Document Type
* Upload Date

Each document card displays:

* Document Name
* Document Type
* Family Member
* Upload Date
* Processing Status

⸻

5.6 Upload Page

Purpose

Upload medical records.

Components

* Drag & Drop Zone
* File Picker
* Upload Progress
* Upload Queue
* Processing Status

Supported formats:

* PDF
* JPG
* JPEG
* PNG

⸻

5.7 Timeline Page

Purpose

Visualize the patient’s medical history.

Timeline entries display:

* Date
* Document Type
* Hospital
* Doctor (if available)
* Summary

Timeline should be ordered chronologically.

⸻

5.8 AI Assistant

Purpose

Allow users to ask questions about their medical history.

Layout

Left Panel

* Previous Questions

Right Panel

* Chat Conversation

Bottom

* Prompt Input
* Send Button

Example Questions

* When was my last MRI?
* Show my diabetes reports.
* Which doctor prescribed Metformin?
* What surgeries have I had?

Every response should include links to the supporting documents.

⸻

5.9 Family Members

Purpose

Manage medical records for family members.

Features

* View Members
* Add Member
* Edit Member
* Delete Member

Each member card displays:

* Name
* Relationship
* Number of Documents

⸻

5.10 Settings

Sections

Account

* Name
* Email

Preferences

* Theme (Light/Dark/System)

Danger Zone

* Delete Account

⸻

6. Shared Components

The application should reuse components wherever possible.

Core components include:

* Navbar
* Sidebar
* Page Header
* Search Bar
* Button
* Card
* Badge
* Modal
* Dialog
* Dropdown Menu
* Tabs
* Tooltip
* Toast
* Empty State
* Loading Skeleton
* Pagination

⸻

7. Document Components

Upload Zone

Supports:

* Drag & Drop
* Click to Upload
* Multiple Files

⸻

Document Card

Displays:

* Document Name
* Type
* Upload Date
* Status

Actions:

* View
* Download
* Delete

⸻

Document Preview

Supports:

* PDF Viewer
* Image Viewer

Displays:

* Metadata
* AI Summary
* Extracted Information

⸻

8. AI Components

Chat Interface

Supports:

* Conversation History
* Auto Scroll
* Markdown Responses
* Source Citations
* Loading State

⸻

AI Summary Card

Displays:

* Short Summary
* Key Findings
* Important Dates

⸻

Search Box

Supports natural language queries.

Example:

Show my blood reports from 2024

⸻

9. Empty States

Examples:

Documents

“No documents uploaded yet.”

Upload

“Upload your first medical record.”

Timeline

“No medical history available.”

AI Assistant

“Ask a question about your medical records.”

⸻

10. Loading States

The UI should provide clear feedback while processing.

Examples:

* Upload Progress
* AI Processing Spinner
* Skeleton Loaders
* Disabled Buttons

Users should always know what the system is doing.

⸻

11. Error States

Examples:

* Upload failed
* AI processing failed
* Network unavailable
* Session expired

Errors should include clear messaging and suggested next actions where appropriate.

⸻

12. Responsive Design

The application should support:

Desktop

* Full sidebar
* Multi-column layouts

Tablet

* Collapsible sidebar
* Adaptive spacing

Mobile

* Bottom navigation or drawer
* Single-column layout
* Optimized touch targets

⸻

13. Accessibility

The interface should follow basic accessibility best practices.

Include:

* Keyboard navigation
* Focus indicators
* Proper labels
* Sufficient color contrast
* Semantic HTML
* Screen reader-friendly elements

⸻

14. User Flow

New User

Landing

↓

Register

↓

Dashboard

↓

Add Family Member

↓

Upload Documents

↓

AI Processing

↓

View Timeline

↓

Ask AI Questions

⸻

Returning User

Login

↓

Dashboard

↓

Search Documents

↓

Open Timeline

↓

Use AI Assistant

⸻

15. Frontend State Management

Server State

Managed using:

* TanStack Query

Examples:

* Documents
* Family Members
* Timeline
* AI Chat
* Search Results

⸻

Client State

Managed using:

* Zustand

Examples:

* Authentication
* Selected Family Member
* Theme
* Sidebar State
* Active Filters

⸻

16. Design Principles

The MedVault frontend should follow these principles:

* Keep interfaces simple and uncluttered.
* Prioritize readability over visual complexity.
* Surface important information first.
* Minimize the number of clicks required for common tasks.
* Provide immediate feedback for user actions.
* Maintain consistency across pages and components.
* Design for trust, clarity, and ease of use.