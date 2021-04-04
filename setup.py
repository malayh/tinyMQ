import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt","r") as f:
    dependencies = f.read().split("\n")

setuptools.setup(
    name="tinyMQ",
    version="0.0.1",
    author="Malay Hazarika",
    author_email="malay.hazarika@gmail.com",
    description="Transient inmemory Messaging Queue",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/malayh/tinyMQ",
    project_urls={
        "Bug Tracker": "https://github.com/malayh/tinyMQ/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "."},
    packages=["tinyMQ"],
    python_requires=">=3.7",
    install_requires=dependencies,
    
    entry_points={
        'console_scripts': [
            'tmqserver = tinyMQ:execute_cli'
        ]
    },
    
)