# Everything related to docs for Rust itself

# More verbose names, manual correction
GUIDE_TITLES = {
    "A 30-minute Introduction to Rust": "A 30-minute Introduction",
    "A Guide to the Rust Runtime": "Rust Runtime",
    "Rust documentation": "Table of Contents",
    "Rust Documentation": "Documenting Code",
    "The Rust Containers and Iterators Guide": "Containers and Iterators",
    "The Rust Foreign Function Interface Guide": "Foreign Function Interface",
    "The Rust Language Tutorial": "Language Tutorial",
    "The Rust Macros Guide": "Macros",
    "The Rust Pointer Guide": "Pointers",
    "The Rust Reference Manual": "Reference Manual",
    "The Rust References and Lifetimes Guide": "References and Lifetimes",
    "The Rust Tasks and Communication Guide": "Tasks and Communication",
    "The Rust Testing Guide": "Testing",
    "Writing Safe Unsafe and Low-Level Code": "Unsafe and Low-Level Code",
    "Rust Design FAQ": "Design FAQ",
    "Rust Cheatsheet": "Cheatsheet",
}


def guide_title(title):
    return GUIDE_TITLES.get(title, title)
