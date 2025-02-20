#!/usr/bin/env python3

import os
import json
import shutil

from common import (
    run_kiwix_build,
    main_project_versions,
    release_versions,
    get_postfix,
    make_archive,
    create_desktop_image,
    update_flathub_git,
    upload_archive,
    fix_macos_rpath,
    trigger_docker_publish,
    BASE_DIR,
    TMP_DIR,
    HOME,
    OS_NAME,
    PLATFORM_TARGET,
    DESKTOP,
    notarize_macos_build,
)

from upload_to_bintray import upload_from_json


if os.environ.get('GITHUB_EVENT_NAME') == 'schedule':
    RELEASE = False
else:
    RELEASE = True

if PLATFORM_TARGET == "android":
    TARGETS = ("libkiwix-app",)
elif PLATFORM_TARGET.startswith("iOS"):
    TARGETS = ("libzim", "libkiwix")
elif PLATFORM_TARGET.startswith("native_"):
    if OS_NAME == "osx":
        TARGETS = ("libzim", ) if PLATFORM_TARGET == "native_mixed" else ("libzim", "zim-tools", "libkiwix")
    else:
        if DESKTOP:
            TARGETS = ("kiwix-desktop",)
        elif PLATFORM_TARGET == "native_mixed":
            TARGETS = ("libzim",)
        else:
            TARGETS = ("zim-tools", "libkiwix", "kiwix-tools")
elif PLATFORM_TARGET in ("win32_static", "armhf_static", "i586_static"):
    TARGETS = ("kiwix-tools",)
elif PLATFORM_TARGET == "flatpak":
    TARGETS = ("kiwix-desktop",)
else:
    TARGETS = ("libzim", "zim-tools", "libkiwix", "kiwix-tools")

# Filter what to build if we are doing a release.
if RELEASE:
    def release_filter(project):
        if project == "libkiwix-app":
            project = "libkiwix"
        return release_versions.get(project) is not None
    TARGETS = tuple(filter(release_filter, TARGETS))

if RELEASE and PLATFORM_TARGET == "android":
    # libkiwix need to know the extrapostfix version to correctly generate the pom.xml file.
    extra_postfix = release_versions.get('libkiwix')
    if extra_postfix:
        os.environ['KIWIXLIB_BUILDVERSION'] = str(extra_postfix)

for target in TARGETS:
    run_kiwix_build(target, platform=PLATFORM_TARGET, make_release=RELEASE)
    if target == "kiwix-desktop":
        archive = create_desktop_image(make_release=RELEASE)
    else:
        if PLATFORM_TARGET == "native_mixed" and OS_NAME == "osx":
            fix_macos_rpath(target)
            notarize_macos_build(target)
        archive = make_archive(target, make_release=RELEASE)
    if archive:
        upload_archive(archive, target, make_release=RELEASE)
        if RELEASE and target in ("zim-tools", "kiwix-tools"):
            trigger_docker_publish(target)

# We have few more things to do for release:
if RELEASE:
    # Publish source archives
    if PLATFORM_TARGET in ("native_dyn", "native_mixed") and OS_NAME != "osx":
        for target in TARGETS:
            if release_versions.get(target) != 0:
                continue
            run_kiwix_build(
                target, platform=PLATFORM_TARGET, make_release=RELEASE, make_dist=True
            )
            full_target_name = "{}-{}".format(target, main_project_versions[target])
            if target == "kiwix-desktop":
                archive = (
                    BASE_DIR / full_target_name / "{}.tar.gz".format(full_target_name)
                )
            else:
                archive = (
                    BASE_DIR
                    / full_target_name
                    / "meson-dist"
                    / "{}.tar.xz".format(full_target_name)
                )
            upload_archive(archive, target, make_release=RELEASE)

    # Publish flathub
    if PLATFORM_TARGET == "flatpak" and "kiwix-desktop" in TARGETS:
        update_flathub_git()

    if PLATFORM_TARGET == "android" and "libkiwix-app" in TARGETS:
        postfix = get_postfix("libkiwix")
        basename = "kiwixlib-{}".format(postfix)

        output_release_dir = (
            HOME / "BUILD_android" / "libkiwix-app" / "kiwixLibAndroid" / "build"
        )
        shutil.copy(
            str(output_release_dir / "outputs" / "aar" / "kiwixLibAndroid-release.aar"),
            str(TMP_DIR / (basename + ".aar")),
        )
        shutil.copy(
            str(output_release_dir / "pom.xml"), str(TMP_DIR / (basename + ".pom"))
        )

        json_filename = "{}_bintray_info.json".format(basename)
        data = {
            "version": postfix,
            "files": [basename + ext for ext in (".aar", ".pom")],
        }
        with open(str(TMP_DIR / json_filename), "w") as f:
            json.dump(data, f)

        upload_from_json(TMP_DIR / json_filename)
