# CrowdPics TV — Terms of Service

**Effective Date: January 31, 2026**
**Last Updated: January 31, 2026**

These Terms of Service ("Terms") govern your access to and use of the CrowdPics TV platform ("Service"), operated by CrowdPics Inc. ("Company," "we," "our"). By accessing or using the Service, you agree to be bound by these Terms.

---

## 1. Service Description

CrowdPics TV is a cloud-based digital signage platform that enables businesses, venues, and event organizers ("Customers") to collect, curate, and display user-submitted photographs on connected display devices in real time.

### 1.1 Core Platform Capabilities

The Service provides the following capabilities:

1. **Photo Collection** — Attendees and guests ("End Users") may submit photographs to a Customer's gallery via the CrowdPics mobile web application, native iOS application, native Android application, or SMS submission. End Users do not require an account to submit photos.

2. **Content Moderation** — All submitted photographs are processed through a multi-layer moderation pipeline consisting of: (a) automated AI-powered content analysis using computer vision models for nudity, violence, and inappropriate content detection; (b) automated text/overlay detection for offensive language; (c) optional human review queue accessible to Customer administrators; and (d) configurable moderation sensitivity thresholds per Customer account.

3. **Display Management** — Customers may register and manage one or more display devices ("Devices"), including Amazon Fire TV, Android TV, Apple TV, Chromecast-enabled displays, and any modern web browser. Each Device connects to the Service via a persistent WebSocket connection and receives real-time content updates without manual refresh.

4. **Playlist Curation** — Customers may organize approved photographs into one or more playlists with configurable display duration, transition effects, and scheduling rules. Playlists may be assigned to specific Devices or Device groups.

5. **Real-Time Display** — Approved photographs appear on connected Devices within 5 seconds of approval. Devices display content in a continuous slideshow format with configurable transitions including fade, slide, zoom, and ken-burns effects.

6. **Branded Experience** — Customers may customize the display experience with their own logo, brand colors, welcome messages, QR code overlays, and custom CSS. The submission interface may also be branded with the Customer's identity.

7. **Analytics Dashboard** — The Service provides real-time and historical analytics including: total submissions per event, approval/rejection ratios, peak submission times, unique submitter counts, average photos per submitter, Device uptime statistics, and audience engagement metrics derived from submission patterns.

8. **Event Management** — Customers may create discrete events with start and end times, unique submission URLs, dedicated QR codes, and independent moderation settings. Events may be recurring with automatic gallery reset between occurrences.

9. **Team Collaboration** — Customer accounts support multiple team members with role-based access control. Available roles include: Owner (full access including billing), Admin (full access excluding billing and ownership transfer), Moderator (photo approval/rejection and playlist management only), and Viewer (read-only dashboard access).

10. **AI-Powered Enhancements** — The Service offers optional AI-powered features including: automatic photo enhancement (brightness, contrast, color correction), intelligent cropping for optimal display aspect ratios, duplicate photo detection, face clustering for privacy management, and AI-generated slideshow narratives.

11. **Integration Capabilities** — The Service integrates with third-party platforms including: Stripe for payment processing, Slack for moderation notifications, Zapier for workflow automation, Google Sheets for submission data export, and custom webhook endpoints for programmatic event handling.

12. **Multi-Location Management** — Customers on Team plans may manage multiple physical locations from a single account, with per-location Device assignments, separate galleries, and consolidated billing.

### 1.2 Submission Methods

End Users may submit photographs through the following channels:

- **Mobile Web Application** — Accessible via QR code scan or direct URL. No app installation required. Supports camera capture and gallery selection.
- **Native iOS Application** — Available on the Apple App Store. Supports camera capture, gallery selection, burst upload, and push notification for photo approval status.
- **Native Android Application** — Available on the Google Play Store. Supports camera capture, gallery selection, and push notification for photo approval status.
- **SMS Submission** — End Users may text photographs to a dedicated phone number assigned to the Customer's event. Available in supported regions (United States, Canada, United Kingdom, Bahamas, and additional territories as added).
- **Email Submission** — End Users may email photographs to a dedicated email address assigned to the Customer's event. Supports attachments up to 25MB.
- **API Submission** — Customers with Developer access may submit photographs programmatically via the CrowdPics REST API.

### 1.3 Supported Devices

The Service supports the following display platforms:

- Amazon Fire TV (Fire OS 5.0 and later)
- Android TV (Android 8.0 and later)
- Apple TV (tvOS 14.0 and later)
- Google Chromecast (Generation 3 and later)
- Samsung Tizen Smart TV (2019 models and later)
- LG webOS Smart TV (2019 models and later)
- Roku (OS 10.0 and later)
- Any device with a modern web browser (Chrome 90+, Safari 14+, Firefox 88+, Edge 90+)

---

## 2. Account Registration and Security

### 2.1 Account Creation

To use the Service as a Customer, you must create an account by providing a valid email address, creating a password that meets our minimum security requirements (minimum 12 characters, including uppercase, lowercase, numeric, and special characters), and agreeing to these Terms.

### 2.2 Account Security

Customers are responsible for maintaining the security of their accounts. The Service supports and encourages the following security measures:

- **Two-Factor Authentication (2FA)** — Available via authenticator application (TOTP). Customers may enforce 2FA for all team members from the Security Settings panel.
- **Session Management** — Active sessions are visible in the Security Settings panel. Customers may terminate individual sessions or all sessions remotely.
- **Audit Logging** — All account actions including logins, setting changes, team member modifications, and billing events are recorded in an immutable audit log accessible to account Owners and Admins. Audit logs are retained for 12 months.
- **IP Allowlisting** — Customers on Pro and Team plans may restrict dashboard access to specific IP addresses or CIDR ranges.
- **API Key Management** — API keys may be created, rotated, and revoked from the Developer Settings panel. Each key may be scoped to specific API endpoints.
- **Single Sign-On (SSO)** — Customers on Team plans may configure SSO via SAML 2.0 or OpenID Connect with supported identity providers including Okta, Azure AD, Google Workspace, and OneLogin.

### 2.3 Account Verification

Business accounts must complete identity verification within 30 days of account creation. Verification requires a valid government-issued ID for the account Owner and proof of business registration. Unverified accounts are limited to 100 photo submissions per month and 1 connected Device.

---

## 3. Subscription Plans and Billing

### 3.1 Plans

The Service is offered under the following subscription plans:

| Plan | Monthly Price | Annual Price | Devices | Storage | Team Members | Events/Month |
|------|--------------|-------------|---------|---------|-------------|-------------|
| Starter | $79/month | $790/year | Up to 3 | 10 GB | 2 | 10 |
| Pro | $149/month | $1,490/year | Up to 10 | 50 GB | 10 | Unlimited |
| Team | $299/month | $2,990/year | Up to 50 | 200 GB | Unlimited | Unlimited |
| Enterprise | Custom | Custom | Unlimited | Custom | Unlimited | Unlimited |

All plans include: unlimited photo submissions from End Users, automated AI moderation, real-time display, mobile web submission app, email support, and a 14-day free trial.

**Pro plan additionally includes:** Custom branding, analytics dashboard, SMS submission, priority support (4-hour response), API access, IP allowlisting, and webhook integrations.

**Team plan additionally includes:** Multi-location management, SSO, dedicated account manager, 99.9% uptime SLA, custom transition effects, white-label display mode, and phone support.

**Enterprise plan additionally includes:** Custom SLA, on-premises deployment option, custom integrations, dedicated infrastructure, and 24/7 phone support.

### 3.2 Free Trial

New Customers receive a 14-day free trial of the Pro plan. No credit card is required to start a trial. At trial expiration, Customers may select a paid plan or their account will be downgraded to a limited free tier (1 Device, 50 photos/month, no custom branding).

### 3.3 Billing

Subscriptions are billed monthly or annually in advance via credit card, debit card, or ACH transfer. All prices are in United States Dollars (USD). Invoices are available in the Billing section of the dashboard. The Service uses Stripe for payment processing; the Company does not store credit card numbers on its servers.

### 3.4 Refund Policy

Customers may cancel their subscription at any time. Monthly subscriptions are not eligible for partial-month refunds. Annual subscriptions may be refunded on a pro-rata basis within the first 30 days of purchase. After 30 days, annual subscriptions are non-refundable but remain active until the end of the billing period.

### 3.5 Usage Overages

If a Customer exceeds their plan's Device or storage limits, they will receive a notification and a 7-day grace period to upgrade their plan or reduce usage. After the grace period, additional Devices will be disconnected (most recently added first) and photo uploads may be throttled.

---

## 4. Data Handling and Privacy

### 4.1 Customer Data

Customer data includes account information, billing details, team member profiles, device registrations, playlist configurations, event settings, and analytics data. Customer data is:

- Stored on encrypted servers (AES-256 at rest) in the United States
- Transmitted over TLS 1.3 encrypted connections
- Backed up daily with 30-day retention
- Accessible only to authorized team members based on role permissions
- Exportable in standard formats (CSV, JSON) from the dashboard at any time
- Deleted within 30 days of account termination upon request

### 4.2 End User Data

End User data includes photographs, submission metadata (timestamp, device type, approximate location if permitted), and optional contact information (phone number for SMS submissions, email for email submissions). End User data is:

- Processed solely for the purpose of display on Customer Devices
- Subject to automated content moderation
- Stored for the duration of the Customer's photo retention policy (configurable: 7 days, 30 days, 90 days, 1 year, or indefinite)
- Not sold, shared with, or disclosed to any third party except as required for content moderation (AI processing) or as required by law
- Deletable by the submitting End User via the submission confirmation page or by contacting the Customer

### 4.3 Photo Processing

Submitted photographs are processed as follows:

1. **Upload** — Photo is received and stored in encrypted cloud storage (AWS S3, US regions)
2. **Moderation** — Photo is analyzed by AI content moderation (AWS Rekognition) for policy compliance
3. **Optimization** — Photo is resized and optimized for display resolution (1080p and 4K variants generated)
4. **Thumbnail** — A thumbnail variant is generated for the moderation queue and gallery view
5. **Metadata Extraction** — EXIF data is read for orientation correction; GPS data is stripped for privacy
6. **Display** — Upon approval, photo is delivered to assigned Devices via WebSocket
7. **Retention** — Photo is retained per Customer's configured retention policy, then permanently deleted

All processing occurs within 10 seconds of upload under normal load conditions.

### 4.4 Content Moderation AI

The Service uses AI-powered content moderation to detect and flag potentially inappropriate content. The AI moderation system:

- Analyzes photographs for nudity, violence, hate symbols, drug paraphernalia, and other content categories
- Assigns a confidence score (0-100) for each detected category
- Automatically rejects photographs exceeding the Customer's configured sensitivity threshold
- Flags photographs in an ambiguous range for human review
- Does not make final moderation decisions for flagged content — Customers retain full control
- Is not 100% accurate and may produce false positives or false negatives
- Does not use submitted photographs to train AI models

### 4.5 GDPR and CCPA Compliance

The Service is designed to comply with the General Data Protection Regulation (GDPR) and the California Consumer Privacy Act (CCPA). Customers acting as data controllers may:

- Respond to data subject access requests via the dashboard
- Export all End User data associated with a submission
- Delete specific submissions or all data associated with an End User
- Configure data retention policies to comply with minimization principles
- Execute a Data Processing Agreement (DPA) with the Company upon request

---

## 5. Acceptable Use Policy

### 5.1 Permitted Use

The Service may be used for lawful display of user-submitted photographs in commercial, educational, nonprofit, and personal settings including but not limited to: retail stores, restaurants, bars, hotels, conferences, weddings, corporate events, houses of worship, schools, museums, and community gatherings.

### 5.2 Prohibited Use

Customers and End Users may not use the Service to:

- Submit, display, or distribute photographs depicting child sexual abuse material (CSAM). The Service reports all detected CSAM to the National Center for Missing and Exploited Children (NCMEC) as required by law.
- Submit, display, or distribute photographs that infringe the intellectual property rights of any third party without authorization.
- Submit photographs containing malware, executable code, or files designed to compromise device security.
- Circumvent or disable the content moderation system.
- Use the Service to harass, stalk, or intimidate any individual.
- Reverse engineer, decompile, or disassemble any component of the Service.
- Use automated tools to submit photographs at a rate exceeding 100 photos per minute per event.
- Resell access to the Service without written authorization from the Company.
- Use the Service to display content that violates any applicable local, state, national, or international law.

### 5.3 Content Standards

All photographs displayed through the Service must comply with the following content standards:

- No nudity or sexually explicit content (unless the Customer has enabled "Adult Venue Mode" and verified age-restriction compliance for their venue)
- No graphic violence or gore
- No hate speech, hate symbols, or discriminatory imagery
- No promotion of illegal activities
- No personally identifiable information of third parties without consent (e.g., photographs of documents, ID cards, medical records)

Customers are responsible for configuring their moderation settings appropriately for their venue and audience.

---

## 6. Service Level Agreement

### 6.1 Uptime Commitment

The Service targets the following uptime commitments:

| Component | Starter | Pro | Team/Enterprise |
|-----------|---------|-----|-----------------|
| API & Backend | 99.5% | 99.9% | 99.99% |
| Display Delivery | 99.5% | 99.9% | 99.99% |
| Dashboard | 99.5% | 99.9% | 99.99% |
| Mobile Web App | 99.5% | 99.9% | 99.99% |

Uptime is calculated monthly, excluding scheduled maintenance windows (announced 48 hours in advance).

### 6.2 Performance Guarantees

- Photo upload to Device display: under 10 seconds (from approval) for 95th percentile
- Dashboard page load: under 2 seconds for 95th percentile
- API response time: under 200ms for 95th percentile
- WebSocket reconnection: automatic within 5 seconds of connection loss
- Device heartbeat monitoring: alerts within 60 seconds of Device going offline

### 6.3 Service Credits

If the Service fails to meet the uptime commitment for any calendar month, Customers on Pro, Team, or Enterprise plans are eligible for service credits:

| Monthly Uptime | Service Credit |
|----------------|---------------|
| 99.0% - 99.9% | 10% of monthly fee |
| 95.0% - 99.0% | 25% of monthly fee |
| Below 95.0% | 50% of monthly fee |

Service credits must be requested within 30 days of the incident and are applied to future invoices. Credits do not exceed 50% of the monthly fee.

### 6.4 Disaster Recovery

Customer data is replicated across multiple availability zones. In the event of a regional outage:

- Database failover: automatic within 60 seconds
- Photo storage: replicated across 3 AWS regions
- Service restoration target: 4 hours for full service, 1 hour for display continuity

---

## 7. Intellectual Property

### 7.1 Customer Content

Customers retain all ownership rights to photographs submitted to their galleries. The Company claims no ownership of Customer content.

### 7.2 License Grant

By submitting photographs to the Service, End Users grant the Customer a non-exclusive, royalty-free license to display the photograph on the Customer's Devices for the duration of the Customer's retention policy. End Users also grant the Company a limited license to process, store, moderate, and deliver the photograph as necessary to provide the Service.

### 7.3 Company Intellectual Property

The Service, including its software, design, documentation, APIs, and trademarks, is the property of the Company. These Terms do not grant Customers any rights to the Company's intellectual property beyond the right to use the Service as described herein.

---

## 8. Device Management

### 8.1 Device Registration

Devices are registered to a Customer account using a unique registration code displayed on the Device screen. The registration process requires:

1. Install the CrowdPics TV application on the Device (or open the web-based display URL)
2. Note the 6-character registration code displayed on screen
3. Enter the code in the Customer dashboard under Devices > Add Device
4. Assign the Device a name, location, and default playlist

### 8.2 Device Monitoring

The Service continuously monitors connected Devices via heartbeat signals. Customers receive notifications when:

- A Device goes offline for more than 5 minutes
- A Device's display application requires an update
- A Device reports an error condition
- A Device's storage is more than 80% utilized

### 8.3 Remote Management

Customers may remotely perform the following actions on connected Devices:

- Change the active playlist
- Force a content refresh
- Restart the display application
- Adjust display settings (transition speed, photo duration, shuffle mode)
- Display a custom message or announcement overlay
- Put the Device in standby mode with a configurable wake schedule
- Push an application update (Fire TV and Android TV only)

### 8.4 Offline Mode

Devices cache the most recent 500 approved photographs locally. If the Device loses internet connectivity, it will continue displaying cached content in its current playlist order until connectivity is restored. Upon reconnection, the Device will sync any new content and resume normal operation.

---

## 9. Customer Onboarding

New Customer accounts are guided through a 7-step onboarding wizard:

1. **Business Profile** — Company name, industry, and venue type
2. **Branding** — Upload logo, select brand colors, customize display theme
3. **First Device** — Register and name the first display Device
4. **Moderation Settings** — Configure AI sensitivity and review preferences
5. **First Event** — Create an event with start time, submission URL, and QR code
6. **Invite Team** — Add team members with appropriate roles
7. **Test Submission** — Submit a test photo and verify it appears on the Device

Onboarding must be completed before Devices will display content. Customers may return to any step to modify settings later.

---

## 10. API Access

### 10.1 Availability

API access is available on Pro, Team, and Enterprise plans. The CrowdPics REST API allows programmatic access to:

- Photo submission and retrieval
- Event creation and management
- Device status and control
- Playlist management
- Analytics data export
- Webhook configuration
- Moderation queue management

### 10.2 Rate Limits

| Plan | Requests per Minute | Requests per Day |
|------|--------------------|--------------------|
| Pro | 60 | 10,000 |
| Team | 300 | 100,000 |
| Enterprise | Custom | Custom |

Rate-limited requests receive HTTP 429 responses with a Retry-After header.

### 10.3 API Versioning

The API is versioned. The current version is v2. Deprecated API versions receive 12 months of support after deprecation announcement. Breaking changes are never introduced within a version.

---

## 11. Support

### 11.1 Support Channels

| Channel | Starter | Pro | Team | Enterprise |
|---------|---------|-----|------|------------|
| Email | ✓ (48h response) | ✓ (4h response) | ✓ (1h response) | ✓ (30min response) |
| Live Chat | — | ✓ (business hours) | ✓ (extended hours) | ✓ (24/7) |
| Phone | — | — | ✓ (business hours) | ✓ (24/7) |
| Dedicated Account Manager | — | — | ✓ | ✓ |
| Knowledge Base | ✓ | ✓ | ✓ | ✓ |
| Community Forum | ✓ | ✓ | ✓ | ✓ |

Business hours are Monday through Friday, 9:00 AM to 6:00 PM Eastern Time (US), excluding federal holidays.

### 11.2 Severity Levels

| Severity | Description | Target Response | Target Resolution |
|----------|------------|----------------|-------------------|
| Critical | Service is down for all Devices | 30 minutes | 4 hours |
| High | Feature is non-functional for a Customer | 2 hours | 24 hours |
| Medium | Feature is degraded but functional | 8 hours | 72 hours |
| Low | Cosmetic issue or feature request | 48 hours | Best effort |

---

## 12. Termination

### 12.1 Customer-Initiated

Customers may cancel their subscription at any time from the Billing section of the dashboard. Upon cancellation:

- Service access continues until the end of the current billing period
- Devices will display a "Service Expired" message after the billing period ends
- Customer data is retained for 30 days after the billing period ends
- During the 30-day retention period, Customers may export their data or reactivate their account
- After 30 days, all Customer data including photographs, settings, and analytics is permanently deleted

### 12.2 Company-Initiated

The Company may suspend or terminate a Customer account for:

- Violation of these Terms or the Acceptable Use Policy
- Non-payment after a 14-day grace period
- Fraudulent activity
- Legal requirement

The Company will provide 7 days' notice before termination except in cases of illegal activity or imminent harm.

### 12.3 Data Portability

Upon termination, Customers may request a full data export including:

- All photographs in original resolution
- Event data and analytics in CSV/JSON format
- Device configuration data
- Team member list (without passwords)
- Audit logs for the retention period

Data export requests are processed within 72 hours.

---

## 13. Liability and Disclaimers

### 13.1 Service Provided "As Is"

The Service is provided on an "as is" and "as available" basis. The Company does not warrant that the Service will be uninterrupted, error-free, or free from harmful components.

### 13.2 Limitation of Liability

To the maximum extent permitted by law, the Company's total liability for any claims arising from or related to the Service shall not exceed the amount paid by the Customer in the 12 months preceding the claim.

### 13.3 Content Liability

The Company is not liable for content submitted by End Users. Customers are responsible for configuring and monitoring their moderation settings. The automated content moderation system is provided as a tool to assist Customers and is not guaranteed to detect all inappropriate content.

### 13.4 Third-Party Services

The Service integrates with third-party services (Stripe, AWS, etc.) that are governed by their own terms of service. The Company is not liable for the availability or performance of third-party services.

---

## 14. Modifications to Terms

The Company may modify these Terms at any time. Material changes will be communicated via email and dashboard notification at least 30 days before taking effect. Continued use of the Service after the effective date constitutes acceptance of the modified Terms. Customers who do not agree to modified Terms may cancel their subscription before the effective date for a pro-rata refund.

---

## 15. Governing Law

These Terms are governed by the laws of the Commonwealth of The Bahamas. Disputes arising from these Terms shall be resolved through binding arbitration administered by the Bahamas Chamber of Commerce, with proceedings conducted in Nassau, New Providence.

---

## 16. Contact

CrowdPics Inc.
Email: legal@crowdpics.ai
Support: support@crowdpics.ai
Website: https://crowdpics.ai
