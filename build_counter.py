import os

# Read the build number from the environment variable
build_number = os.environ.get("GITHUB_RUN_NUMBER")

if build_number:
    build_numnber = int(build_number)

    with open("opteryx/__version__.py", "r") as f:
        contents = f.read().splitlines()[1:]

    # Save the build number to the build.py file
    with open("opteryx/__version__.py", "w") as f:
        f.write(f"__build__ = {build_number}\n")
        f.write("\n".join(contents))

    print(f"Build Number: {build_number}")

__version__ = "notset"
with open(f"{LIBRARY}/__version__.py", mode="r") as v:
    vers = v.read()
exec(vers)  # nosec
os.environ["OPTERYX_VERSION"] = __version__
