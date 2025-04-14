import sys
import os
import subprocess
import shlex
import readline


def get_matches(text):
    path_dirs = os.environ.get("PATH", "").split(":")
    commands = ["echo", "exit", "type", "pwd", "cd"]  # built-ins
    # Get executables from PATH
    for directory in path_dirs:
        try:
            files = os.listdir(directory)
            commands.extend(files)
        except:
            continue
    # Find matches
    matches = [cmd for cmd in commands if cmd.startswith(text)]
    return sorted(set(matches))  # Remove duplicates and sort


def find_common_prefix(matches):
    if not matches:
        return ""
    prefix = matches[0]
    for match in matches[1:]:
        while not match.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    return prefix


def complete(text, state):
    global last_tab_matches
    global tab_count
    if state == 0:
        matches = get_matches(text)
        last_tab_matches = matches
        if len(matches) > 1:
            common_prefix = find_common_prefix(matches)
            if common_prefix and common_prefix != text:
                # return common_prefix + " "
                # Don't add space for prefix matches
                exact_matches = [m for m in matches if m == common_prefix]
                return common_prefix
            if tab_count == 0:
                sys.stdout.write("\a")  # Ring bell on first tab
                tab_count += 1
                return text
            else:
                # Print matches on second tab
                print()
                print("  ".join(matches))
                print(f"$ {text}", end="")
                tab_count = 0
                return text
        elif len(matches) == 1:
            # return matches[0] + " "
            # Add space only if it's a final match (no other commands start with this)
            other_matches = get_matches(matches[0] + "_")
            if not other_matches:
                return matches[0] + " "
            return matches[0]
    return None


def main():
    global last_tab_matches
    global tab_count
    last_tab_matches = []
    tab_count = 0
    # Uncomment this block to pass the first stage
    # sys.stdout.write("$ ")
    PATH = os.environ.get("PATH", "")
    commands = ["echo", "exit", "type", "pwd", "cd"]
    # Wait for user input
    readline.set_completer(complete)
    readline.parse_and_bind("tab: complete")
    while True:
        sys.stdout.write("$ ")
        command = input()
        if "1>>" in command or "2>>" in command or ">>" in command:
            split_on = (
                "1>>" if "1>>" in command else "2>>" if "2>>" in command else ">>"
            )
            parts = command.split(split_on)
            left_command = shlex.split(parts[0].strip())  # Command to execute
            right_file = parts[1].strip()  # File to write output to
            # Only create directories if there's a path
            dir_path = os.path.dirname(right_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            try:
                result = subprocess.run(
                    left_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                with open(right_file, "a") as f:
                    if "2>>" in command:
                        # For 2>>, write stderr to file and stdout to console
                        if result.stderr:
                            f.write(result.stderr)
                        if result.stdout:
                            print(result.stdout.strip())
                    else:
                        # For >> or 1>>, write stdout to file and stderr to console
                        if result.stdout:
                            f.write(result.stdout)
                        if result.stderr:
                            sys.stderr.write(result.stderr)
            except FileNotFoundError:
                sys.stderr.write(f"{right_file}: No such file or directory\n")
            except Exception as e:
                sys.stderr.write(f"Error: {e}\n")
            continue
        elif "2>" in command:
            parts = command.split("2>")
            left_command = shlex.split(parts[0].strip())  # Command to execute
            right_file = parts[1].strip()  # File to write output to
            os.makedirs(os.path.dirname(right_file), exist_ok=True)
            try:
                # Run the command and capture stdout and stderr
                result = subprocess.run(
                    left_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                # Open the output file to write stderr
                with open(right_file, "w") as f:
                    if result.stderr:
                        f.write(result.stderr)
                    # If there's stdout and no stderr, write stdout
                    # elif result.stdout:
                    #     print(result.stdout, end='')  # Print stdout to console
                if result.stdout:
                    print(result.stdout.strip())
                # Return stdout for potential further processing
                # return result.stdout if result.stdout else ""
            except FileNotFoundError as e:
                # Handle cases where the command itself is invalid
                with open(right_file, "w") as f:
                    error_msg = f"Command not found: {e}\n"
                    f.write(error_msg)
            continue
        elif "1>" in command or ">" in command:
            parts = command.split(
                "1>") if "1>" in command else command.split(">")
            left_command = shlex.split(parts[0].strip())  # Command to execute
            right_file = parts[1].strip()  # File to write output to
            try:
                with open(right_file, "w") as f:
                    result = subprocess.run(
                        left_command, stdout=f, stderr=subprocess.PIPE, text=True
                    )
                    if result.stderr:
                        sys.stderr.write(result.stderr)
            except FileNotFoundError:
                sys.stderr.write(f"{right_file}: No such file or directory\n")
            except Exception as e:
                sys.stderr.write(f"Error: {e}\n")
            continue
        match command.split():
            case ("exit", "0"):
                break
            case ("echo", *args):
                if (command.startswith("'") and command.endswith("'")) or (
                    command.startswith('"') and command.endswith('"')
                ):
                    message = command[6:-1]
                    print(command[6:-1])
                else:
                    message = shlex.split(command[5:])
                    print(" ".join(message))
            case ("type", *args):
                evaled_command = command.split(" ")[1]
                # cmd = command.split(' ')[1]
                cmd_path = None
                paths = PATH.split(":")
                for path in paths:
                    if os.path.exists(f"{path}//{evaled_command}") and os.access(f"{path}//{evaled_command}", os.X_OK):
                        cmd_path = f"{path}/{evaled_command}"
                if evaled_command in commands:
                    print(f"{evaled_command} is a shell builtin")
                elif cmd_path:
                    print(f"{evaled_command} is {cmd_path}")
                else:
                    print(f"{evaled_command}: not found")
            case ["pwd"]:
                sys.stdout.write(f"{os.getcwd()}\n")
            case ("cd", *args):
                command = command.split()
                path = "".join(command[1:])
                path = os.path.expanduser(path)
                try:
                    # os.chdir(os.path.join(curr_dir, arg))
                    # os.chdir(" ".join(command[1:]))
                    os.chdir(path)
                except FileNotFoundError:
                    print(
                        "cd: " + " ".join(command[1:]) +
                        ": No such file or directory"
                    )
            case _:
                # Try to execute the command using os.system
                program = command.split()[0]
                cmd_path = None
                # Search for the program in PATH
                for path in PATH.split(":"):
                    potential_path = os.path.join(path, program)
                    if os.path.isfile(potential_path) and os.access(
                        potential_path, os.X_OK
                    ):
                        cmd_path = potential_path
                        break
                args = shlex.split(command)
                # executablePath = cmd_path
                if cmd_path:
                    # Use os.system to execute the command
                    # os.system(command)
                    result = subprocess.run(
                        args, capture_output=True, text=True)
                    print(result.stdout, end="")
                elif command.startswith('"') or command.startswith("'"):
                    result = subprocess.run(
                        args, capture_output=True, text=True)
                    print(result.stdout, end="")
                else:
                    print(f"{program}: command not found")

                    # print(f"{program}: command not found")
if __name__ == "__main__":
    main()
