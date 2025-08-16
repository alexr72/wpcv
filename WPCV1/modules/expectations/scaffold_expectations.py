import os
from datetime import datetime

def scaffold_expectations(base_dir):
    """
    Scaffold a default expectations.md file for validation.
    Returns: (path, folder, agent, expectation_type, auto_validate)
    """
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    expectation_type = "expectations"
    filename = f"{expectation_type}.md"
    path = os.path.join(docs_dir, filename)

    content = f"""# Validation Expectations — {timestamp}

## ✅ Syntax
- Code must compile without errors
- No unused variables or unreachable blocks

## ✅ Structure
- Modular functions with clear separation
- No inline logic in global scope

## ✅ Comments
- Each function must have a docstring
- Complex logic must be annotated

## ✅ Security
- No hardcoded credentials
- Input validation required

## ✅ Performance
- Avoid nested loops > O(n²)
- Prefer async where applicable

## ✅ Compatibility
- Must run in Linux-based environment
- Avoid OS-specific dependencies

## ✅ Logging
- Use centralized logger module
- Include timestamps and severity levels

## ✅ Permissions
- Respect file ownership and access rights
- Avoid chmod/chown unless explicitly required
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    folder = "modules"      # default target folder for validation
    agent = "local"         # default agent for challenge
    auto_validate = True    # trigger validation after scaffold

    return path, folder, agent, expectation_type, auto_validate
