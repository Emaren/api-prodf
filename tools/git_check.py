#!/usr/bin/env python3

import subprocess
import os
import filecmp

repos = {
    "local-staging": {
        "aoe2hd-frontend": "/Users/tonyblum/projects/app-staging",
        "aoe2hd-parsing": "/Users/tonyblum/projects/api-staging",
        "explorerdev": "/Users/tonyblum/projects/explorer-staging",
        "wolodev": "/Users/tonyblum/projects/wolo-staging",
    },
    "local-prod": {
        "aoe2hd-frontend": "/Users/tonyblum/projects/app-prod",
        "aoe2hd-parsing": "/Users/tonyblum/projects/api-prod",
        "app-prodf": "/Users/tonyblum/projects/app-prodf",
        "app-prodn": "/Users/tonyblum/projects/app-prodn",
        "api-prodf": "/Users/tonyblum/projects/api-prodf",
        "api-prodn": "/Users/tonyblum/projects/api-prodn",
        "explorerdev": "/Users/tonyblum/projects/explorer-prod",
        "wolodev": "/Users/tonyblum/projects/wolo-prod",
    },
    "vps-staging": {
        "aoe2hd-frontend": "/var/www/app-staging",
        "aoe2hd-parsing": "/var/www/api-staging",
        "explorerdev": "/var/www/explorer-staging",
        "wolodev": "/var/www/wolo-staging",
    },
    "vps-prod": {
        "aoe2hd-frontend": "/var/www/app-prod",
        "aoe2hd-parsing": "/var/www/api-prod",
        "app-prodf": "/var/www/app_prodf",
        "app-prodn": "/var/www/app-prodn",
        "api-prodf": "/var/www/api-prodf",
        "api-prodn": "/var/www/api-prodn",
        "explorerdev": "/var/www/explorer-prod",
        "wolodev": "/var/www/wolo-prod",
    }
}

def check_status(repo_path):
    if not os.path.exists(repo_path):
        return f"{repo_path} ❌ Not found"
    try:
        os.chdir(repo_path)
        branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
        status = subprocess.check_output(["git", "status", "--short"], text=True).strip()
        remote_diff = subprocess.check_output(
            ["git", "rev-list", "--left-right", "--count", f"{branch}...origin/{branch}"],
            text=True
        ).strip()
        ahead, behind = map(int, remote_diff.split())
        return f"{repo_path} [{branch}] ✅ Ahead: {ahead}, Behind: {behind}, Dirty: {'Yes' if status else 'No'}"
    except Exception as e:
        return f"{repo_path} ❌ Error: {e}"

def check_sync(path1, path2):
    if not os.path.exists(path1) or not os.path.exists(path2):
        return False
    try:
        dircmp = filecmp.dircmp(path1, path2, ignore=[".git", "__pycache__"])
        return not (dircmp.left_only or dircmp.right_only or dircmp.diff_files)
    except Exception:
        return False

def main():
    for scope, paths in repos.items():
        print(f"\n🔍 {scope.upper()} REPOS")
        for name, path in paths.items():
            print(" •", check_status(path))

        if scope.endswith("prod"):
            sync_scope = scope.replace("prod", "staging")
            label = "LOCAL" if scope.startswith("local") else "VPS"
            print(f"\n🔁 {label} STAGING ⇄ PROD SYNC CHECK")
            for name in repos[sync_scope]:
                if name in paths:
                    p1, p2 = repos[sync_scope][name], paths[name]
                    tag = "✅ In sync" if check_sync(p1, p2) else "❌ Not in sync"
                    print(f" • VPS: {p2} ⇄ Local: {p1} {tag}")

    print(f"\n🔁 LOCAL ⇄ PROD SYNC CHECK (Manual Additions)")
    manual_pairs = [
        ("/var/www/app_prodf", "/Users/tonyblum/projects/app-prodf"),
        ("/var/www/app-prodn", "/Users/tonyblum/projects/app-prodn"),
        ("/var/www/api-prodf", "/Users/tonyblum/projects/api-prodf"),
        ("/var/www/api-prodn", "/Users/tonyblum/projects/api-prodn"),
    ]
    for vps_path, local_path in manual_pairs:
        tag = "✅ In sync" if check_sync(vps_path, local_path) else "❌ Not in sync"
        print(f" • VPS: {vps_path} ⇄ Local: {local_path} {tag}")

if __name__ == "__main__":
    main()

