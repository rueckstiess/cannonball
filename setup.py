from setuptools import setup, find_packages

setup(
    name="cannonball",
    version="0.0.1",
    packages=find_packages(),
    author="Thomas Rueckstiess",
    author_email="me@tomr.au",
    description="An AI-powered personal productivity system.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/cannonball",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.8",
)