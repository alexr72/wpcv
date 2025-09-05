"""
dispatcher.py

Routes validation tasks to appropriate modules.
"""

from modules.validator import validator
from modules.rewriter import rewriter
from modules.revision import revision
from modules.expectations import expectations

def run_validation(base_dir, file_path, code_str, expectations_path):
    """
    Runs full validation pipeline.
    """
    revision.save_revision(base_dir, file_path, code_str, label="before")
    syntax_errors = validator.check_syntax(code_str)
    lint_warnings = validator.lint_code(code_str)
    expectations_list = expectations.load_expectations(expectations_path)
    expectation_mismatches = validator.match_expectations(code_str, expectations_list)
    rewritten_code, changes = rewriter.auto_rewrite(code_str)
    revision.save_revision(base_dir, file_path, rewritten_code, label="after")

    return {
        "syntax": syntax_errors,
        "lint": lint_warnings,
        "expectations": expectation_mismatches,
        "rewrites": changes
    }
