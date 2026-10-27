from setuptools import find_packages, setup

package_name = "pcam_driver"

setup(
    name=package_name,
    version="1.0.0",
    packages=[package_name],
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools", "requests"],
    zip_safe=True,
    maintainer="Hyungseok",
    maintainer_email="engineering@neoma-pcam.com",
    description="NEOMA P-CAM Ros 2 Hardware Reflex Solver Node",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "compliance_node = pcam_driver.compliance_node:main",
        ],
    },
)
