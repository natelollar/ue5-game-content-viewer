import unreal
from pathlib import Path
import inspect

current_dir = Path(__file__).parent
output_path = Path(f"{current_dir}/unreal_stubs.pyi")
output_path.parent.mkdir(parents=True, exist_ok=True)

def gen_stubs() -> None:
    """Generate Unreal Python API stubs for use with code editor."""
    with output_path.open("w", encoding="utf-8") as f:
        f.write("# Unreal Engine Python Stub File\n\n")

        for attr in dir(unreal):
            try:
                cls = getattr(unreal, attr)
                
                if isinstance(cls, type):
                    # write class documentation and properties
                    f.write(f"class {attr}:\n")
                    doc = cls.__doc__ or "No documentation available"
                    f.write(f"    \"\"\"{doc}\"\"\"\n\n")
                    for prop in dir(cls):
                        if not prop.startswith("__"):
                            f.write(f"    {prop}: ...\n")
                    f.write("\n")
                elif callable(cls):
                    # write function signatures
                    try:
                        signature = inspect.signature(cls)
                        f.write(f"def {attr}{signature}: ...\n")
                    except ValueError:
                        f.write(f"def {attr}(*args, **kwargs): ...  # Built-in or C++\n")
                else:
                    # constants or other attributes
                    f.write(f"{attr}: {type(cls).__name__} = ...\n")
                
                f.write("\n")
            
            except Exception as e:
                f.write(f"# Error processing {attr}: {e}\n")

if __name__ == "__main__":
    gen_stubs()