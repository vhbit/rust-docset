TO_DASH_TYPE = {
    "gd": "Guide",
    "fn": "Function",
    "trait": "Trait",
    "struct": "_Struct",
    "structfield": "Field",
    "mod": "Module",
    "type": "Type",
    "static": "Constant",
    "macro": "Macro",
    "primitive": "Type",
    "ffi": "Function",
    "method": "Method",
    "field": "Field",
    "variant": "Variant",
    "enum": "Enum",
    "ffs": "Constant",
    "tymethod": "Method"
}


def to_dash_type(ty, default = None):
    return TO_DASH_TYPE.get(ty, default)
