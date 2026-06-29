class TestClass:
    # Basic types
    string_attr: str = "test"
    int_attr: int = 42
    bool_attr: bool = True
    float_attr: float = 3.14
    bytes_attr: bytes = b"test"
    none_attr: None | None = None

    # Container types
    list_attr: list[str] = ["a", "b"]
    dict_attr: dict[str, int] = {"a": 1, "b": 2}

    # Optional types
    optional_attr: str | None = None

    # Complex types
    nested_attr: list[dict[str, int]] = [{"a": 1}]

    def __init__(self):
        # Instance attributes
        self.instance_str: str = "instance"
        self.instance_int: int = 100
