from setuptools import setup, find_packages

setup(
    name="cannonball",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "networkx>=3.1",
        "pymongo>=4.5.0",
        "regraph>=2.0.2",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="An AI-powered productivity system based on directed acyclic graphs",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/productivity-system",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)
