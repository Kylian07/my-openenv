"""
Task definitions with dirty data, clean (ground-truth) data, and metadata.

Each task has:
  - dirty_data:   What the agent starts with (messy)
  - clean_data:   The correct answer (what it should become)
  - rows_to_delete: Which row indices are duplicates
"""

# ── Formatting rules shared across all tasks ──────────────
FORMATTING_RULES = """
Formatting Rules:
- name: Title Case, single spaces, trimmed (e.g., "John Doe")
- email: all lowercase, trimmed (e.g., "john@example.com")
- phone: XXX-XXX-XXXX format, digits and dashes only (e.g., "555-123-4567")
- date/start_date: YYYY-MM-DD format (e.g., "2024-01-15")
- city: Title Case, trimmed (e.g., "New York")
- department: Title Case (e.g., "Engineering")
- salary: plain integer string, no symbols (e.g., "95000")
- age: plain integer string (e.g., "30")
- status: one of "Active", "Inactive", "On Leave"
"""

TASKS = {

    # ══════════════════════════════════════════════════════════
    #  EASY TASK: Just fix formatting (5 rows, 5 columns)
    #  No duplicates, no missing values
    # ══════════════════════════════════════════════════════════
    "easy_format_standardization": {
        "task_id": "easy_format_standardization",
        "difficulty": "easy",
        "description": (
            "Clean a 5-row contact dataset by standardizing all cell formats. "
            "Every cell has a value but many have incorrect formatting. "
            "Use fix_cell to correct each value, then submit.\n\n"
            "Issues to fix:\n"
            "- Names: wrong case, extra spaces\n"
            "- Emails: uppercase letters, extra spaces\n"
            "- Phones: dots, parentheses, spaces instead of XXX-XXX-XXXX\n"
            "- Dates: wrong format (MM-DD-YYYY, slashes, dots instead of YYYY-MM-DD)\n"
            "- Cities: wrong case, extra spaces"
        ),
        "columns": ["name", "email", "phone", "date", "city"],
        "column_descriptions": {
            "name": "Full name in Title Case, trimmed, single spaces",
            "email": "Email address, all lowercase, trimmed",
            "phone": "Phone in XXX-XXX-XXXX format",
            "date": "Date in YYYY-MM-DD format",
            "city": "City name in Title Case, trimmed",
        },
        "max_steps": 35,

        # ── DIRTY (what the agent sees) ───────────────────
        "dirty_data": [
            {
                "name": "  john DOE  ",
                "email": "JOHN@GMAIL.COM",
                "phone": "555.123.4567",
                "date": "01-15-2024",
                "city": "new york"
            },
            {
                "name": "Jane   Smith",
                "email": "jane@Yahoo.COM",
                "phone": "(555) 234-5678",
                "date": "2024/02/20",
                "city": "LOS ANGELES"
            },
            {
                "name": "bob WILSON",
                "email": "  Bob.Wilson@Email.ORG  ",
                "phone": "5551239876",
                "date": "03/25/2024",
                "city": "  chicago  "
            },
            {
                "name": "ALICE    brown",
                "email": "ALICE.B@COMPANY.COM",
                "phone": "555 987 6543",
                "date": "12-31-2023",
                "city": "san FRANCISCO"
            },
            {
                "name": "  charlie Davis",
                "email": "Charlie@test.IO",
                "phone": "555-111-2222",
                "date": "2024.01.10",
                "city": "SEATTLE"
            },
        ],

        # ── CLEAN (correct answers) ──────────────────────
        "clean_data": [
            {
                "name": "John Doe",
                "email": "john@gmail.com",
                "phone": "555-123-4567",
                "date": "2024-01-15",
                "city": "New York"
            },
            {
                "name": "Jane Smith",
                "email": "jane@yahoo.com",
                "phone": "555-234-5678",
                "date": "2024-02-20",
                "city": "Los Angeles"
            },
            {
                "name": "Bob Wilson",
                "email": "bob.wilson@email.org",
                "phone": "555-123-9876",
                "date": "2024-03-25",
                "city": "Chicago"
            },
            {
                "name": "Alice Brown",
                "email": "alice.b@company.com",
                "phone": "555-987-6543",
                "date": "2023-12-31",
                "city": "San Francisco"
            },
            {
                "name": "Charlie Davis",
                "email": "charlie@test.io",
                "phone": "555-111-2222",
                "date": "2024-01-10",
                "city": "Seattle"
            },
        ],

        "rows_to_delete": [],  # No duplicates in easy task
    },

    # ══════════════════════════════════════════════════════════
    #  MEDIUM TASK: Format + Duplicates + Missing (10 rows)
    # ══════════════════════════════════════════════════════════
    "medium_dedup_and_fill": {
        "task_id": "medium_dedup_and_fill",
        "difficulty": "medium",
        "description": (
            "Clean a 10-row employee dataset:\n"
            "1. Fix ALL formatting issues (same rules as easy task).\n"
            "2. Delete DUPLICATE rows (keep the FIRST occurrence).\n"
            "   - Row 5 is a duplicate of Row 0\n"
            "   - Row 9 is a duplicate of Row 1\n"
            "3. Fill MISSING (None) values:\n"
            "   - Missing department: infer from job_title\n"
            "     (e.g., 'Data Scientist' belongs to 'Engineering')\n"
            "   - Missing salary: use average of that department's known salaries\n"
            "     (rounded to nearest integer)\n\n"
            "Use fix_cell and delete_row actions, then submit."
        ),
        "columns": ["name", "email", "phone", "department", "job_title",
                     "salary", "start_date"],
        "column_descriptions": {
            "name": "Employee name (Title Case)",
            "email": "Email (lowercase)",
            "phone": "Phone (XXX-XXX-XXXX)",
            "department": "Department (Title Case)",
            "job_title": "Job title",
            "salary": "Annual salary (plain integer string)",
            "start_date": "Start date (YYYY-MM-DD)",
        },
        "max_steps": 60,

        "dirty_data": [
            # Row 0
            {"name": "  john DOE  ", "email": "JOHN@COMPANY.COM",
             "phone": "555.123.4567", "department": "Engineering",
             "job_title": "Software Engineer", "salary": "95000",
             "start_date": "01-15-2023"},
            # Row 1
            {"name": "Jane   Smith", "email": "jane@company.COM",
             "phone": "(555) 234-5678", "department": "Marketing",
             "job_title": "Marketing Manager", "salary": "85000",
             "start_date": "2023/02/20"},
            # Row 2
            {"name": "bob WILSON", "email": "bob@COMPANY.com",
             "phone": "5551239876", "department": "Engineering",
             "job_title": "Senior Developer", "salary": "110000",
             "start_date": "03/25/2022"},
            # Row 3 — department is MISSING
            {"name": "ALICE    brown", "email": "ALICE@COMPANY.COM",
             "phone": "555 987 6543", "department": None,
             "job_title": "Data Scientist", "salary": "100000",
             "start_date": "12-31-2022"},
            # Row 4
            {"name": "  charlie Davis", "email": "Charlie@Company.com",
             "phone": "555-111-2222", "department": "Marketing",
             "job_title": "Content Writer", "salary": "65000",
             "start_date": "2024.01.10"},
            # Row 5 — DUPLICATE of Row 0
            {"name": "John Doe", "email": "john@company.com",
             "phone": "555-123-4567", "department": "Engineering",
             "job_title": "Software Engineer", "salary": "95000",
             "start_date": "2023-01-15"},
            # Row 6 — salary is MISSING
            {"name": "  diana PRINCE", "email": "diana@COMPANY.COM",
             "phone": "555.444.3333", "department": "Engineering",
             "job_title": "QA Engineer", "salary": None,
             "start_date": "06-15-2023"},
            # Row 7 — department is MISSING
            {"name": "frank Miller", "email": "FRANK@company.com",
             "phone": "(555) 555-6666", "department": None,
             "job_title": "Marketing Analyst", "salary": "70000",
             "start_date": "2023/09/01"},
            # Row 8
            {"name": "Grace   Lee", "email": "grace@Company.COM",
             "phone": "5557778888", "department": "Engineering",
             "job_title": "DevOps Engineer", "salary": "105000",
             "start_date": "04-20-2023"},
            # Row 9 — DUPLICATE of Row 1
            {"name": "jane smith", "email": "jane@company.com",
             "phone": "555-234-5678", "department": "Marketing",
             "job_title": "Marketing Manager", "salary": "85000",
             "start_date": "2023-02-20"},
        ],

        "clean_data": [
            {"name": "John Doe", "email": "john@company.com",
             "phone": "555-123-4567", "department": "Engineering",
             "job_title": "Software Engineer", "salary": "95000",
             "start_date": "2023-01-15"},
            {"name": "Jane Smith", "email": "jane@company.com",
             "phone": "555-234-5678", "department": "Marketing",
             "job_title": "Marketing Manager", "salary": "85000",
             "start_date": "2023-02-20"},
            {"name": "Bob Wilson", "email": "bob@company.com",
             "phone": "555-123-9876", "department": "Engineering",
             "job_title": "Senior Developer", "salary": "110000",
             "start_date": "2022-03-25"},
            {"name": "Alice Brown", "email": "alice@company.com",
             "phone": "555-987-6543", "department": "Engineering",
             "job_title": "Data Scientist", "salary": "100000",
             "start_date": "2022-12-31"},
            {"name": "Charlie Davis", "email": "charlie@company.com",
             "phone": "555-111-2222", "department": "Marketing",
             "job_title": "Content Writer", "salary": "65000",
             "start_date": "2024-01-10"},
            # Row 5 → DELETED
            {"name": "Diana Prince", "email": "diana@company.com",
             "phone": "555-444-3333", "department": "Engineering",
             "job_title": "QA Engineer", "salary": "102500",
             "start_date": "2023-06-15"},
            # salary = avg(95000,110000,100000,105000) = 102500
            {"name": "Frank Miller", "email": "frank@company.com",
             "phone": "555-555-6666", "department": "Marketing",
             "job_title": "Marketing Analyst", "salary": "70000",
             "start_date": "2023-09-01"},
            {"name": "Grace Lee", "email": "grace@company.com",
             "phone": "555-777-8888", "department": "Engineering",
             "job_title": "DevOps Engineer", "salary": "105000",
             "start_date": "2023-04-20"},
            # Row 9 → DELETED
        ],

        "rows_to_delete": [5, 9],
    },

    # ══════════════════════════════════════════════════════════
    #  HARD TASK: Everything (15 rows, 10 columns)
    # ══════════════════════════════════════════════════════════
    "hard_full_pipeline": {
        "task_id": "hard_full_pipeline",
        "difficulty": "hard",
        "description": (
            "Clean a 15-row HR dataset with ALL of these issues:\n"
            "1. FORMATTING — fix names, emails, phones, dates, cities\n"
            "2. DUPLICATES — delete duplicate rows (keep first occurrence)\n"
            "   - Row 5 is a duplicate of Row 0\n"
            "   - Row 13 is a duplicate of Row 1\n"
            "3. MISSING VALUES — fill using context:\n"
            "   - Missing department: infer from job_title\n"
            "   - Missing salary: use department median\n"
            "   - Missing age: use department average age\n"
            "4. OUTLIERS — salary outliers:\n"
            "   - If salary > 3x department median → fix to median\n"
            "   - If salary < 0.3x department median → fix to median\n"
            "   (Round to nearest 1000)\n"
            "5. CROSS-FIELD VALIDATION:\n"
            "   - status must be exactly: 'Active', 'Inactive', or 'On Leave'\n"
            "   - age must be reasonable (18-80); fix obvious typos\n"
            "     (e.g., 255 is likely 25)\n\n"
            "Use fix_cell, delete_row, then submit."
        ),
        "columns": ["name", "email", "phone", "department", "job_title",
                     "salary", "age", "status", "start_date", "city"],
        "column_descriptions": {
            "name": "Full name (Title Case)",
            "email": "Email (lowercase)",
            "phone": "Phone (XXX-XXX-XXXX)",
            "department": "Department (Title Case)",
            "job_title": "Job title",
            "salary": "Annual salary (plain integer, no symbols)",
            "age": "Age (integer 18-80)",
            "status": "One of: Active, Inactive, On Leave",
            "start_date": "Date (YYYY-MM-DD)",
            "city": "City (Title Case)",
        },
        "max_steps": 100,

        "dirty_data": [
            # Row 0
            {"name": "  john DOE  ", "email": "JOHN@CORP.COM",
             "phone": "555.123.4567", "department": "Engineering",
             "job_title": "Software Engineer", "salary": "95000",
             "age": "32", "status": "active",
             "start_date": "01-15-2023", "city": "new york"},
            # Row 1
            {"name": "Jane   Smith", "email": "jane@corp.COM",
             "phone": "(555) 234-5678", "department": "Marketing",
             "job_title": "Marketing Manager", "salary": "85000",
             "age": "41", "status": "Active",
             "start_date": "2023/02/20", "city": "LOS ANGELES"},
            # Row 2 — salary 999999 is OUTLIER
            {"name": "bob WILSON", "email": "bob@CORP.com",
             "phone": "5551239876", "department": "Engineering",
             "job_title": "Senior Developer", "salary": "999999",
             "age": "38", "status": "ACTIVE",
             "start_date": "03/25/2022", "city": "  chicago  "},
            # Row 3 — department MISSING
            {"name": "ALICE    brown", "email": "ALICE@CORP.COM",
             "phone": "555 987 6543", "department": None,
             "job_title": "Data Scientist", "salary": "100000",
             "age": "29", "status": "Active",
             "start_date": "12-31-2022", "city": "san FRANCISCO"},
            # Row 4 — age 255 is TYPO, status wrong case
            {"name": "  charlie Davis", "email": "Charlie@Corp.com",
             "phone": "555-111-2222", "department": "Marketing",
             "job_title": "Content Writer", "salary": "65000",
             "age": "255", "status": "On leave",
             "start_date": "2024.01.10", "city": "SEATTLE"},
            # Row 5 — DUPLICATE of Row 0
            {"name": "John Doe", "email": "john@corp.com",
             "phone": "555-123-4567", "department": "Engineering",
             "job_title": "Software Engineer", "salary": "95000",
             "age": "32", "status": "Active",
             "start_date": "2023-01-15", "city": "New York"},
            # Row 6 — salary MISSING, status TYPO
            {"name": "  diana PRINCE", "email": "diana@CORP.COM",
             "phone": "555.444.3333", "department": "Engineering",
             "job_title": "QA Engineer", "salary": None,
             "age": "27", "status": "actve",
             "start_date": "06-15-2023", "city": "BOSTON"},
            # Row 7 — department MISSING (should be Sales)
            {"name": "frank Miller", "email": "FRANK@corp.com",
             "phone": "(555) 555-6666", "department": None,
             "job_title": "Sales Representative", "salary": "72000",
             "age": "35", "status": "Active",
             "start_date": "2023/09/01", "city": "denver"},
            # Row 8 — age MISSING
            {"name": "Grace   Lee", "email": "grace@Corp.COM",
             "phone": "5557778888", "department": "Engineering",
             "job_title": "DevOps Engineer", "salary": "105000",
             "age": None, "status": "Active",
             "start_date": "04-20-2023", "city": "austin"},
            # Row 9
            {"name": "henry   FORD", "email": "HENRY@corp.COM",
             "phone": "555 222 3333", "department": "Sales",
             "job_title": "Sales Manager", "salary": "90000",
             "age": "48", "status": "Inactive",
             "start_date": "01-10-2021", "city": "  MIAMI  "},
            # Row 10 — salary 5000 is OUTLIER
            {"name": "iris CHANG", "email": "iris@CORP.com",
             "phone": "555.999.0000", "department": "Marketing",
             "job_title": "SEO Specialist", "salary": "5000",
             "age": "31", "status": "Active",
             "start_date": "2023/11/15", "city": "portland"},
            # Row 11
            {"name": "JACK    white", "email": "JACK@CORP.COM",
             "phone": "(555) 888-7777", "department": "Engineering",
             "job_title": "Frontend Developer", "salary": "92000",
             "age": "26", "status": "on Leave",
             "start_date": "07-01-2023", "city": "SAN DIEGO"},
            # Row 12
            {"name": "karen BLACK", "email": "karen@Corp.COM",
             "phone": "5556665555", "department": "Sales",
             "job_title": "Account Executive", "salary": "78000",
             "age": "33", "status": "Active",
             "start_date": "2022/06/15", "city": "ATLANTA"},
            # Row 13 — DUPLICATE of Row 1
            {"name": "jane smith", "email": "jane@corp.com",
             "phone": "555-234-5678", "department": "Marketing",
             "job_title": "Marketing Manager", "salary": "85000",
             "age": "41", "status": "Active",
             "start_date": "2023-02-20", "city": "Los Angeles"},
            # Row 14 — department MISSING, status TYPO
            {"name": "  leo MARTINEZ  ", "email": "LEO@corp.COM",
             "phone": "555 333 4444", "department": None,
             "job_title": "HR Coordinator", "salary": "62000",
             "age": "29", "status": "Activ",
             "start_date": "2024.03.01", "city": "  PHOENIX  "},
        ],

        "clean_data": [
            {"name": "John Doe", "email": "john@corp.com",
             "phone": "555-123-4567", "department": "Engineering",
             "job_title": "Software Engineer", "salary": "95000",
             "age": "32", "status": "Active",
             "start_date": "2023-01-15", "city": "New York"},
            {"name": "Jane Smith", "email": "jane@corp.com",
             "phone": "555-234-5678", "department": "Marketing",
             "job_title": "Marketing Manager", "salary": "85000",
             "age": "41", "status": "Active",
             "start_date": "2023-02-20", "city": "Los Angeles"},
            {"name": "Bob Wilson", "email": "bob@corp.com",
             "phone": "555-123-9876", "department": "Engineering",
             "job_title": "Senior Developer", "salary": "98000",
             "age": "38", "status": "Active",
             "start_date": "2022-03-25", "city": "Chicago"},
            {"name": "Alice Brown", "email": "alice@corp.com",
             "phone": "555-987-6543", "department": "Engineering",
             "job_title": "Data Scientist", "salary": "100000",
             "age": "29", "status": "Active",
             "start_date": "2022-12-31", "city": "San Francisco"},
            {"name": "Charlie Davis", "email": "charlie@corp.com",
             "phone": "555-111-2222", "department": "Marketing",
             "job_title": "Content Writer", "salary": "65000",
             "age": "25", "status": "On Leave",
             "start_date": "2024-01-10", "city": "Seattle"},
            # Row 5 → DELETED
            {"name": "Diana Prince", "email": "diana@corp.com",
             "phone": "555-444-3333", "department": "Engineering",
             "job_title": "QA Engineer", "salary": "98000",
             "age": "27", "status": "Active",
             "start_date": "2023-06-15", "city": "Boston"},
            {"name": "Frank Miller", "email": "frank@corp.com",
             "phone": "555-555-6666", "department": "Sales",
             "job_title": "Sales Representative", "salary": "72000",
             "age": "35", "status": "Active",
             "start_date": "2023-09-01", "city": "Denver"},
            {"name": "Grace Lee", "email": "grace@corp.com",
             "phone": "555-777-8888", "department": "Engineering",
             "job_title": "DevOps Engineer", "salary": "105000",
             "age": "30", "status": "Active",
             "start_date": "2023-04-20", "city": "Austin"},
            {"name": "Henry Ford", "email": "henry@corp.com",
             "phone": "555-222-3333", "department": "Sales",
             "job_title": "Sales Manager", "salary": "90000",
             "age": "48", "status": "Inactive",
             "start_date": "2021-01-10", "city": "Miami"},
            {"name": "Iris Chang", "email": "iris@corp.com",
             "phone": "555-999-0000", "department": "Marketing",
             "job_title": "SEO Specialist", "salary": "75000",
             "age": "31", "status": "Active",
             "start_date": "2023-11-15", "city": "Portland"},
            {"name": "Jack White", "email": "jack@corp.com",
             "phone": "555-888-7777", "department": "Engineering",
             "job_title": "Frontend Developer", "salary": "92000",
             "age": "26", "status": "On Leave",
             "start_date": "2023-07-01", "city": "San Diego"},
            {"name": "Karen Black", "email": "karen@corp.com",
             "phone": "555-666-5555", "department": "Sales",
             "job_title": "Account Executive", "salary": "78000",
             "age": "33", "status": "Active",
             "start_date": "2022-06-15", "city": "Atlanta"},
            # Row 13 → DELETED
            {"name": "Leo Martinez", "email": "leo@corp.com",
             "phone": "555-333-4444", "department": "Human Resources",
             "job_title": "HR Coordinator", "salary": "62000",
             "age": "29", "status": "Active",
             "start_date": "2024-03-01", "city": "Phoenix"},
        ],

        "rows_to_delete": [5, 13],
    },
}


def get_task(task_id: str) -> dict:
    """Get a task definition by ID."""
    if task_id not in TASKS:
        raise ValueError(
            f"Unknown task_id: '{task_id}'. "
            f"Available tasks: {list(TASKS.keys())}"
        )
    return TASKS[task_id]


def list_tasks() -> list:
    """List all available task IDs."""
    return list(TASKS.keys())