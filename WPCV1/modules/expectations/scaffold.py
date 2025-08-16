import os

def scaffold_expectations(base_path):
    print("\n🧠 Let's build your expectation file step by step.\n")
    title = input("🔹 What is the goal of this validation? ")
    language = input("🔹 What language is the code in? (e.g. JS, Python) ")
    style = input("🔹 Should the code follow any style guide? (e.g. PEP8, Airbnb) ")
    tests = input("🔹 Should it include test coverage? (yes/no) ")
    comments = input("🔹 Minimum comment ratio? (e.g. 10%) ")

    expectation_text = f"""# Expectations: {title}
- Language: {language}
- Style Guide: {style}
- Test Coverage: {tests}
- Comment Ratio: {comments}
"""

    docs_path = os.path.join(base_path, "docs")
    os.makedirs(docs_path, exist_ok=True)
    file_name = f"expectations_{language.lower()}.md"
    full_path = os.path.join(docs_path, file_name)

    with open(full_path, "w") as f:
        f.write(expectation_text)

    print(f"\n✅ Saved to {full_path}")
    return full_path
