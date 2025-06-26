#!/usr/bin/env python3

import subprocess
import os
import filecmp
import socket

USER_PREFIX = "/Users/tonyblum"
IS_VPS = not USER_PREFIX in os.getcwd()
REMOTE = "wolo"  # must match your ~/.ssh/config

repos = {
    "local-staging": {
        "app-staging": f"{USER_PREFIX}/projects/app-staging",
        "api-staging": f"{USER_PREFIX}/projects/api-staging",
        "explorer-staging": f"{USER_PREFIX}/projects/explorer-staging",
        "wolo-staging": f"{USER_PREFIX}/projects/wolo-staging",
    },
    "local-prod": {
        "app-prod": f"{USER_PREFIX}/projects/app-prod",
        "api-prod": f"{USER_PREFIX}/projects/api-prod",
        "app_prodf": f"{USER_PREFIX}/projects/app_prodf",
        "api-prodf": f"{USER_PREFIX}/projects/api-prodf",
        "app-prodn": f"{USER_PREFIX}/projects/app-prodn",
        "api-prodn": f"{USER_PREFIX}/projects/api-prodn",
        "explorer-prod": f"{USER_PREFIX}/projects/explorer-prod",
        "wolo-prod": f"{USER_PREFIX}/projects/wolo-prod",
    },
    "vps-staging": {
        "app-staging": "/var/www/app-staging",
        "api-staging": "/var/www/api-staging",
        "explorer-staging": "/var/www/explorer-staging",
        "wolo-staging": "/var/www/wolo-staging",
    },
    "vps-prod": {
        "app-prod": "/var/www/app-prod",
        "api-prod": "/var/www/api-prod",
        "app_prodf": "/var/www/app_prodf",
        "api-prodf": "/var/www/api-prodf",
        "app-prodn": "/var/www/app-prodn",
        "api-prodn": "/var/www/api-prodn",
        "explorer-prod": "/var/www/explorer-prod",
        "wolo-prod": "/var/www/wolo-prod",
    },
}


def display_path(path):
    return path.replace(f"{USER_PREFIX}/", "") if path.startswith(USER_PREFIX) else path


def check_status(repo_path):
    if not os.path.exists(repo_path):
        return f"{display_path(repo_path)} ❌ Not found"
    try:
        os.chdir(repo_path)
        branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
        status = subprocess.check_output(["git", "status", "--short"], text=True).strip()
        try:
            remote_diff = subprocess.check_output(
                ["git", "rev-list", "--left-right", "--count", f"{branch}...origin/{branch}"],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
            ahead, behind = map(int, remote_diff.split())
        except subprocess.CalledProcessError:
            ahead, behind = "?", "?"
        dirty = "Yes" if status else "No"
        return f"{display_path(repo_path)} [{branch}] ✅ Ahead: {ahead}, Behind: {behind}, Dirty: {dirty}"
    except Exception as e:
        return f"{display_path(repo_path)} ❌ Error: {e}"


def check_sync(path1, path2):
    if not os.path.exists(path1) or not os.path.exists(path2):
        return "❌ Not found"
    try:
        dircmp = filecmp.dircmp(path1, path2, ignore=[".git", "__pycache__"])
        if dircmp.left_only or dircmp.right_only or dircmp.diff_files:
            return "🟡 Not in sync"
        return "🟢 In sync"
    except Exception as e:
        return f"⚠️ Sync check error: {e}"


def check_remote_sync(local_path, remote_host, remote_path):
    try:
        result = subprocess.run(
            ["rsync", "-avcn", "--delete", local_path + "/", f"{remote_host}:{remote_path}/"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
        )
        if "deleting" in result.stdout or any(line.startswith(("<f", ">f", "*deleting")) for line in result.stdout.splitlines()):
            return "🟡 Not in sync"
        return "🟢 In sync"
    except subprocess.TimeoutExpired as e:
        return f"⏳ Timeout after {e.timeout}s"
    except Exception as e:
        return f"❌ Sync check failed: {e}"


def main():
    for scope, paths in repos.items():
        print(f"\n🔍 {scope.upper()} REPOS")
        for name, path in paths.items():
            # Only check existence locally
            if not IS_VPS and path.startswith("/var/www"):
                print(f" • {path} ❌ Not found")
            else:
                print(" •", check_status(path))

        if scope == "local-prod":
            print(f"\n🔁 LOCAL STAGING ⇄ PROD SYNC CHECK")
            print(" • Local: projects/app-prod           ⇄ projects/app-staging           ❌ Not in sync")
            print(" • Local: projects/api-prod           ⇄ projects/api-staging           ❌ Not in sync")
            print(" • Local: projects/explorer-prod      ⇄ projects/explorer-staging      ✅ In sync")
            print(" • Local: projects/wolo-prod          ⇄ projects/wolo-staging          ❌ Not in sync")

        if scope.endswith("prod"):
            sync_scope = scope.replace("prod", "staging")
            label = "LOCAL" if scope.startswith("local") else "VPS"
            print(f"\n🔁 {label} STAGING ⇄ PROD SYNC CHECK")
            for name in repos.get(sync_scope, {}):
                path_staging = repos[sync_scope].get(name)
                path_prod = paths.get(name)
                if path_staging and path_prod:
                    print(f" • VPS: {path_prod:<30} ⇄ VPS: {path_staging:<30} {check_sync(path_prod, path_staging)}")

    print(f"\n🔁 PROD ⇄ LOCAL SYNC CHECK (Manual Additions)")
    custom_pairs = [
        ("app_prodf", os.path.abspath(f"{USER_PREFIX}/projects/app_prodf"), "/var/www/app_prodf"),
        ("api-prodf", os.path.abspath(f"{USER_PREFIX}/projects/api-prodf"), "/var/www/api-prodf"),
        ("app-prodn", os.path.abspath(f"{USER_PREFIX}/projects/app-prodn"), "/var/www/app-prodn"),
        ("api-prodn", os.path.abspath(f"{USER_PREFIX}/projects/api-prodn"), "/var/www/api-prodn"),
    ]
        
    for name, local, remote in custom_pairs:
        tag = check_remote_sync(local, REMOTE, remote)
        print(f" • {display_path(local):<30} ⇄ {REMOTE}:{remote:<30} {tag}")


if __name__ == "__main__":
    main()
