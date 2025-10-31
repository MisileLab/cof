# Cof - A Version Control System for Binary Files

Cof is a version control system (VCS) designed and optimized for handling large binary files. It provides a git-like command-line interface while leveraging block-level deduplication and a tiered storage system to efficiently manage and store large files.

## Key Features

*   **Block-Level Deduplication:** Cof splits files into blocks and stores each block only once. This significantly reduces storage requirements when working with large, repetitive files.
*   **Tiered Storage:** A multi-tiered storage system (hot, warm, and cold) is used to manage blocks based on their access frequency, optimizing storage costs and performance.
*   **Content-Aware Chunking:** The system uses content-aware chunking to intelligently divide files into blocks, improving deduplication ratios.
*   **Git-like Interface:** Cof provides a familiar command-line interface with commands like `init`, `add`, `commit`, `log`, `status`, `branch`, `checkout`, and `merge`.
*   **Built-in Authentication and Remotes:** Cof includes a simple, self-hosted authentication and remote repository system, allowing you to manage access to your repositories without relying on third-party services.

## Installation

You can install Cof using `uv`:

```bash
uv tool install git+https://github.com/misilelab/cof
```

or
```bash
# Clone repository
uv sync
```

## Getting Started

Here's a quick guide to get you started with Cof:

1.  **Initialize a new repository:**

    ```bash
    cof init
    ```

2.  **Add files to the staging area:**

    ```bash
    cof add <file1> <file2> ...
    ```

3.  **Commit your changes:**

    ```bash
    cof commit -m "Your commit message"
    ```

4.  **View the commit history:**

    ```bash
    cof log
    ```

5.  **Check the status of your repository:**

    ```bash
    cof status
    ```

## Command Reference

Here is a list of the most common commands:

| Command         | Description                                       |
| --------------- | ------------------------------------------------- |
| `cof init`      | Initialize a new Cof repository.                  |
| `cof add`       | Add files to the staging area.                    |
| `cof commit`    | Create a new commit.                              |
| `cof log`       | Show the commit history.                          |
| `cof status`    | Show the working tree status.                     |
| `cof branch`    | Create or list branches.                          |
| `cof checkout`  | Switch to a different branch.                     |
| `cof merge`     | Merge another branch into the current branch.     |
| `cof push`      | Push changes to a remote repository.              |
| `cof pull`      | Pull changes from a remote repository.            |
| `cof clone`     | Clone a remote repository.                        |
| `cof remote`    | Manage remote repositories.                       |
| `cof auth`      | Manage user authentication.                       |
| `cof server`    | Start the Cof server.                             |

## Remote Repositories

Cof includes a built-in server for hosting your repositories. You can start the server using the `server` command:

```bash
cof server --host 0.0.0.0 --port 7357
```

This will start a UDP server on the specified host and port. The server will serve repositories located within the directory where the `cof server` command was executed. For example, if you run `cof server` in `/home/user/my_repos/` and you have a cof repository at `/home/user/my_repos/project_A`, you can clone it using `cof://<server_ip>:<port>/project_A`.

You can then clone a repository from the server using the `clone` command:

```bash
cof clone cof://<server_ip>:<port>/<repository_path> <target_directory>
```

For example, to clone a repository named `my_repo` from a server running on `127.0.0.1:7357`:

```bash
cof clone cof://127.0.0.1:7357/my_repo my_cloned_repo
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on the project's GitHub repository.

## License

This project is licensed under the terms of the LICENSE file.
