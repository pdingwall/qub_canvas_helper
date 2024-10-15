from setuptools import setup, find_packages

setup(
    name="qub_canvas_helper",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "requests"
    ],
    include_package_data=True,
    description="A helper package for managing Canvas assignments and calendar events.",
    author="Paul Dingwall",
    author_email="p.dingwall@qub.ac.uk",
    url="https://github.com/pdingwall/qub_canvas_helper",
)
