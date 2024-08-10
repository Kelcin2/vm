#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
import logging
import os
import pathlib
import sys

build_version = "v1.0.2"
github = "https://github.com/Kelcin2/vm"
support_components = {
    "JAVA": ["JVM_HOME", "JVM_SYMLINK", "JRE_SYMLINK"],
    "Gradle": ["GVM_HOME", "GVM_SYMLINK"],
    "Groovy": ["GROVM_HOME", "GROVM_SYMLINK"],
    "Node": ["NVM_HOME", "NVM_SYMLINK"],
    "Kubectl": ["KVM_HOME", "KVM_SYMLINK"],
    "Maven": ["MVM_HOME", "MVM_SYMLINK"],
    "Protoc": ["PROVM_HOME", "PROVM_SYMLINK"],
    "Python": ["PVM_HOME", "PVM_SYMLINK"]
}

support_components_matrix = {}

exclude_folders = {
    "Maven": ["repository"]
}

cmd_version = ["version", "--version", "v", "-v"]
cmd_quit = ["q", "quit", "e", "exit"]
cmd_previous = ["p", "previous", "l", "last", "!"]
quit_msg = "Type {} for exit".format(" ".join(["`{}`".format(n) for n in cmd_quit]))
previous_msg = "Type {} for previous page".format(" ".join(["`{}`".format(n) for n in cmd_previous]))


def is_admin():
    if os.name == 'nt':
        # if windows system
        import ctypes
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except BaseException:
            return False
    else:
        return False


def set_env(is_system, k, v):
    if is_system and not is_admin():
        logging.error("Failed to set system environment cause current user doesn't have an admin permission")
        return
    cmd = "setx{} {} {}".format(" /M" if is_system else "", k, v)
    os.popen(cmd).read()


def create_symlink_for_dir(source_dir, target_dir):
    file = pathlib.Path(source_dir)
    if not file.exists() and not os.path.islink(file):
        os.symlink(target_dir, source_dir, True)
        return True
    elif os.path.islink(file):
        if not file.is_dir() or target_dir != os.readlink(os.path.abspath(file)):
            os.unlink(source_dir)
            os.symlink(target_dir, source_dir, True)
        return True
    logging.error("Path `{}` already exists, can't create symlink for it".format(source_dir))
    return False


def remove_symlink_for_dir(source_dir):
    file = pathlib.Path(source_dir)
    if os.path.islink(file):
        os.unlink(file)


def is_configured_component(v_c_home, v_c_symlink):
    c_home = os.getenv(v_c_home)
    if c_home is None or not str(c_home).strip():
        return False
    c_symlink = os.getenv(v_c_symlink)
    if c_symlink is None or not str(c_symlink).strip():
        return False
    return True


def version_selected_by(cn):
    symlink = os.getenv(support_components[cn][1])
    if symlink is None or not symlink.strip():
        return None
    file = pathlib.Path(symlink.strip())
    if not os.path.islink(file):
        return None
    target_path = os.readlink(os.path.abspath(file))
    base_name = os.path.basename(os.path.abspath(target_path))
    return base_name if "jdk" != base_name.lower() else os.path.basename(os.path.abspath(os.path.join(target_path.strip(), "..")))


def set_matrix(index, cn=None, versions=None):
    if index not in support_components_matrix or support_components_matrix[index] is None:
        support_components_matrix[index] = {}
    if cn is not None:
        support_components_matrix[index]["cn"] = cn
    if versions is not None:
        support_components_matrix[index]["versions"] = versions


def switch_version_for_java(c_index, v_index):
    version_home = os.getenv(support_components[support_components_matrix[c_index]["cn"]][0])
    jvm_symlink = os.getenv(support_components[support_components_matrix[c_index]["cn"]][1])
    jre_symlink = os.getenv(support_components[support_components_matrix[c_index]["cn"]][2])
    version = support_components_matrix[c_index]["versions"][int(v_index) - 1]

    bin_dir = pathlib.Path(os.path.join(version_home, version, "jdk"))
    if bin_dir.exists():
        result = create_symlink_for_dir(jvm_symlink, os.path.abspath(bin_dir))
        if result and jre_symlink is not None:
            jre_bin = pathlib.Path(os.path.join(version_home, version, "jdk", "jre"))
            if jre_bin.exists():
                result = create_symlink_for_dir(jre_symlink, os.path.abspath(jre_bin))
            else:
                remove_symlink_for_dir(jre_symlink)
    else:
        bin_dir = pathlib.Path(os.path.join(version_home, version))
        result = create_symlink_for_dir(jvm_symlink, os.path.abspath(bin_dir))
        if result and jre_symlink is not None:
            jre_bin = pathlib.Path(os.path.join(version_home, version, "jre"))
            if jre_bin.exists():
                result = create_symlink_for_dir(jre_symlink, os.path.abspath(jre_bin))
            else:
                remove_symlink_for_dir(jre_symlink)
    original_java_home = os.getenv("JAVA_HOME")
    if result and original_java_home is not None and original_java_home.strip():
        java_home = os.path.abspath(bin_dir)
        if java_home != original_java_home.strip():
            set_env(True, "JAVA_HOME", java_home)

    return result


def switch_version(c_index, v_index, env_need_changed=None):
    version_home = os.getenv(support_components[support_components_matrix[c_index]["cn"]][0])
    symlink = os.getenv(support_components[support_components_matrix[c_index]["cn"]][1])
    version = support_components_matrix[c_index]["versions"][int(v_index) - 1]

    version_dir = pathlib.Path(os.path.join(version_home, version))
    success = create_symlink_for_dir(symlink, os.path.abspath(version_dir))
    if success and env_need_changed is not None and os.getenv(env_need_changed) is not None and os.getenv(env_need_changed).strip() and os.getenv(env_need_changed).strip() != os.path.abspath(version_dir):
        set_env(True, env_need_changed, os.path.abspath(version_dir))
    return success


def show_support_components():
    index = 0
    print("\nConfigured Components currently:\n")
    for k, v in support_components.items():
        if is_configured_component(v[0], v[1]):
            index += 1
            set_matrix(str(index), cn=k)
            print("  {}. {}".format(index, k))

    if 0 == index:
        print("You have not configured any components, Please type `vm help` for details")
    else:
        print("\nNote: {}\n".format(quit_msg))
    return 0 < index


def show_versions(c_index, v_c_home):
    c_home = os.getenv(v_c_home)
    cn = support_components_matrix[c_index]['cn']
    print("\nInstalled Versions for {} currently:\n".format(cn))
    file = None
    try:
        file = pathlib.Path(c_home)
    except BaseException:
        logging.error("The path specified by System Environment `{}` is not a valid directory".format(v_c_home))
        exit(1)
    index = 0
    versions = []
    if file is not None and file.is_dir():
        version_selected = version_selected_by(cn)
        for version in os.listdir(c_home):
            version_file = pathlib.Path(os.path.join(c_home, version.strip()))
            if not version_file.is_dir() or (cn in [v for v in exclude_folders.keys()] and version.strip().lower() in exclude_folders[cn]):
                continue
            versions.append(version.strip())
            index += 1
            print("  {} {}. {}".format("*" if version_selected is not None and version_selected.strip() ==  version.strip() else " ", index, version))
    if 0 < index:
        set_matrix(c_index, versions=versions)
    else:
        print("You have not installed any versions for {}, Please type `vm help` for details".format(cn))
    print("\nNote: {}, {}\n".format(quit_msg, previous_msg))
    return 0 < index


def show_help():
    print("\nVersion: {}".format(build_version))
    print("\n!!!IMPORTANT!!! Must Run as Administrator(for Creating Symlinks) !!!IMPORTANT!!!")
    print("\nJust Simply Type `vm` to GO!")

    print("\nusage: vm [-h][-v]\n")
    print("optional arguments:\n")
    print("  -h, --help     Show this help message and exit")
    print("  -v, --version  Show program version info and exit")

    print("\n\nAll Components Supported by Version Management(`vm` for command):\n")
    index = 0
    for k, v in support_components.items():
        index += 1
        print("  {}. {}".format(index, k))
        if k in ["JAVA"]:
            print("    To switch {} version freely, you MUST set env variable `{}` for fetching versions, set `{}` for creating symlink and add `%{}%\\bin` to env variable `PATH`. Alternatively you can set env variable `{}` for creating corresponding symlink and add `%{}%\\bin` to env variable `PATH`"
                  .format(k, v[0], v[1], v[1], v[2], v[2]))
        elif k == "Python":
            print("    To switch {} version freely, you MUST set env variable `{}` for fetching versions, set `{}` to create symlink and add `%{}%` to env variable `PATH` for `python` command and add `%{}%\\Scripts` to env variable `PATH` for `pip` command"
                  .format(k, v[0], v[1], v[1], v[1]))
        elif k in ["Gradle", "Maven", "Groovy", "Protoc"]:
            print("    To switch {} version freely, you MUST set env variable `{}` for fetching versions, set `{}` for creating symlink and add `%{}%\\bin` to env variable `PATH`."
                  .format(k, v[0], v[1], v[1]))
        else:
            print("    To switch {} version freely, you MUST set env variable `{}` for fetching versions, set `{}` for creating symlink and add `%{}%` to env variable `PATH`."
                  .format(k, v[0], v[1], v[1]))
        print()

    print("Any Bug or Suggestion Please Commit to Github {} .\n".format(github))


def show_build_version():
    print("\nVersion: {}\n".format(build_version))


def input_with_keyboard_interrupt(prompt_msg, default_value_when_keyboard_interrupt=None):
    try:
        return input(prompt_msg)
    except KeyboardInterrupt as e:
        if default_value_when_keyboard_interrupt is not None:
            return default_value_when_keyboard_interrupt
        else:
            raise e


def process():
    process_c_index()


def process_c_index():
    if not show_support_components():
        exit(0)

    c_index_input_msg = "Which component would you like to choose?(empty for first one):"
    c_index = input_with_keyboard_interrupt(c_index_input_msg, cmd_quit[0])
    while c_index is not None and c_index.strip() and c_index.strip().lower() not in (cmd_quit + [n for n in support_components_matrix.keys()]):
        print("Error Input, Please try again!\n")
        c_index = input_with_keyboard_interrupt(c_index_input_msg, cmd_quit[0])
    if c_index is None or not c_index.strip():
        c_index = "1"
    c_index = c_index.strip().lower()
    if c_index in cmd_quit:
        exit(0)
    process_version(c_index)


def process_version(c_index):
    version_mapping = {}
    if show_versions(c_index, support_components[support_components_matrix[c_index]["cn"]][0]):
        version_mapping = {str(index + 1): item for index, item in enumerate(support_components_matrix[c_index]["versions"])}

    input_msg = "Which version for {} would you like to switch to?(empty for first one):".format(support_components_matrix[c_index]["cn"])
    version_index = input_with_keyboard_interrupt(input_msg, cmd_quit[0])
    while (version_index is not None and version_index.strip() and version_index.strip().lower() not in (cmd_quit + cmd_previous + [n for n in version_mapping.keys()])) or (not version_index.strip() and 0 >= len(version_mapping.keys())):
        print("Error Input, Please try again!\n")
        version_index = input_with_keyboard_interrupt(input_msg, cmd_quit[0])
    if version_index is None or not version_index.strip():
        version_index = "1"
    version_index = version_index.strip().lower()
    if version_index in cmd_quit:
        exit(0)
    if version_index in cmd_previous:
        process_c_index()
    else:
        process_switch_version(c_index, version_index)


def process_switch_version(c_index, v_index):
    cn = support_components_matrix[c_index]['cn']
    if cn in ["JAVA"]:
        success = switch_version_for_java(c_index, v_index)
    elif cn in ["Maven"]:
        success = switch_version(c_index, v_index, "MAVEN_HOME")
    else:
        success = switch_version(c_index, v_index)
    version = support_components_matrix[c_index]['versions'][int(v_index) - 1]
    if not success:
        print("Switch version to `{}` for `{}` failed! Please type `vm help` for details!".format(version, cn))
    else:
        print("Successfully switch version to `{}` for `{}` !\n".format(version, cn))


def main():
    args = sys.argv[1:]
    if len(args) == 1 and args[0].strip().lower() in cmd_version:
        show_build_version()
    elif len(args) > 0:
        show_help()
    elif not is_admin():
        logging.error("Must run as administrator(for creating symlinks)")
    else:
        process()


if __name__ == '__main__':
    main()
