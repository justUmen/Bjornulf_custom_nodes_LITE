class AnyType(str):
    """A special class that is always equal in not equal comparisons. Credit to pydantic."""
    def __ne__(self, __value: object) -> bool:
        return False

any = AnyType("*")

class ConditionalNull:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = (any,)
    RETURN_NAMES = ("output",)
    FUNCTION = "execute"
    CATEGORY = "utils"

    def execute(self):
        return (None,)