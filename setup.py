""" Tool Setup """
# !/usr/bin/env python3

import os
from shutil import copyfile
from setuptools import setup
from setuptools.command.install import install

PACKAGE_NAME = "pihole-dashboard"
VERSION = "2.0.0"  # Updated for Pi-hole v6 compatibility

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


def parse_requirements(filename):
    """Load requirements from a pip requirements file."""
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


class PostInstallJob(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        print("Installing cronjob...")
        self_dir = os.path.dirname(os.path.realpath(__file__))
        cron_dir = os.path.join(self_dir, 'cron')
        copyfile(os.path.join(cron_dir, "pihole-dashboard-cron"),
                 "/etc/cron.d/pihole-dashboard-cron")
        print("Installing config file...")
        self_dir = os.path.dirname(os.path.realpath(__file__))
        conf_dir = os.path.join(self_dir, 'conf')
        conf_sys_dir = "/etc/pihole-dashboard"
        if not os.path.exists(conf_sys_dir):
            os.makedirs(conf_sys_dir)
        copyfile(os.path.join(conf_dir, "config.toml"),
                 "/etc/pihole-dashboard/config.toml")
        print("Done.")


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
        package_data={'pihole_dashboard': ['font/*.ttf']},
        scripts=[
            "scripts/pihole-dashboard-clean-screen",
            "scripts/pihole-dashboard-draw"
        ],
        python_requires='>=3.3.5',
        install_requires=parse_requirements("requirements.txt"),
        cmdclass={
            'install': PostInstallJob,
        },
    )
