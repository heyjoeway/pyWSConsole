import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyWSConsole-heyjoeway",
    version="1.1.0",
    author="Joseph Judge",
    author_email="joe@jojudge.com",
    description="Console-like client/server WebSockets wrapper for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/heyjoeway/pyWSConsole",
    project_urls={
        "Bug Tracker": "https://github.com/heyjoeway/pyWSConsole/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=[
        'websockets'
    ]
)
