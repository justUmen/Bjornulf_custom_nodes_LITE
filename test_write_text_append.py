import sys
import os

# Adjust path to import from the custom nodes package
sys.path.append("/home/umen/SyNc/Plugins/ComfyUI/Bjornulf_custom_nodes")

from write_text import WriteTextAppend

def test_write_text_append():
    node = WriteTextAppend()
    
    # Test case 1: No input text
    print("Testing case 1: No input text")
    result1 = node.append_text(text="World", text_input=None)
    print(f"Result 1: {result1}")
    assert result1[0] == "World"
    
    # Test case 2: With input text
    print("\nTesting case 2: With input text")
    result2 = node.append_text(text="World", text_input="Hello")
    print(f"Result 2: {result2}")
    assert result2[0] == "Hello\nWorld"
    
    # Test case 3: Empty input text
    print("\nTesting case 3: Empty input text")
    result3 = node.append_text(text="World", text_input="")
    print(f"Result 3: {result3}")
    assert result3[0] == "World"

    print("\nAll tests passed!")

if __name__ == "__main__":
    test_write_text_append()
