import os
import subprocess
import pexpect
from pathlib import Path
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from dotenv import load_dotenv
load_dotenv()

def index(request):
    if request.user.is_superuser:
        return render(request, "production_admin/index.html")
    else:
        return redirect("corehome")


def pull_and_restart(request):
    if request.user.is_superuser:
        # Check if we're in development mode
        if settings.DEVELOPMENT:
            messages.success(
                request, 
                "[DEVELOPMENT MODE] Git pull would show results here. "
                "This action is disabled in development environment."
            )
            messages.success(
                request, 
                "[DEVELOPMENT MODE] Gunicorn restart would show results here. "
                "This action is disabled in development environment."
            )
            return redirect("production_admin:index")
            
        try:
            # First do git pull
            git_pull_result = subprocess.run(
                ["git", "pull", "origin", "main"],
                check=True,
                capture_output=True,
                text=True,
            )
            messages.success(request, f"Git pull results: {git_pull_result.stdout}")

            # Use pexpect to handle the sudo password prompt
            server_password = os.getenv('SERVER_PASSWORD')
            try:
                child = pexpect.spawn('sudo systemctl restart gunicorn.socket')
                # Wait for password prompt
                i = child.expect(['password for.*:', pexpect.EOF, pexpect.TIMEOUT], timeout=5)
                if i == 0:  # Password prompt received
                    child.sendline(server_password)
                    child.expect(pexpect.EOF, timeout=5)
                    messages.success(request, "Gunicorn service restarted successfully")
                elif i == 1:  # EOF before password prompt
                    messages.error(request, "Unexpected EOF while restarting Gunicorn")
                else:  # Timeout
                    messages.error(request, "Timeout while waiting for password prompt")
                child.close()
            except pexpect.ExceptionPexpect as e:
                messages.error(
                    request, f"Error restarting Gunicorn: {str(e)}"
                )

            return redirect("production_admin:index")
            
        except subprocess.CalledProcessError as e:
            messages.error(
                request, f"Error during git pull: {e.stderr}"
            )
            return redirect("production_admin:index")
    else:
        return redirect("corehome")


def migrate_database(request, app_name):
    if app_name == 'all':
        app_name = None
    
    if request.user.is_superuser:
        if settings.DEVELOPMENT:
            messages.success(
                request, 
                "[DEVELOPMENT MODE] Makemigrations would show results here. "
                "This action is disabled in development environment."
            )
            return redirect("production_admin:index")

        try:
            makemigrations_command = ["python3", "manage.py", "makemigrations"]
            if app_name:
                makemigrations_command.append(app_name)
            makemigrations_result = subprocess.run(
                makemigrations_command, check=True, capture_output=True, text=True
            )
            messages.success(
                request, f"Makemigrations results: {makemigrations_result.stdout}"
            )
            migrate_command = ["python3", "manage.py", "migrate"]
            if app_name:
                migrate_command.append(app_name)
            migrate_result = subprocess.run(
                migrate_command, check=True, capture_output=True, text=True
            )
            messages.success(request, f"Migrate results: {migrate_result.stdout}")
            return redirect("production_admin:index")
        except subprocess.CalledProcessError as e:
            messages.error(request, f"Error during migration: {e.stderr}")
            return redirect("production_admin:index")
    else:
        return redirect("corehome")
