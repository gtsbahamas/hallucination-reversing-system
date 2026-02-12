#!/usr/bin/env python
"""Django management script."""
import os
import sys

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myapi.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
