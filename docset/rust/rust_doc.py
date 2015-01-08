# Everything related to docs for Rust itself

# More verbose names, manual correction
GUIDE_TITLES = {
    "A 30-minute Introduction to Rust": "A 30-minute Introduction",
    "A Guide to the Rust Runtime": "Runtime",
    "Rust documentation": "Table of Contents",
    "Rust Documentation": "Documenting Code",
    "The Rust Containers and Iterators Guide": "Containers and Iterators",
    "The Rust Foreign Function Interface Guide": "FFI",
    "The Rust Language Tutorial": "Tutorial",
    "The Rust Macros Guide": "Macros",
    "The Rust Pointer Guide": "Pointers",
    "The Rust Reference Manual": "Reference Manual",
    "The Rust References and Lifetimes Guide": "References and Lifetimes",
    "The Rust Threads and Communication Guide": "Threads and Communication",
    "The Rust Testing Guide": "Testing",
    "Writing Safe Unsafe and Low-Level Code": "Unsafe and Low-Level Code",
    "Rust Design FAQ": "Design FAQ",
    "Rust Cheatsheet": "Cheatsheet",
    "The Rust Compiler Plugins Guide": "Compiler Plugins",
    "The Rust Design FAQ": "Design FAQ",
    "The Rust Guide": "Guide",
    "The Rust Language FAQ": "Language FAQ",
    "The Rust Project FAQ": "Project FAQ",
    "The Rust Reference": "Language Reference",
    "Writing Unsafe and Low-Level Code in Rust": "Unsafe and Low-Level Code",
    "The Guide to Rust Strings": "Strings",
    "The Rust Crates and Modules Guide": "Crates and Modules",
    "The Rust Ownership Guide": "Ownership",
}


def guide_title(title):
    return GUIDE_TITLES.get(title, title)
