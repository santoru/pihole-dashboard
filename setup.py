""" Tool Setup """
# !/usr/bin/env python3

from setuptools import setup

PACKAGE_NAME = "pihole-dashboard"
VERSION = "2.0.10"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


if __name__ == "__main__":
    setup(
        name=PACKAGE_NAME,
        version=VERSION,
        author="santoru",
        author_email="santoru@pm.me",
        description="Minimal dashboard for Pi-Hole that works with WaveShare's 2.13 inch HAT display (v6 compatible)",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/santoru/pihole-dashboard",
        packages=["pihole_dashboard"],
        package_data={
            'pihole_dashboard': ['font/*.ttf'],
        },
        data_files=[
            ('/etc/cron.d', ['cron/pihole-dashboard-cron']),
            ('/etc/pihole-dashboard', ['conf/config.toml']),
        ],
        scripts=[
            "scripts/pihole-dashboard-clean-screen",
            "scripts/pihole-dashboard-draw"
        ],
        python_requires='>=3.3.5',
        install_requires=[
            "waveshare-epd",
            "netifaces>=0.10.9",
            "Pillow>=8.2.0",
            "toml>=0.10.2"
        ],
    )
