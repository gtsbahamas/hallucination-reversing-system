"""Track 4: Feature Addition task specifications.

15 feature-addition tasks based on real-world patterns.
Each task provides a base repo, a feature request, and a test suite.
Success = all tests pass (existing + new feature tests).
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


REPOS_DIR = Path(__file__).parent / "repos"


class Complexity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class FeatTaskSpec:
    """Specification for a single feature addition task."""
    task_id: str
    title: str
    complexity: Complexity
    base_repo: str            # directory name under repos/
    feature_request: str      # the prompt given to the platform
    existing_test_count: int  # tests that should pass BEFORE and AFTER
    feature_test_count: int   # tests that should FAIL before, PASS after
    tech_stack: str
    timeout_seconds: int = 600

    @property
    def repo_path(self) -> Path:
        return REPOS_DIR / self.base_repo

    @property
    def total_tests(self) -> int:
        return self.existing_test_count + self.feature_test_count


# ---------------------------------------------------------------------------
# FEAT-01: Express API -- Add Rate Limiting (Low)
# ---------------------------------------------------------------------------

FEAT_01 = FeatTaskSpec(
    task_id="FEAT-01",
    title="Express API: Add Rate Limiting Middleware",
    complexity=Complexity.LOW,
    base_repo="feat01_express_rate_limit",
    feature_request=(
        "Add rate limiting middleware to this Express API. Requirements:\n"
        "1. Limit each IP to 100 requests per 15-minute window\n"
        "2. Return 429 status with JSON error when limit exceeded\n"
        "3. Include X-RateLimit-Limit, X-RateLimit-Remaining, and "
        "X-RateLimit-Reset headers in all responses\n"
        "4. The /health endpoint should be exempt from rate limiting\n"
        "5. Use in-memory storage (no Redis required)\n"
        "All existing tests must continue to pass."
    ),
    existing_test_count=5,
    feature_test_count=6,
    tech_stack="Node.js / Express",
)

# ---------------------------------------------------------------------------
# FEAT-02: React Todo App -- Add Drag-and-Drop Reordering (Low)
# ---------------------------------------------------------------------------

FEAT_02 = FeatTaskSpec(
    task_id="FEAT-02",
    title="React Todo App: Add Drag-and-Drop Reordering",
    complexity=Complexity.LOW,
    base_repo="feat02_react_dnd",
    feature_request=(
        "Add drag-and-drop reordering to this React todo app. Requirements:\n"
        "1. Users can drag todo items to reorder them\n"
        "2. The new order persists to localStorage\n"
        "3. Completed items can be dragged too\n"
        "4. Visual feedback during drag (dragged item styled differently)\n"
        "5. The reorder must use HTML5 drag-and-drop API or a library "
        "like @dnd-kit or react-beautiful-dnd\n"
        "All existing tests must continue to pass."
    ),
    existing_test_count=6,
    feature_test_count=5,
    tech_stack="React + TypeScript",
)

# ---------------------------------------------------------------------------
# FEAT-03: Flask Blog -- Add Markdown Support (Low)
# ---------------------------------------------------------------------------

FEAT_03 = FeatTaskSpec(
    task_id="FEAT-03",
    title="Flask Blog: Add Markdown Support to Posts",
    complexity=Complexity.LOW,
    base_repo="feat03_flask_markdown",
    feature_request=(
        "Add Markdown rendering support to this Flask blog. Requirements:\n"
        "1. Post content is stored as raw Markdown\n"
        "2. When viewing a post, render the Markdown as HTML\n"
        "3. Support: headings, bold, italic, links, code blocks, lists\n"
        "4. Sanitize HTML output to prevent XSS attacks\n"
        "5. The edit form should still show raw Markdown\n"
        "All existing tests must continue to pass."
    ),
    existing_test_count=5,
    feature_test_count=6,
    tech_stack="Python / Flask",
)

# ---------------------------------------------------------------------------
# FEAT-04: Next.js Portfolio -- Add Dark Mode (Medium)
# ---------------------------------------------------------------------------

FEAT_04 = FeatTaskSpec(
    task_id="FEAT-04",
    title="Next.js Portfolio: Add Dark Mode Toggle with Persistence",
    complexity=Complexity.MEDIUM,
    base_repo="feat04_nextjs_darkmode",
    feature_request=(
        "Add a dark mode toggle to this Next.js portfolio site. Requirements:\n"
        "1. Toggle button switches between light and dark themes\n"
        "2. Theme preference persists in localStorage\n"
        "3. Respect system preference (prefers-color-scheme) on first visit\n"
        "4. No flash of wrong theme on page load (SSR-safe)\n"
        "5. All colors should change: background, text, borders, cards\n"
        "6. Toggle shows sun/moon icon based on current theme\n"
        "All existing tests must continue to pass."
    ),
    existing_test_count=4,
    feature_test_count=6,
    tech_stack="Next.js + TypeScript",
)

# ---------------------------------------------------------------------------
# FEAT-05: Django REST API -- Add JWT Authentication (Medium)
# ---------------------------------------------------------------------------

FEAT_05 = FeatTaskSpec(
    task_id="FEAT-05",
    title="Django REST API: Add JWT Authentication",
    complexity=Complexity.MEDIUM,
    base_repo="feat05_django_jwt",
    feature_request=(
        "Add JWT authentication to this Django REST API. Requirements:\n"
        "1. POST /api/auth/register -- create user with email + password\n"
        "2. POST /api/auth/login -- return access + refresh tokens\n"
        "3. POST /api/auth/refresh -- refresh an expired access token\n"
        "4. Protect existing /api/items/ endpoints -- require valid token\n"
        "5. Access token expires in 15 minutes, refresh in 7 days\n"
        "6. Return proper 401 for invalid/expired tokens\n"
        "All existing tests must continue to pass."
    ),
    existing_test_count=5,
    feature_test_count=8,
    tech_stack="Python / Django REST Framework",
)

# ---------------------------------------------------------------------------
# FEAT-06 through FEAT-15: Specs + stubs (higher complexity)
# ---------------------------------------------------------------------------

FEAT_06 = FeatTaskSpec(
    task_id="FEAT-06",
    title="React Dashboard: Add CSV Export for Data Tables",
    complexity=Complexity.MEDIUM,
    base_repo="feat06_react_csv_export",
    feature_request=(
        "Add CSV export functionality to the data tables in this React dashboard.\n"
        "1. Export button on each table\n"
        "2. Exports currently visible (filtered/sorted) data\n"
        "3. Proper CSV escaping for commas, quotes, newlines\n"
        "4. UTF-8 BOM for Excel compatibility\n"
        "5. Filename includes table name and date\n"
        "All existing tests must continue to pass."
    ),
    existing_test_count=4,
    feature_test_count=5,
    tech_stack="React + TypeScript",
)

FEAT_07 = FeatTaskSpec(
    task_id="FEAT-07",
    title="Express + Postgres: Add Full-Text Search",
    complexity=Complexity.MEDIUM,
    base_repo="feat07_express_fts",
    feature_request=(
        "Add full-text search to this Express + Postgres API.\n"
        "1. GET /api/search?q=<query> endpoint\n"
        "2. Search across title and description fields\n"
        "3. Results ranked by relevance\n"
        "4. Highlight matching terms in results\n"
        "5. Support quoted phrases for exact match\n"
        "All existing tests must continue to pass."
    ),
    existing_test_count=4,
    feature_test_count=5,
    tech_stack="Node.js / Express / PostgreSQL",
)

FEAT_08 = FeatTaskSpec(
    task_id="FEAT-08",
    title="Vue.js E-commerce: Add Product Filtering",
    complexity=Complexity.MEDIUM,
    base_repo="feat08_vue_filtering",
    feature_request=(
        "Add product filtering to this Vue.js e-commerce app.\n"
        "1. Filter by price range (min/max slider)\n"
        "2. Filter by category (checkbox list)\n"
        "3. Filter by rating (star rating selector)\n"
        "4. Filters combine with AND logic\n"
        "5. URL reflects filter state for shareable links\n"
        "All existing tests must continue to pass."
    ),
    existing_test_count=4,
    feature_test_count=5,
    tech_stack="Vue.js + TypeScript",
)

FEAT_09 = FeatTaskSpec(
    task_id="FEAT-09",
    title="FastAPI + SQLAlchemy: Add Cursor Pagination",
    complexity=Complexity.MEDIUM,
    base_repo="feat09_fastapi_pagination",
    feature_request=(
        "Add cursor-based pagination to this FastAPI + SQLAlchemy API.\n"
        "1. Replace offset pagination with cursor-based\n"
        "2. Return next_cursor and prev_cursor in responses\n"
        "3. Support configurable page_size (max 100)\n"
        "4. Stable ordering even with concurrent inserts\n"
        "5. Cursor is opaque (base64-encoded)\n"
        "All existing tests must continue to pass."
    ),
    existing_test_count=4,
    feature_test_count=5,
    tech_stack="Python / FastAPI / SQLAlchemy",
)

FEAT_10 = FeatTaskSpec(
    task_id="FEAT-10",
    title="React + Firebase: Add Real-Time Notifications",
    complexity=Complexity.HARD,
    base_repo="feat10_react_notifications",
    feature_request=(
        "Add real-time notifications to this React + Firebase app.\n"
        "1. Notification bell with unread count badge\n"
        "2. Dropdown showing recent notifications\n"
        "3. Mark individual or all notifications as read\n"
        "4. Real-time updates via Firebase listeners\n"
        "5. Notification types: info, success, warning, error\n"
        "6. Toast notification for new items\n"
        "All existing tests must continue to pass."
    ),
    existing_test_count=4,
    feature_test_count=6,
    tech_stack="React + Firebase",
)

FEAT_11 = FeatTaskSpec(
    task_id="FEAT-11",
    title="Django Multi-Tenant: Add Per-Tenant Stripe Billing",
    complexity=Complexity.HARD,
    base_repo="feat11_django_billing",
    feature_request=(
        "Add per-tenant billing with Stripe to this Django multi-tenant app.\n"
        "1. Each tenant has a Stripe customer ID\n"
        "2. Subscription management (create, cancel, upgrade)\n"
        "3. Webhook handler for payment events\n"
        "4. Usage metering for overage charges\n"
        "5. Billing portal redirect for self-serve management\n"
        "All existing tests must continue to pass."
    ),
    existing_test_count=4,
    feature_test_count=7,
    tech_stack="Python / Django / Stripe",
)

FEAT_12 = FeatTaskSpec(
    task_id="FEAT-12",
    title="Next.js SaaS: Add Team Invitation Flow",
    complexity=Complexity.HARD,
    base_repo="feat12_nextjs_invitations",
    feature_request=(
        "Add team invitation flow with email to this Next.js SaaS app.\n"
        "1. Invite form (email + role selection)\n"
        "2. Invitation email with unique token link\n"
        "3. Accept invitation page (creates account or links existing)\n"
        "4. Pending invitations list with resend/revoke\n"
        "5. Role assignment on join (admin, member, viewer)\n"
        "6. Invitation expires after 7 days\n"
        "All existing tests must continue to pass."
    ),
    existing_test_count=4,
    feature_test_count=7,
    tech_stack="Next.js + TypeScript",
)

FEAT_13 = FeatTaskSpec(
    task_id="FEAT-13",
    title="Express + Redis: Add Job Queue with Retry",
    complexity=Complexity.HARD,
    base_repo="feat13_express_job_queue",
    feature_request=(
        "Add a job queue with retry and dead-letter to this Express app.\n"
        "1. POST /api/jobs to enqueue a job\n"
        "2. Worker processes jobs from Redis queue\n"
        "3. Failed jobs retry up to 3 times with exponential backoff\n"
        "4. Jobs that exceed retries go to dead-letter queue\n"
        "5. GET /api/jobs/:id returns job status\n"
        "6. GET /api/jobs/dead-letter lists failed jobs\n"
        "All existing tests must continue to pass."
    ),
    existing_test_count=4,
    feature_test_count=7,
    tech_stack="Node.js / Express / Redis",
)

FEAT_14 = FeatTaskSpec(
    task_id="FEAT-14",
    title="React + GraphQL: Add Optimistic UI Updates",
    complexity=Complexity.HARD,
    base_repo="feat14_react_optimistic",
    feature_request=(
        "Add optimistic UI updates with rollback to this React + GraphQL app.\n"
        "1. Mutations update UI immediately before server response\n"
        "2. On server error, roll back to previous state\n"
        "3. Show error toast on rollback\n"
        "4. Handle concurrent optimistic updates\n"
        "5. Loading states during server confirmation\n"
        "All existing tests must continue to pass."
    ),
    existing_test_count=4,
    feature_test_count=6,
    tech_stack="React + Apollo GraphQL",
)

FEAT_15 = FeatTaskSpec(
    task_id="FEAT-15",
    title="Full-Stack App: Add End-to-End Encryption",
    complexity=Complexity.HARD,
    base_repo="feat15_e2e_encryption",
    feature_request=(
        "Add end-to-end encryption for messages in this full-stack app.\n"
        "1. Generate key pair per user (Web Crypto API)\n"
        "2. Encrypt messages with recipient's public key\n"
        "3. Decrypt messages with own private key\n"
        "4. Key exchange protocol on first message\n"
        "5. Private key stored encrypted in localStorage\n"
        "6. Server never sees plaintext message content\n"
        "All existing tests must continue to pass."
    ),
    existing_test_count=4,
    feature_test_count=7,
    tech_stack="Node.js / React / Web Crypto API",
)

# ---------------------------------------------------------------------------
# Collected task list
# ---------------------------------------------------------------------------

FEAT_TASKS: List[FeatTaskSpec] = [
    FEAT_01, FEAT_02, FEAT_03, FEAT_04, FEAT_05,  # Low/Medium
    FEAT_06, FEAT_07, FEAT_08, FEAT_09, FEAT_10,  # Medium/Hard
    FEAT_11, FEAT_12, FEAT_13, FEAT_14, FEAT_15,  # Hard
]

TASKS_BY_ID = {t.task_id: t for t in FEAT_TASKS}
TASKS_BY_COMPLEXITY = {
    Complexity.LOW: [t for t in FEAT_TASKS if t.complexity == Complexity.LOW],
    Complexity.MEDIUM: [t for t in FEAT_TASKS if t.complexity == Complexity.MEDIUM],
    Complexity.HARD: [t for t in FEAT_TASKS if t.complexity == Complexity.HARD],
}
