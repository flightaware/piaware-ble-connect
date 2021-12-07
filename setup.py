from setuptools import setup, find_packages
setup(
    name="piaware-ble-connect",
    version="7.0",
    description="Bluetooth LE application for configurating piaware",
    url="",
    author="Eric Tran",
    author_email="eric.tran@flightawre.com",
    license="MIT",
    packages=find_packages(),
    install_requires=["dbus-python","requests"]
)
