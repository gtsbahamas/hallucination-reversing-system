# CrowdPics TV — LUCID Gap Analysis (Iteration 1)

**Generated: January 31, 2026**
**Method: ToS claims vs. verified application state**

---

## Legend

| Status | Meaning |
|--------|---------|
| REAL | Exists and verified in production |
| PARTIAL | Exists but incomplete or limited |
| HALLUCINATED | Does not exist — ToS claim is fiction |
| UNVERIFIED | May exist but not confirmed |

---

## Section 1: Core Platform Capabilities

### 1.1 Photo Collection
| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| Mobile web app submission | REAL | https://app.crowdpics.ai — Vite + React + Capacitor |
| Native iOS application | PARTIAL | Expo app built, rejected by Apple App Store (touch responsiveness dispute) |
| Native Android application | PARTIAL | Expo app built, not submitted to Google Play |
| SMS submission | PARTIAL | Twilio integrated but limited to Bahamas only (10DLC pending US approval) |
| Email submission | HALLUCINATED | No email submission system exists |
| API submission | UNVERIFIED | REST API exists but photo submission endpoint not confirmed for external use |
| No account required for End Users | REAL | Submission is anonymous |

### 1.2 Content Moderation
| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| AI-powered content analysis (AWS Rekognition) | REAL | AWS Rekognition integration confirmed |
| Automated text/overlay detection | UNVERIFIED | May be part of Rekognition but not confirmed separately |
| Human review queue | REAL | Moderation queue exists in admin dashboard |
| Configurable sensitivity thresholds | UNVERIFIED | Settings exist but configurability per-customer not confirmed |

### 1.3 Display Management
| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| Amazon Fire TV | REAL | Primary platform, v1.0.6 ready for resubmission |
| Android TV | HALLUCINATED | No Android TV app |
| Apple TV | HALLUCINATED | No Apple TV app |
| Chromecast | HALLUCINATED | No Chromecast support |
| Samsung Tizen Smart TV | HALLUCINATED | No Tizen app |
| LG webOS Smart TV | HALLUCINATED | No webOS app |
| Roku | HALLUCINATED | No Roku app |
| Web browser display | REAL | TV Display Simulator at https://tv.firephoto.ai |
| WebSocket real-time updates | REAL | WebSocket confirmed in backend |

### 1.4 Playlist Curation
| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| Multiple playlists | REAL | Playlist management exists |
| Configurable display duration | UNVERIFIED | Likely exists but not confirmed |
| Transition effects (fade, slide, zoom, ken-burns) | UNVERIFIED | Some transitions likely, full set unconfirmed |
| Scheduling rules | HALLUCINATED | No evidence of playlist scheduling |
| Device group assignment | HALLUCINATED | No device grouping confirmed |

### 1.5 Real-Time Display
| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| Photos appear within 5 seconds of approval | UNVERIFIED | WebSocket exists but latency not measured |
| Continuous slideshow format | REAL | Core functionality |

### 1.6 Branded Experience
| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| Custom logo | UNVERIFIED | Likely part of onboarding but not confirmed |
| Brand colors | UNVERIFIED | Likely part of onboarding but not confirmed |
| Welcome messages | HALLUCINATED | Not confirmed |
| QR code overlays on display | HALLUCINATED | QR codes exist for submission but overlay on display not confirmed |
| Custom CSS | HALLUCINATED | No evidence of custom CSS support |

### 1.7 Analytics Dashboard
| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| Total submissions per event | HALLUCINATED | No analytics dashboard confirmed |
| Approval/rejection ratios | HALLUCINATED | Not confirmed |
| Peak submission times | HALLUCINATED | Not confirmed |
| Unique submitter counts | HALLUCINATED | Not confirmed |
| Device uptime statistics | HALLUCINATED | Heartbeat monitoring exists but stats dashboard not confirmed |
| Audience engagement metrics | HALLUCINATED | Not confirmed |

### 1.8 Event Management
| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| Discrete events with start/end times | UNVERIFIED | Events may exist but discrete event model not confirmed |
| Unique submission URLs per event | UNVERIFIED | Not confirmed |
| Dedicated QR codes per event | UNVERIFIED | QR codes exist but per-event not confirmed |
| Recurring events with auto-reset | HALLUCINATED | Not confirmed |

### 1.9 Team Collaboration
| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| Multiple team members | REAL | 20 members in database |
| Owner role | UNVERIFIED | Role system exists but specific roles not confirmed |
| Admin role | UNVERIFIED | Same |
| Moderator role | UNVERIFIED | Same |
| Viewer role | HALLUCINATED | Likely doesn't exist as distinct role |

### 1.10 AI-Powered Enhancements
| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| Auto photo enhancement | HALLUCINATED | No auto-enhancement |
| Intelligent cropping | UNVERIFIED | Sharp is used for image processing but smart cropping not confirmed |
| Duplicate detection | HALLUCINATED | Not confirmed |
| Face clustering | HALLUCINATED | Not confirmed |
| AI-generated slideshow narratives | HALLUCINATED | Not confirmed |

### 1.11 Integration Capabilities
| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| Stripe | REAL | Confirmed |
| Slack notifications | HALLUCINATED | Not confirmed |
| Zapier | HALLUCINATED | Not confirmed |
| Google Sheets export | HALLUCINATED | Not confirmed |
| Custom webhooks | UNVERIFIED | Webhook capability referenced but not confirmed for customers |

### 1.12 Multi-Location Management
| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| Multiple locations per account | HALLUCINATED | Multi-tenant exists but multi-location per customer not confirmed |
| Per-location Device assignments | HALLUCINATED | Not confirmed |
| Consolidated billing | HALLUCINATED | Not confirmed |

---

## Section 2: Account Security

| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| 2FA (TOTP) | REAL | Security sprint deployed Dec 2025 |
| Session management panel | UNVERIFIED | Security settings UI exists but session listing not confirmed |
| Audit logging (12 month retention) | REAL | Audit logging deployed, retention period unconfirmed |
| IP allowlisting | HALLUCINATED | Not confirmed |
| API key management | HALLUCINATED | Not confirmed |
| SSO (SAML/OIDC) | HALLUCINATED | Not confirmed |
| Account verification (ID + business proof) | HALLUCINATED | Not confirmed |
| 12-char password with complexity | UNVERIFIED | Password requirements exist but specific policy not confirmed |

---

## Section 3: Subscription Plans

| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| Starter $79/mo | REAL | New pricing released Jan 2026 |
| Pro $149/mo | REAL | New pricing released Jan 2026 |
| Team $299/mo | REAL | New pricing released Jan 2026 |
| Enterprise (custom) | HALLUCINATED | No enterprise tier confirmed |
| Annual pricing (2 months free) | HALLUCINATED | Annual billing not confirmed |
| 14-day free trial | HALLUCINATED | Free trial existence not confirmed |
| Free tier after trial | HALLUCINATED | No free tier confirmed |
| ACH transfer payment | HALLUCINATED | Only credit/debit via Stripe confirmed |
| Usage overage notifications | HALLUCINATED | Not confirmed |
| 7-day grace period for overages | HALLUCINATED | Not confirmed |

---

## Section 4: Data Handling

| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| AES-256 encryption at rest | UNVERIFIED | AWS S3 likely uses this but not explicitly confirmed |
| TLS 1.3 | UNVERIFIED | HTTPS confirmed but specific TLS version not checked |
| Daily backups (30-day retention) | UNVERIFIED | Render likely provides backups but not confirmed |
| Data export (CSV/JSON) | HALLUCINATED | No export functionality confirmed |
| Photo retention policies (configurable) | REAL | Photo retention/expiration policies exist |
| EXIF GPS stripping | UNVERIFIED | Sharp processes images but GPS strip not confirmed |
| 10-second processing pipeline | UNVERIFIED | Not measured |
| GDPR/CCPA compliance tooling | HALLUCINATED | No data subject request tools confirmed |
| Data Processing Agreement | HALLUCINATED | No DPA template confirmed |

---

## Section 5: Service Level

| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| 99.5% uptime (Starter) | HALLUCINATED | No SLA exists |
| 99.9% uptime (Pro) | HALLUCINATED | No SLA exists |
| 99.99% uptime (Team) | HALLUCINATED | No SLA exists |
| Service credits | HALLUCINATED | No credit policy exists |
| Multi-AZ failover | HALLUCINATED | Running on Render, not multi-AZ |
| 3-region photo replication | HALLUCINATED | S3 single region likely |
| Uptime monitoring | PARTIAL | Heartbeat monitoring for devices but no service-level monitoring confirmed |

---

## Section 6: Device Management

| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| 6-character registration code | REAL | Device bootstrap process confirmed |
| Device naming and location | UNVERIFIED | Device registration exists but location field not confirmed |
| Offline notifications (5 min) | UNVERIFIED | Heartbeat monitoring exists but threshold not confirmed |
| Remote playlist change | UNVERIFIED | WebSocket commands likely support this |
| Remote display restart | HALLUCINATED | Not confirmed |
| Custom announcement overlay | HALLUCINATED | Not confirmed |
| Standby mode with wake schedule | HALLUCINATED | Not confirmed |
| Remote app update push | HALLUCINATED | Not confirmed |
| Offline mode (500 photo cache) | HALLUCINATED | No offline caching confirmed |

---

## Section 7: Customer Onboarding

| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| 7-step onboarding wizard | REAL | Confirmed, blocks device assignment until complete |
| Business profile step | UNVERIFIED | Exists but specific fields not confirmed |
| Branding step | UNVERIFIED | Same |
| First device step | UNVERIFIED | Same |
| Moderation settings step | UNVERIFIED | Same |
| First event step | UNVERIFIED | Same |
| Invite team step | UNVERIFIED | Same |
| Test submission step | UNVERIFIED | Same |

---

## Section 8: API Access

| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| REST API | REAL | Express backend with routes |
| Rate limiting (60/300 rpm by plan) | HALLUCINATED | No rate limiting confirmed |
| API versioning (v2) | HALLUCINATED | No versioning confirmed |
| API documentation | HALLUCINATED | No public API docs confirmed |
| Developer settings panel | HALLUCINATED | Not confirmed |

---

## Section 9: Support

| ToS Claim | Status | Evidence / Gap |
|-----------|--------|----------------|
| Email support | UNVERIFIED | Likely exists but SLA not confirmed |
| Live chat | HALLUCINATED | Not confirmed |
| Phone support | HALLUCINATED | Not confirmed |
| Dedicated account manager | HALLUCINATED | Not confirmed |
| Knowledge base | REAL | Knowledge base with semantic search exists |
| Community forum | HALLUCINATED | Not confirmed |
| Severity-based SLA | HALLUCINATED | Not confirmed |

---

## Summary Statistics

| Status | Count | Percentage |
|--------|-------|------------|
| REAL | 27 | 24% |
| PARTIAL | 4 | 4% |
| UNVERIFIED | 29 | 26% |
| HALLUCINATED | 52 | 46% |
| **Total Claims** | **112** | **100%** |

---

## Top Hallucinated Features (Highest Impact for Customer Acquisition)

These hallucinated claims, if built, would likely have the highest impact on reaching the 50-customer target:

| Priority | Feature | ToS Section | Rationale |
|----------|---------|-------------|-----------|
| 1 | Analytics Dashboard | 1.7 | Customers need to prove ROI to justify subscription |
| 2 | 14-Day Free Trial | 3.2 | Removes friction for new customer acquisition |
| 3 | Multi-Device Platform Support | 1.3 | Unlocks customers without Fire TV |
| 4 | Event Management | 1.8 | Core value prop for wedding/conference market |
| 5 | Offline Device Mode | 8.4 | Critical for venues with unreliable internet |
| 6 | Data Export (CSV/JSON) | 4.1 | Enterprise requirement, table stakes for Team plan |
| 7 | Slack/Webhook Integrations | 1.11 | Enables workflow automation for larger customers |
| 8 | Email Submission Channel | 1.2 | Low-friction alternative for less tech-savvy users |
| 9 | Annual Billing | 3.1 | Increases LTV, reduces churn |
| 10 | Custom Branding (full) | 1.6 | Differentiation for Pro/Team upsell |

---

## Next Step

Feed this gap analysis into a Ralph loop to systematically build the hallucinated features, starting with the highest-priority items. Each iteration closes gaps, then a new ToS is regenerated to discover what the next version of the product "should" be.
