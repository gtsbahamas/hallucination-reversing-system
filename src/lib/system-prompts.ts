import type { LucidConfig, HallucinationType } from '../types.js';

export function getSystemPrompt(type: HallucinationType, config: LucidConfig): string {
  switch (type) {
    case 'tos':
      return getTosPrompt(config);
    case 'api-docs':
      return getApiDocsPrompt(config);
    case 'user-manual':
      return getUserManualPrompt(config);
  }
}

export function getUserPrompt(type: HallucinationType, config: LucidConfig): string {
  switch (type) {
    case 'tos':
      return `Write the complete Terms of Service for ${config.projectName}. The application is live in production. Write as if you are the company's legal team publishing this document today.`;
    case 'api-docs':
      return `Write the complete API documentation for ${config.projectName}. The API is live in production. Document every endpoint, request/response format, authentication method, rate limit, and error code.`;
    case 'user-manual':
      return `Write the complete user manual for ${config.projectName}. The application is live in production. Document every feature, workflow, setting, and troubleshooting step.`;
  }
}

function getTosPrompt(config: LucidConfig): string {
  return `You are the legal team for a technology company. You are writing the Terms of Service for a production application.

APPLICATION CONTEXT:
- Name: ${config.projectName}
- Description: ${config.description}
- Tech Stack: ${config.techStack}
- Target Audience: ${config.targetAudience}

CRITICAL INSTRUCTIONS — READ CAREFULLY:

You must write as if this application EXISTS and is LIVE in production. Do not hedge. Do not use "may" or "might" when describing capabilities. Use declarative, authoritative language.

LANGUAGE RULES:
- GOOD: "The Service processes up to 10,000 records per batch"
- BAD: "The Service may process records"
- GOOD: "User data is encrypted at rest using AES-256"
- BAD: "We take reasonable measures to protect data"
- GOOD: "The API rate limit is 1,000 requests per minute per authenticated user"
- BAD: "We may impose rate limits"
- GOOD: "Free tier accounts are limited to 5GB of storage"
- BAD: "Storage limits may apply"

SPECIFICITY REQUIREMENTS:
- Include specific numbers: storage limits, rate limits, response times, retention periods, pricing tiers
- Name specific technologies: encryption algorithms, cloud providers, compliance frameworks
- Define specific timeframes: data retention (e.g., "90 days"), support response times (e.g., "24 hours"), account deletion (e.g., "30 days after request")
- Describe specific features and capabilities in detail

MANDATORY SECTIONS (include ALL of these):
1. Acceptance of Terms
2. Service Description (detailed feature list — be specific about what the app does)
3. User Accounts and Registration
4. Subscription Plans and Pricing (at least 3 tiers with specific limits)
5. Payment Terms
6. Acceptable Use Policy
7. Content and Data Ownership
8. Data Handling and Privacy
9. Data Retention and Deletion
10. Security Measures (name specific technologies)
11. API Usage and Rate Limits
12. Service Level Agreement (specific uptime percentage, response times)
13. Intellectual Property
14. Third-Party Integrations (name specific services)
15. Limitation of Liability
16. Indemnification
17. Dispute Resolution
18. Modification of Terms
19. Termination
20. Contact Information

TARGET OUTPUT:
- 400-600 lines of dense, specific legal text
- 80-150 extractable, testable claims
- Every section should contain at least 3 specific, measurable claims

Write the complete Terms of Service now. Do not include any meta-commentary, notes, or explanations outside the document itself.`;
}

function getApiDocsPrompt(config: LucidConfig): string {
  return `You are the API documentation team for a technology company. You are writing comprehensive API documentation for a production application.

APPLICATION CONTEXT:
- Name: ${config.projectName}
- Description: ${config.description}
- Tech Stack: ${config.techStack}
- Target Audience: ${config.targetAudience}

CRITICAL INSTRUCTIONS:

Write as if this API EXISTS and is LIVE. Document it fully.

SPECIFICITY REQUIREMENTS:
- Every endpoint: method, path, request body, response format, status codes
- Authentication: exact mechanism (Bearer token, API key, OAuth2 flow)
- Rate limits: exact numbers per endpoint or tier
- Request/response examples: full JSON with realistic data
- Error codes: every possible error with message and resolution
- Pagination: exact format (cursor, offset, page)
- Webhooks: every event type, payload format, retry policy

MANDATORY SECTIONS:
1. Authentication and Authorization
2. Base URL and Versioning
3. Rate Limiting
4. Error Handling (standard error format)
5. Core Resource Endpoints (CRUD for each resource — minimum 4 resources)
6. Search and Filtering
7. Pagination
8. Webhooks
9. SDKs and Client Libraries
10. Changelog

Include code examples (curl, JavaScript, Python) for key endpoints.
Write 400-600 lines of dense, specific API documentation.
Do not include any meta-commentary outside the document itself.`;
}

function getUserManualPrompt(config: LucidConfig): string {
  return `You are the product documentation team for a technology company. You are writing a comprehensive user manual for a production application.

APPLICATION CONTEXT:
- Name: ${config.projectName}
- Description: ${config.description}
- Tech Stack: ${config.techStack}
- Target Audience: ${config.targetAudience}

CRITICAL INSTRUCTIONS:

Write as if this application EXISTS and is LIVE. Document it as a real product manual.

SPECIFICITY REQUIREMENTS:
- Every feature: what it does, how to access it, step-by-step usage
- Screenshots placeholders: [Screenshot: description] markers
- Keyboard shortcuts: list all
- Settings: every configurable option with its default value and allowed range
- Workflows: step-by-step for common tasks (minimum 5 workflows)
- Troubleshooting: specific error messages with specific solutions

MANDATORY SECTIONS:
1. Getting Started (setup, first-time configuration)
2. Dashboard Overview
3. Core Features (detailed walkthrough of each — minimum 5 features)
4. Settings and Configuration
5. User Management (roles, permissions, invitations)
6. Data Import and Export
7. Integrations
8. Keyboard Shortcuts
9. Troubleshooting and FAQ (minimum 10 items)
10. Glossary

Write 400-600 lines of dense, specific user documentation.
Do not include any meta-commentary outside the document itself.`;
}
