import argparse
import hashlib
import os

import requests
import yaml


class LatestReleaseNotFoundException(Exception):
    pass


class ChecksumNotMatchingException(Exception):
    pass


class GithubDownload:
    def __init__(self, orga, repo, arch='linux-amd64', path='.'):
        self.repo = repo
        self.orga = orga
        self.arch = arch
        self.path = path
    
    @staticmethod
    def load_config(self, path='config.yml'):
        with open(path, 'r') as f:
            return yaml.safe_load(f)['config']

    def get_checksum(self, url):
        for cs in requests.get(url).text.split('\n'):
            if self.arch in cs:
                return cs.split()[0]

    def download_latest_release(self):
        path = '.'
        r = requests.get(f"https://api.github.com/repos/{self.orga}/{self.repo}/releases/latest")
        r.raise_for_status()
        for package in r.json()['assets']:
            if self.arch in package['browser_download_url']:
                download_url = package['browser_download_url']
            elif 'sha256sums' in package['browser_download_url']:
                checksum_url = package['browser_download_url']
        if not download_url:
            raise LatestReleaseNotFoundException
        filename = download_url.split('/')[-1]
        # TODO: check ob file schon im Filesystem exisitiert - passt das mit den Endungen? 
        if os.path.isfile(f'{path}/{filename}'):
            return
        file_checksum = hashlib.sha256()
        download = requests.get(download_url)
        file_checksum.update(download.content)
        if self.get_checksum(checksum_url) != file_checksum.hexdigest():
            raise ChecksumNotMatchingException
        with open(f'{path}/{filename}', 'wb') as f:
            f.write(download.content)

def main():
    download = GithubDownload(args.orga, args.repo, args.arch, args.path)
    download.download_latest_release()


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description='Download latest Release of a github project repo')
        parser.add_argument('--orga', help='Github-Organization', required=True)
        parser.add_argument('--repo', help='Repository inside organization', required=True)
        parser.add_argument('--arch', help='Package-Architecture to download', default='linux-amd64')
        parser.add_argument('--path', help='Destination directory of downloaded package')
        args = parser.parse_args()
        main()
    except Exception as e:
        print(f'uncaught exception{e}')
