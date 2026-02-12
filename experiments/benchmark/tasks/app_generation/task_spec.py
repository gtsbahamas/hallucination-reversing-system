"""Track 3: App Generation task specifications.

20 full-application generation tasks across 3 difficulty tiers.
Each task defines a prompt, requirements, and evaluation criteria.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class DifficultyTier(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class AppTaskSpec:
    """Specification for a single app generation task."""
    task_id: str
    title: str
    difficulty: DifficultyTier
    prompt: str
    requirements: List[str]
    test_module: str  # e.g. "test_app01_todo"
    tech_constraints: str = "any"
    timeout_seconds: int = 300

    # Scoring rubric weights (must sum to 1.0)
    weight_builds: float = 0.20
    weight_renders: float = 0.15
    weight_core: float = 0.35
    weight_edge: float = 0.15
    weight_error: float = 0.15


# ---------------------------------------------------------------------------
# Tier 1: Simple (5 tasks) -- single-page, minimal logic
# ---------------------------------------------------------------------------

APP_01 = AppTaskSpec(
    task_id="APP-01",
    title="Todo List App",
    difficulty=DifficultyTier.SIMPLE,
    prompt=(
        "Build a todo list web application with the following features:\n"
        "1. Add new todo items via a text input and submit button\n"
        "2. Mark todo items as complete (checkbox or click toggle)\n"
        "3. Delete todo items\n"
        "4. Persist todos to localStorage so they survive page reload\n"
        "5. Show a count of remaining (incomplete) items\n"
        "Use React with TypeScript. The app should be a single page."
    ),
    requirements=[
        "Text input field for new todos",
        "Submit button or Enter key adds a todo",
        "Each todo has a completion toggle",
        "Each todo has a delete button",
        "Completed todos are visually distinct (strikethrough or similar)",
        "Remaining item count is displayed and updates correctly",
        "Data persists across page reload via localStorage",
        "Empty input does not create a todo",
    ],
    test_module="test_app01_todo",
    tech_constraints="React + TypeScript",
)

APP_02 = AppTaskSpec(
    task_id="APP-02",
    title="Calculator",
    difficulty=DifficultyTier.SIMPLE,
    prompt=(
        "Build a calculator web application with the following features:\n"
        "1. Basic arithmetic: addition, subtraction, multiplication, division\n"
        "2. Decimal number support\n"
        "3. Clear button to reset\n"
        "4. Display showing current input and result\n"
        "5. Chain operations (e.g. 2 + 3 * 4 should work)\n"
        "Use any frontend framework. The app should be a single page."
    ),
    requirements=[
        "Buttons for digits 0-9",
        "Buttons for +, -, *, /",
        "Decimal point button",
        "Equals button computes result",
        "Clear button resets to 0",
        "Display shows current expression or result",
        "Division by zero handled gracefully (error message, not crash)",
        "Chained operations produce correct results",
    ],
    test_module="test_app02_calculator",
)

APP_03 = AppTaskSpec(
    task_id="APP-03",
    title="Markdown Previewer",
    difficulty=DifficultyTier.SIMPLE,
    prompt=(
        "Build a markdown previewer web application:\n"
        "1. Split-pane layout: editor on left, preview on right\n"
        "2. Real-time preview as user types\n"
        "3. Support common Markdown: headings, bold, italic, links, "
        "code blocks, lists, images\n"
        "4. Syntax highlighting for code blocks\n"
        "Use any frontend framework."
    ),
    requirements=[
        "Text area for markdown input",
        "Preview pane renders HTML",
        "Preview updates in real-time as user types",
        "Headings (h1-h6) render correctly",
        "Bold and italic render correctly",
        "Links render as clickable anchors",
        "Code blocks render with monospace font",
        "Ordered and unordered lists render correctly",
    ],
    test_module="test_app03_markdown",
)

APP_04 = AppTaskSpec(
    task_id="APP-04",
    title="Timer / Stopwatch",
    difficulty=DifficultyTier.SIMPLE,
    prompt=(
        "Build a timer/stopwatch web application:\n"
        "1. Start, stop, and reset controls\n"
        "2. Display time in MM:SS.ms format\n"
        "3. Lap time recording -- button to record current time\n"
        "4. Display list of recorded lap times\n"
        "5. Clear all laps button\n"
        "Use any frontend framework."
    ),
    requirements=[
        "Start button begins counting",
        "Stop button pauses counting",
        "Reset button returns to 00:00.00",
        "Time display updates at least 10 times per second",
        "Lap button records current time to a list",
        "Lap times are displayed in order",
        "Clear laps removes all recorded laps",
        "Start/stop toggle works correctly (resume from paused state)",
    ],
    test_module="test_app04_timer",
)

APP_05 = AppTaskSpec(
    task_id="APP-05",
    title="Color Palette Generator",
    difficulty=DifficultyTier.SIMPLE,
    prompt=(
        "Build a color palette generator web application:\n"
        "1. Generate a palette of 5 harmonious colors\n"
        "2. Display each color as a large swatch with hex code\n"
        "3. Click a swatch to copy hex code to clipboard\n"
        "4. 'Generate' button creates a new random palette\n"
        "5. Lock individual colors so they persist across regeneration\n"
        "Use any frontend framework."
    ),
    requirements=[
        "Displays 5 color swatches",
        "Each swatch shows its hex code",
        "Generate button creates new palette",
        "Click to copy hex code to clipboard",
        "Lock toggle on each swatch",
        "Locked colors persist when generating new palette",
        "All hex codes are valid (#RRGGBB format)",
        "Colors are visually distinct from each other",
    ],
    test_module="test_app05_color_palette",
)

# ---------------------------------------------------------------------------
# Tier 2: Medium (8 tasks) -- multi-page, data management, API integration
# ---------------------------------------------------------------------------

APP_06 = AppTaskSpec(
    task_id="APP-06",
    title="Weather Dashboard",
    difficulty=DifficultyTier.MEDIUM,
    prompt=(
        "Build a weather dashboard web application:\n"
        "1. Search bar to look up weather by city name\n"
        "2. Display current temperature, conditions, humidity, wind speed\n"
        "3. Show a 5-day forecast\n"
        "4. Error handling for invalid city names\n"
        "5. Loading state while fetching data\n"
        "Use any frontend framework. Use the OpenWeatherMap API "
        "(or mock it if no API key is available)."
    ),
    requirements=[
        "Search input for city name",
        "Current weather display (temperature, conditions)",
        "Humidity and wind speed displayed",
        "5-day forecast with daily temperatures",
        "Loading spinner/indicator during API call",
        "Error message for invalid city name",
        "Graceful handling of network errors",
        "Temperature unit display (Celsius or Fahrenheit)",
    ],
    test_module="test_app06_weather",
    timeout_seconds=600,
)

APP_07 = AppTaskSpec(
    task_id="APP-07",
    title="Blog with Authentication",
    difficulty=DifficultyTier.MEDIUM,
    prompt=(
        "Build a blog application with user authentication:\n"
        "1. User signup and login (email + password)\n"
        "2. Authenticated users can create, edit, and delete posts\n"
        "3. Public view of all posts (no auth required)\n"
        "4. Each post has title, content, author, date\n"
        "5. Only post authors can edit/delete their own posts\n"
        "Use any full-stack framework. In-memory or file-based storage is fine."
    ),
    requirements=[
        "Signup form (email, password, confirm password)",
        "Login form (email, password)",
        "Logout functionality",
        "Create post form (title, content)",
        "Post listing page showing all posts",
        "Edit post (only by author)",
        "Delete post (only by author)",
        "Unauthorized access to edit/delete is blocked",
    ],
    test_module="test_app07_blog",
    timeout_seconds=600,
)

APP_08 = AppTaskSpec(
    task_id="APP-08",
    title="E-commerce Product Page",
    difficulty=DifficultyTier.MEDIUM,
    prompt=(
        "Build an e-commerce product page with shopping cart:\n"
        "1. Product listing with image, name, price, description\n"
        "2. Add to cart button on each product\n"
        "3. Cart sidebar/page showing items, quantities, totals\n"
        "4. Quantity adjustment (increase/decrease) in cart\n"
        "5. Remove item from cart\n"
        "6. Checkout form (name, email, address -- no real payment)\n"
        "Use any frontend framework. Use mock product data."
    ),
    requirements=[
        "Product listing with at least 4 products",
        "Each product shows image, name, price",
        "Add to cart button on each product",
        "Cart displays item count badge/indicator",
        "Cart shows line items with subtotals",
        "Quantity can be increased and decreased",
        "Items can be removed from cart",
        "Cart total is calculated correctly",
        "Checkout form with validation",
    ],
    test_module="test_app08_ecommerce",
    timeout_seconds=600,
)

APP_09 = AppTaskSpec(
    task_id="APP-09",
    title="Kanban Board",
    difficulty=DifficultyTier.MEDIUM,
    prompt=(
        "Build a Kanban board application:\n"
        "1. Three columns: To Do, In Progress, Done\n"
        "2. Add new cards to any column\n"
        "3. Drag and drop cards between columns\n"
        "4. Edit card title and description\n"
        "5. Delete cards\n"
        "6. Persist board state to localStorage\n"
        "Use any frontend framework."
    ),
    requirements=[
        "Three columns displayed: To Do, In Progress, Done",
        "Add new card button per column",
        "Card shows title",
        "Drag and drop cards between columns",
        "Edit card title",
        "Delete card",
        "Board state persists via localStorage",
        "Cards stay in correct column after reload",
    ],
    test_module="test_app09_kanban",
    timeout_seconds=600,
)

APP_10 = AppTaskSpec(
    task_id="APP-10",
    title="Chat Interface with WebSocket",
    difficulty=DifficultyTier.MEDIUM,
    prompt=(
        "Build a real-time chat application:\n"
        "1. WebSocket-based real-time messaging\n"
        "2. Username selection on entry\n"
        "3. Message input with send button\n"
        "4. Message history displayed in order\n"
        "5. Visual indicator when other users are typing\n"
        "6. Handle disconnection/reconnection gracefully\n"
        "Use Node.js + any frontend framework."
    ),
    requirements=[
        "Username entry screen",
        "Message input field and send button",
        "Messages appear in real-time",
        "Messages show sender name and timestamp",
        "Message history displayed in chronological order",
        "Typing indicator when others type",
        "Handles server disconnect gracefully",
        "Enter key sends message",
    ],
    test_module="test_app10_chat",
    timeout_seconds=600,
)

APP_11 = AppTaskSpec(
    task_id="APP-11",
    title="File Upload and Preview",
    difficulty=DifficultyTier.MEDIUM,
    prompt=(
        "Build a file upload application with preview:\n"
        "1. Upload images (jpg, png, gif) and PDF files\n"
        "2. Drag-and-drop upload zone\n"
        "3. Preview uploaded images inline\n"
        "4. Show PDF filename and size (preview optional)\n"
        "5. Delete uploaded files\n"
        "6. File size limit: 5MB per file\n"
        "Use any full-stack framework."
    ),
    requirements=[
        "File input or drag-and-drop zone",
        "Accepts jpg, png, gif, pdf",
        "Rejects unsupported file types with message",
        "Image preview displayed after upload",
        "File size shown for each upload",
        "Delete button removes uploaded file",
        "Files over 5MB are rejected with error message",
        "Upload progress indicator",
    ],
    test_module="test_app11_upload",
    timeout_seconds=600,
)

APP_12 = AppTaskSpec(
    task_id="APP-12",
    title="Data Table with Sort/Filter/Paginate",
    difficulty=DifficultyTier.MEDIUM,
    prompt=(
        "Build a data table component:\n"
        "1. Load a dataset of at least 100 rows (mock data is fine)\n"
        "2. Column headers are clickable to sort (asc/desc)\n"
        "3. Text filter input to search across all columns\n"
        "4. Pagination with configurable page size (10, 25, 50)\n"
        "5. Show total row count and current page info\n"
        "Use any frontend framework."
    ),
    requirements=[
        "Table with at least 4 columns",
        "At least 100 rows of data",
        "Click column header to sort ascending",
        "Click again to sort descending",
        "Text filter filters rows across all columns",
        "Pagination controls (next, previous, page numbers)",
        "Page size selector (10, 25, 50)",
        "Row count display (e.g. 'Showing 1-10 of 100')",
    ],
    test_module="test_app12_datatable",
    timeout_seconds=600,
)

APP_13 = AppTaskSpec(
    task_id="APP-13",
    title="Multi-step Form Wizard",
    difficulty=DifficultyTier.MEDIUM,
    prompt=(
        "Build a multi-step form wizard:\n"
        "1. At least 3 steps: Personal Info, Address, Review & Submit\n"
        "2. Validation on each step before allowing next\n"
        "3. Back button to return to previous steps\n"
        "4. Progress indicator showing current step\n"
        "5. Review step shows all entered data before submit\n"
        "6. Submit button on final step (log data to console)\n"
        "Use any frontend framework."
    ),
    requirements=[
        "Step 1: Name, email, phone fields with validation",
        "Step 2: Street, city, state, zip fields with validation",
        "Step 3: Review showing all data from steps 1 and 2",
        "Next button disabled until current step validates",
        "Back button preserves previously entered data",
        "Progress indicator shows step 1/2/3",
        "Submit button on review step",
        "Email validation (basic format check)",
    ],
    test_module="test_app13_wizard",
    timeout_seconds=600,
)

# ---------------------------------------------------------------------------
# Tier 3: Hard (7 tasks) -- complex logic, real-world patterns
# ---------------------------------------------------------------------------

APP_14 = AppTaskSpec(
    task_id="APP-14",
    title="Dashboard with Charts",
    difficulty=DifficultyTier.HARD,
    prompt=(
        "Build a data dashboard with charts:\n"
        "1. At least 3 chart types: bar, line, pie\n"
        "2. Data loaded from a JSON API endpoint (mock is fine)\n"
        "3. Responsive layout that works on mobile\n"
        "4. Date range filter to adjust displayed data\n"
        "5. Legend and tooltips on charts\n"
        "Use any frontend framework with a charting library."
    ),
    requirements=[
        "Bar chart rendering with data",
        "Line chart rendering with data",
        "Pie chart rendering with data",
        "Charts have legends",
        "Tooltips appear on hover",
        "Date range filter adjusts chart data",
        "Responsive layout (works at 375px width)",
        "Data loaded from API endpoint",
    ],
    test_module="test_app14_dashboard",
    timeout_seconds=900,
)

APP_15 = AppTaskSpec(
    task_id="APP-15",
    title="Collaborative Text Editor",
    difficulty=DifficultyTier.HARD,
    prompt=(
        "Build a collaborative text editor:\n"
        "1. Real-time co-editing via WebSocket\n"
        "2. Cursor presence (see other users' cursors)\n"
        "3. Conflict resolution for simultaneous edits\n"
        "4. Basic text formatting (bold, italic, underline)\n"
        "5. Document saved automatically\n"
        "Use any full-stack framework. OT or CRDT approach."
    ),
    requirements=[
        "Rich text editing area",
        "Bold, italic, underline formatting",
        "Real-time sync between two clients",
        "Cursor position shown for other users",
        "Simultaneous edits merge without data loss",
        "Auto-save indicator",
        "Undo/redo support",
        "Handles user disconnect gracefully",
    ],
    test_module="test_app15_collab_editor",
    timeout_seconds=900,
)

APP_16 = AppTaskSpec(
    task_id="APP-16",
    title="OAuth Integration",
    difficulty=DifficultyTier.HARD,
    prompt=(
        "Build a web app with OAuth authentication:\n"
        "1. Google OAuth login (or GitHub OAuth)\n"
        "2. Session management with secure cookies\n"
        "3. Protected routes that redirect to login\n"
        "4. User profile page showing OAuth data\n"
        "5. Logout functionality that clears session\n"
        "Use any full-stack framework."
    ),
    requirements=[
        "OAuth login button (Google or GitHub)",
        "OAuth redirect flow completes",
        "Session persists across page reloads",
        "Protected route redirects unauthenticated users",
        "User profile shows name/email from OAuth",
        "Logout button clears session",
        "Cannot access protected routes after logout",
        "CSRF protection on session endpoints",
    ],
    test_module="test_app16_oauth",
    timeout_seconds=900,
)

APP_17 = AppTaskSpec(
    task_id="APP-17",
    title="Payment Flow (Stripe Test Mode)",
    difficulty=DifficultyTier.HARD,
    prompt=(
        "Build a payment flow using Stripe test mode:\n"
        "1. Product selection page\n"
        "2. Stripe Checkout session creation\n"
        "3. Redirect to Stripe payment page\n"
        "4. Success page after payment\n"
        "5. Cancel/failure handling\n"
        "Use any full-stack framework. Use Stripe test keys."
    ),
    requirements=[
        "Product selection with price display",
        "Checkout button creates Stripe session",
        "Redirect to Stripe Checkout page",
        "Success URL renders success page",
        "Cancel URL renders cancel page",
        "Server validates webhook events",
        "Handles Stripe API errors gracefully",
        "Uses Stripe test mode keys",
    ],
    test_module="test_app17_payment",
    timeout_seconds=900,
)

APP_18 = AppTaskSpec(
    task_id="APP-18",
    title="REST API with Database",
    difficulty=DifficultyTier.HARD,
    prompt=(
        "Build a REST API with database backend:\n"
        "1. CRUD endpoints for a 'products' resource\n"
        "2. Input validation on create/update\n"
        "3. Proper HTTP status codes (201, 400, 404, 500)\n"
        "4. Pagination on list endpoint\n"
        "5. Search/filter query parameters\n"
        "Use Node.js/Express or Python/FastAPI with SQLite."
    ),
    requirements=[
        "GET /api/products returns paginated list",
        "GET /api/products/:id returns single product",
        "POST /api/products creates with validation",
        "PUT /api/products/:id updates with validation",
        "DELETE /api/products/:id removes product",
        "400 status on invalid input",
        "404 status on missing resource",
        "Pagination with page and limit parameters",
        "Search by name query parameter",
    ],
    test_module="test_app18_rest_api",
    timeout_seconds=900,
)

APP_19 = AppTaskSpec(
    task_id="APP-19",
    title="Search with Autocomplete",
    difficulty=DifficultyTier.HARD,
    prompt=(
        "Build a search interface with autocomplete:\n"
        "1. Search input with debounced API calls\n"
        "2. Dropdown showing matching results as user types\n"
        "3. Keyboard navigation (arrow keys, Enter to select)\n"
        "4. Result ranking by relevance\n"
        "5. Highlight matching text in results\n"
        "Use any framework. Mock data source with 1000+ items."
    ),
    requirements=[
        "Search input field",
        "Results appear as user types (debounced)",
        "Dropdown shows matching results",
        "Arrow keys navigate results",
        "Enter key selects highlighted result",
        "Matching text highlighted in results",
        "Debounce prevents excessive API calls",
        "Empty query clears results",
    ],
    test_module="test_app19_search",
    timeout_seconds=900,
)

APP_20 = AppTaskSpec(
    task_id="APP-20",
    title="Role-Based Access Control",
    difficulty=DifficultyTier.HARD,
    prompt=(
        "Build a web app with role-based access control:\n"
        "1. Two roles: admin and user\n"
        "2. Admin dashboard with user management\n"
        "3. User dashboard with limited features\n"
        "4. Permission enforcement on both frontend and backend\n"
        "5. Admin can create/delete users and change roles\n"
        "Use any full-stack framework."
    ),
    requirements=[
        "Login with role assignment",
        "Admin sees admin dashboard",
        "User sees user dashboard",
        "Admin can list all users",
        "Admin can change user roles",
        "Admin can delete users",
        "User cannot access admin endpoints",
        "Direct URL access to admin pages blocked for users",
    ],
    test_module="test_app20_rbac",
    timeout_seconds=900,
)

# ---------------------------------------------------------------------------
# Collected task list
# ---------------------------------------------------------------------------

APP_TASKS: List[AppTaskSpec] = [
    APP_01, APP_02, APP_03, APP_04, APP_05,  # Simple
    APP_06, APP_07, APP_08, APP_09, APP_10,  # Medium
    APP_11, APP_12, APP_13,                   # Medium (cont.)
    APP_14, APP_15, APP_16, APP_17, APP_18,  # Hard
    APP_19, APP_20,                           # Hard (cont.)
]

TASKS_BY_ID = {t.task_id: t for t in APP_TASKS}
TASKS_BY_TIER = {
    DifficultyTier.SIMPLE: [t for t in APP_TASKS if t.difficulty == DifficultyTier.SIMPLE],
    DifficultyTier.MEDIUM: [t for t in APP_TASKS if t.difficulty == DifficultyTier.MEDIUM],
    DifficultyTier.HARD: [t for t in APP_TASKS if t.difficulty == DifficultyTier.HARD],
}
