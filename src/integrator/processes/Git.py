import os
import requests
from requests.auth import HTTPBasicAuth
from bootstrap import TRAVIS_BUILD_DIR
from utils.Command import Command
from utils.Filesystem import chdir


class Git:
    """ The class handles the GIT processes """

    def __init__(self, token, owner, repo, folder):
        """ Git class constructor """
        self.__github_token = token
        self.__repo_owner = owner
        self.__repo_name = repo
        self.__repo_folder = folder

    def clone(self):
        """ Executes a git clone command on the target repository """
        chdir(TRAVIS_BUILD_DIR)

        # logging the working directory for debug
        print('----- Repo clone: -----')

        if os.path.isdir(self.__repo_folder) and os.path.isdir(os.path.join(self.__repo_folder, '.git')):
            print('Repository {repo_name} is already cloned'.format(repo_name=self.__repo_name) + '\n')
            return 0

        # Command to clone the repo
        cmd = 'git clone https://{owner}:{token}@github.com/{owner}/{repo}.git {repo_folder}'.format(
            owner=self.__repo_owner,
            token=self.__github_token,
            repo=self.__repo_name,
            repo_folder=self.__repo_folder
        )

        command = Command(cmd)
        command.run()

        if command.returned_errors():
            print('Error: ' + command.get_output())
            return 255

        print('Cloned repo {repo} to directory {dir}'.format(repo=self.__repo_name, dir=self.__repo_folder))
        return 0

    def branch(self):
        """ Returns the current branch """
        chdir(self.__repo_folder)

        command = Command(['git', 'branch'])
        command.run()

        chdir(TRAVIS_BUILD_DIR)  # Get back to previous directory

        output = command.get_output()
        lines = output.split('\n')
        for line in lines:
            if line.find('*') == 0:
                return line.lstrip('* ')

        return output

    def push(self, remote, branch, new=False):
        """ Executes a git push command of the given branch """
        chdir(self.__repo_folder)

        # logging the working directory for debug
        print('----- Branch push: -----')
        print('Branch name: ' + branch)

        # Command spec
        cmd = ['git', 'push', remote, branch]
        if new:
            cmd.insert(2, '-u')

        # Command to push to the repo
        command = Command(cmd)
        command.run()

        chdir(TRAVIS_BUILD_DIR)  # Get back to previous directory

        if command.returned_errors():
            print('Could not create a new branch {branch}: '.format(branch=branch) + command.get_output())
            return 255

        print('Branch {branch} has been pushed to {remote}'.format(remote=remote, branch=branch))
        return 0

    def checkout(self, branch, new=False):
        """ Executes a git checkout command of the given branch """
        chdir(self.__repo_folder)

        # logging the working directory for debug
        print('----- Branch checkout {new}: -----'.format(new='NEW' if new is True else ''))
        print('Branch name: ' + branch)

        # Command spec
        cmd = ['git', 'checkout', branch]
        if new:
            cmd.insert(2, '-b')

        # Command to checkout the repo
        command = Command(cmd)
        command.run()

        if command.returned_errors():
            if command.get_output().find('did not match any file(s) known to git') != -1:
                print('Branch does not exist. Trying to create it...\n')
                self.checkout(branch, True)  # Creating the branch
                self.push('origin', branch, True)  # Push to origin
            else:
                print('Unknown error occurred')
                print(command.get_output())
                return 255
        else:
            print(command.get_output())
            print('Working branch: {branch}'.format(branch=self.branch()) + '\n')

        chdir(TRAVIS_BUILD_DIR)  # Get back to previous directory

        return 0

    def stage_changes(self):
        """ Executes a git add command on the working branch """
        chdir(self.__repo_folder)

        # logging the working directory for debug
        print('----- Stage changes: -----')

        # Command to checkout the repo
        command = Command(['git', 'add', '--all'])
        command.run()

        chdir(TRAVIS_BUILD_DIR)  # Get back to previous directory

        if command.returned_errors():
            print('Could not stage changes: ' + command.get_output())
            return 255
        else:
            print('Staged all the changes')
            print(command.get_output())

        return 0

    def commit(self, message):
        """ Executes a git commit on the working branch """
        chdir(self.__repo_folder)

        # logging the working directory for debug
        print('----- Committing changes: -----')

        # Command to checkout the repo
        command = Command(['git', 'commit', '-m', message])
        command.run()

        chdir(TRAVIS_BUILD_DIR)  # Get back to previous directory

        if command.returned_errors():
            print('Could not commit changes: ' + command.get_output())
            return 255
        else:
            print('Commit OK')
            print(command.get_output())

        return 0

    def make_pull_request(self, base_branch, head_branch, title="Automated release"):
        """ The method creates a PR on the target repository """
        # logging the working directory for debug
        print('----- Creating a pull request: -----')

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Content-type": "application/json"
        }

        # Check if a PR is already present in the target branch
        response = requests.get(
            "https://api.github.com/repos/{owner}/{repo}/pulls".format(owner=self.__repo_owner, repo=self.__repo_name),
            auth=HTTPBasicAuth(self.__repo_owner, self.__github_token),
            headers=headers,
            data={"head": "{owner}:{head_branch}".format(owner=self.__repo_owner, head_branch=head_branch)}
        )

        if response.status_code != 200:
            print("Error response: " + response.content.decode("utf-8"))
            return response.status_code

        # Check if we have PR's open for the branch
        pull_requests = response.json()
        if len(pull_requests) > 0:
            for pr in pull_requests:
                if pr.get("title") == title:
                    print("Automated PR already exists")
                    return 0

        # Creating the pull request
        body = {
            "title": title,
            "body": "This release was done because the API spec may have changed",
            "head": "{owner}:{head_branch}".format(owner=self.__repo_owner, head_branch=head_branch),
            "base": base_branch
        }

        response = requests.post(
            "https://api.github.com/repos/{owner}/{repo}/pulls".format(owner=self.__repo_owner, repo=self.__repo_name),
            auth=HTTPBasicAuth(self.__repo_owner, self.__github_token),
            headers=headers,
            json=body
        )

        if response.status_code != 201:
            print("Error response: " + response.content.decode("utf-8"))
            return response.status_code

        print("Created the PR")
        return 0
