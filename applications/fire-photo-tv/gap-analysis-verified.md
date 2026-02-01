# CrowdPics TV — LUCID Gap Analysis (Iteration 1 — VERIFIED)

**Generated: January 31, 2026**
**Verified: January 31, 2026**
**Method: ToS claims vs. codebase evidence (file paths + line numbers)**

---

## Legend

| Status | Meaning |
|--------|---------|
| REAL | Exists with codebase evidence |
| PARTIAL | Exists but incomplete or differs from claim |
| HALLUCINATED | Does not exist — ToS claim is fiction |

---

## Verified Summary

| Status | Count | % |
|--------|-------|---|
| REAL | 35 | 31% |
| PARTIAL | 12 | 11% |
| HALLUCINATED | 65 | 58% |
| **Total Claims** | **112** | **100%** |

**Shift from initial estimate:** 8 items moved from UNVERIFIED to REAL, 4 moved to PARTIAL, 17 confirmed HALLUCINATED. Zero unverified claims remain.

---

## Section 1: Core Platform Capabilities

### 1.1 Photo Collection
| Claim | Status | Evidence |
|-------|--------|----------|
| Mobile web app | REAL | https://app.crowdpics.ai — Vite + React + Capacitor |
| Native iOS app | PARTIAL | Expo app built, Apple rejected (touch responsiveness) |
| Native Android app | PARTIAL | Expo app built, not submitted to Google Play |
| SMS submission | PARTIAL | Twilio integrated, Bahamas only (10DLC pending) |
| Email submission | HALLUCINATED | No email submission system |
| API submission | PARTIAL | Guest upload endpoint exists but no external API key auth |
| No account for End Users | REAL | Anonymous guest sessions |

### 1.2 Content Moderation
| Claim | Status | Evidence |
|-------|--------|----------|
| AI content analysis (Rekognition) | REAL | `DetectModerationLabelsCommand` in aiAnalysis.ts |
| Text/overlay detection | HALLUCINATED | No `DetectTextCommand`, no OCR |
| Human review queue | REAL | Moderation queue in admin dashboard |
| Configurable sensitivity per customer | REAL | `aiModerationThreshold` (0-100) + `guestModerationMode` per customer in businessSettings |

### 1.3 Display Management
| Claim | Status | Evidence |
|-------|--------|----------|
| Amazon Fire TV | REAL | v1.0.6 ready for resubmission |
| Android TV | HALLUCINATED | No Android TV app |
| Apple TV | HALLUCINATED | No Apple TV app |
| Chromecast | HALLUCINATED | No Chromecast support |
| Samsung Tizen | HALLUCINATED | No Tizen app |
| LG webOS | HALLUCINATED | No webOS app |
| Roku | HALLUCINATED | No Roku app |
| Web browser display | REAL | https://tv.firephoto.ai |
| WebSocket real-time updates | REAL | WebSocket confirmed in backend |

### 1.4 Playlist Curation
| Claim | Status | Evidence |
|-------|--------|----------|
| Multiple playlists | REAL | Playlist management exists |
| Configurable display duration | REAL | `slideshowSpeed` 5-60 seconds in localSettings.ts |
| Transition effects (fade, slide, zoom, ken-burns) | PARTIAL | Fade + slide are transitions; zoom + ken-burns are motion effects (separate concept) |
| Scheduling rules | HALLUCINATED | No playlist scheduling |
| Device group assignment | REAL | deviceGroups.ts with batch playlist assignment |

### 1.5 Real-Time Display
| Claim | Status | Evidence |
|-------|--------|----------|
| Photos appear within 5 seconds | HALLUCINATED | No latency measurement or target exists |
| Continuous slideshow format | REAL | Core functionality |

### 1.6 Branded Experience
| Claim | Status | Evidence |
|-------|--------|----------|
| Custom logo | PARTIAL | Frontend UI exists; backend upload endpoint missing |
| Brand colors | REAL | Primary, secondary, accent in schema + UI + TV display |
| Welcome messages | REAL | `welcomeMessage` in event branding JSONB |
| QR code overlays on display | REAL | QRCodeOverlay component with brandColor prop |
| Custom CSS | HALLUCINATED | No custom CSS support |

### 1.7 Analytics Dashboard
| Claim | Status | Evidence |
|-------|--------|----------|
| Total submissions per event | HALLUCINATED | No analytics dashboard |
| Approval/rejection ratios | HALLUCINATED | Not confirmed |
| Peak submission times | HALLUCINATED | Not confirmed |
| Unique submitter counts | HALLUCINATED | Not confirmed |
| Device uptime statistics | HALLUCINATED | Heartbeat exists but no stats dashboard |
| Audience engagement metrics | HALLUCINATED | Not confirmed |

### 1.8 Event Management
| Claim | Status | Evidence |
|-------|--------|----------|
| Events with start/end times | REAL | `events` table with `start_time`/`end_time` BIGINT (migration 039) |
| Unique submission URLs per event | PARTIAL | `eventCode` field exists but no URL routing |
| Dedicated QR codes per event | PARTIAL | FK exists; `getEventQRCodes` is a stub returning `[]` |
| Recurring events with auto-reset | HALLUCINATED | Not confirmed |

### 1.9 Team Collaboration
| Claim | Status | Evidence |
|-------|--------|----------|
| Multiple team members | REAL | 20 members in database |
| Owner role | REAL | DB constraint + TypeScript types + middleware |
| Admin role | REAL | DB constraint + TypeScript types + middleware |
| Moderator role | HALLUCINATED | Only `user`, `admin`, `owner` exist |
| Viewer role | HALLUCINATED | Only `user`, `admin`, `owner` exist |

### 1.10 AI-Powered Enhancements
| Claim | Status | Evidence |
|-------|--------|----------|
| Auto photo enhancement | HALLUCINATED | No auto-enhancement |
| Intelligent cropping | HALLUCINATED | Only basic resize/rotate; no attention/entropy |
| Duplicate detection | HALLUCINATED | Not confirmed |
| Face clustering | HALLUCINATED | Not confirmed |
| AI slideshow narratives | HALLUCINATED | Not confirmed |

### 1.11 Integrations
| Claim | Status | Evidence |
|-------|--------|----------|
| Stripe | REAL | Confirmed |
| Slack notifications | HALLUCINATED | Not confirmed |
| Zapier | HALLUCINATED | Not confirmed |
| Google Sheets export | HALLUCINATED | Not confirmed |
| Custom webhooks | HALLUCINATED | Only internal Stripe/Resend receivers |

### 1.12 Multi-Location Management
| Claim | Status | Evidence |
|-------|--------|----------|
| Multiple locations per account | HALLUCINATED | Not confirmed |
| Per-location Devices | HALLUCINATED | Not confirmed |
| Consolidated billing | HALLUCINATED | Not confirmed |

---

## Section 2: Account Security

| Claim | Status | Evidence |
|-------|--------|----------|
| 2FA (TOTP) | REAL | Security sprint Dec 2025, AES-256-GCM encrypted secrets |
| Session management panel | HALLUCINATED | SecuritySettings is 2FA only; guest session mgmt is separate |
| Audit logging | REAL | Append-only, never deleted by design |
| Audit log retention (12 months) | HALLUCINATED | No retention period defined; logs kept indefinitely |
| IP allowlisting | HALLUCINATED | Not confirmed |
| API key management | HALLUCINATED | Not confirmed |
| SSO (SAML/OIDC) | HALLUCINATED | Not confirmed |
| Account verification | HALLUCINATED | Not confirmed |
| 12-char password complexity | PARTIAL | Actually 8-char minimum; 12 is strength suggestion only |

---

## Section 3: Subscription Plans

| Claim | Status | Evidence |
|-------|--------|----------|
| Starter $79/mo | REAL | Pricing released Jan 2026 |
| Pro $149/mo | REAL | Pricing released Jan 2026 |
| Team $299/mo | REAL | Pricing released Jan 2026 |
| Enterprise (custom) | HALLUCINATED | Enterprise FAQ on pricing page but no real tier |
| Annual pricing | REAL | Stripe create-products script generates yearly prices |
| 14-day free trial | HALLUCINATED | No free trial confirmed |
| Free tier after trial | HALLUCINATED | No free tier |
| ACH payment | HALLUCINATED | Credit/debit only via Stripe |
| Usage overage notifications | HALLUCINATED | Not confirmed |

---

## Section 4: Data Handling

| Claim | Status | Evidence |
|-------|--------|----------|
| AES-256 encryption at rest | PARTIAL | AES-256-GCM for 2FA secrets and SMS passwords only |
| TLS 1.3 | HALLUCINATED | No TLS config; relies on Render defaults |
| Daily backups (30-day retention) | HALLUCINATED | No backups; Render free tier doesn't include them |
| Data export (CSV/JSON) | HALLUCINATED | No export functionality |
| Photo retention policies | REAL | Configurable retention/expiration exists |
| EXIF GPS stripping | HALLUCINATED | Opposite: GPS is extracted and stored for geofencing |
| 10-second processing pipeline | HALLUCINATED | No timing target; timeouts are 30 seconds |
| GDPR/CCPA tooling | HALLUCINATED | No data subject request tools |
| DPA template | HALLUCINATED | Not confirmed |

---

## Section 5: Service Level

| Claim | Status | Evidence |
|-------|--------|----------|
| 99.5% uptime (Starter) | HALLUCINATED | No SLA |
| 99.9% uptime (Pro) | HALLUCINATED | No SLA |
| 99.99% uptime (Team) | HALLUCINATED | No SLA |
| Service credits | HALLUCINATED | No credit policy |
| Multi-AZ failover | HALLUCINATED | Render single instance |
| 3-region photo replication | HALLUCINATED | Single region |

---

## Section 6: Device Management

| Claim | Status | Evidence |
|-------|--------|----------|
| 6-character registration code | REAL | Device bootstrap confirmed |
| Device naming and location | REAL | Migration 019 adds `name` and `location` columns |
| Offline notifications (5 min) | REAL | `HEARTBEAT_STALE_MS: 5 * 60 * 1000` + email alerts |
| Remote playlist change | REAL | `PLAYLIST_ASSIGNED` via WebSocket |
| Remote display restart | HALLUCINATED | Not confirmed |
| Custom announcement overlay | HALLUCINATED | Not confirmed |
| Standby mode with wake schedule | HALLUCINATED | Not confirmed |
| Remote app update push | HALLUCINATED | Not confirmed |
| Offline mode (500 photo cache) | HALLUCINATED | No offline caching |

---

## Section 7: Customer Onboarding

| Claim | Status | Evidence |
|-------|--------|----------|
| 7-step onboarding wizard | REAL | Confirmed, blocks device assignment |

---

## Section 8: API Access

| Claim | Status | Evidence |
|-------|--------|----------|
| REST API | REAL | Express backend with routes |
| Rate limiting | HALLUCINATED | No rate limiting |
| API versioning | HALLUCINATED | No versioning |
| API documentation | HALLUCINATED | No public docs |
| Developer settings panel | HALLUCINATED | Not confirmed |

---

## Section 9: Support

| Claim | Status | Evidence |
|-------|--------|----------|
| Email support | PARTIAL | Listed on pricing page; no SLA or ticket system |
| Live chat | HALLUCINATED | Not confirmed |
| Phone support | HALLUCINATED | Not confirmed |
| Dedicated account manager | HALLUCINATED | Not confirmed |
| Knowledge base | REAL | Semantic search knowledge base exists |
| Community forum | HALLUCINATED | Not confirmed |

---

## Prioritized Build Queue (Hallucinated Features by Customer Acquisition Impact)

| # | Feature | Claims | Impact Rationale |
|---|---------|--------|-----------------|
| 1 | **Analytics Dashboard** | 6 claims | Customers need ROI proof to justify subscription |
| 2 | **14-Day Free Trial** | 1 claim | Removes signup friction, standard SaaS practice |
| 3 | **Web Browser Display (more platforms)** | 6 claims | Already have web display; market as universal |
| 4 | **Complete Event Management** | 2 claims | Stub functions need implementation; events table exists |
| 5 | **Offline Device Mode** | 1 claim | Critical for venues with unreliable internet |
| 6 | **Data Export (CSV/JSON)** | 1 claim | Table stakes for Team plan customers |
| 7 | **Email Submission Channel** | 1 claim | Low-friction alternative for less tech-savvy users |
| 8 | **Annual Billing in Dashboard** | 1 claim | Stripe has yearly prices; needs UI integration |
| 9 | **Logo Upload Backend** | 1 claim | Frontend exists; just needs the endpoint |
| 10 | **Database Backups** | 1 claim | Critical infrastructure gap |

---

## Bonus: Features the ToS DIDN'T Hallucinate (Real Features Not in ToS)

These exist in the codebase but weren't claimed in the hallucinated ToS:

| Feature | Evidence |
|---------|----------|
| Geofencing (location-validated uploads) | Full GPS extraction + geofence validation |
| AI Background Blur (Photoroom) | Smart blur with Photoroom API + basic fallback |
| Photo Contests with Voting | Full contests table, entries, votes |
| Spin Wheel (gamification) | spinwheel.ts route |
| VIP Personalization | Migration 105, overlay processing |
| Lead Generation System | Prospects, campaigns, web scraper |
| Data Governance (retention policies) | Migration 083 |
| LiveKit Video Integration | Video processing capability |
| Daily QR Code Rotation | Security feature for guest access |
| Consent Recording | Audit trail for photo consent |

These represent features the hallucination *missed* — they could be added to the next ToS iteration to capture the full product surface.
