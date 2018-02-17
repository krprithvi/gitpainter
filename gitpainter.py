import os
import sys


from git import Repo
from git import InvalidGitRepositoryError, NoSuchPathError
import datetime
import json


class GitPainter():
    def __init__(self, path="./", patterns="./patterns.json", file=None):
        # Readying the repository
        self.repo = None
        try: self.repo = Repo(path)
        except (InvalidGitRepositoryError, NoSuchPathError):
            self.repo = Repo.init(os.path.join(path, ".git"), mkdir=True, bare=True)
            with self.repo.config_writer() as cw:
                cw.set_value("core", "bare", False)
            self.repo.close()
            self.repo = Repo(path)
        except Exception as e:
            print(e.with_traceback())
            sys.exit(0)
        self.index = self.repo.index


        # Loading patterns
        try:
            self.patterns = json.load(open(patterns))
        except FileNotFoundError as f:
            print(f)
            print("Please provide a json file for the patterns")
            sys.exit(0)

        # Getting the file name
        self.file = file
        if self.file is None:
            self.file = "{}.txt".format(datetime.datetime.today().microsecond)
            if (os.path.isfile(os.path.join(path, self.file))):
                print("File already exists")
                sys.exit(0)
        self.filePath = os.path.join(path, self.file)

    def findFirstSunday(self, month, year):
        first_day = datetime.datetime(day=1, month=month, year=year)
        return first_day + datetime.timedelta(days = 6 - first_day.weekday())


    def getAllDatesForPattern(self, start_day, pattern):
        dates = []
        for w in range(len(pattern)):
            for d in range(7):
                if pattern[w][d]:
                    commit_day = start_day + datetime.timedelta(days=(w*7)+d)
                    commit_day_string = commit_day.strftime("%a, %d %b %Y %H:%M:%S")
                    dates.append(commit_day_string)
        return dates

    def writeCharacterInCommitsForASpecificMonth(self, character, month, year):
        start_date = self.findFirstSunday(month, year)
        self.writeCharacterInCommitsFromSpecificDate(character, start_date)

    def writeCharacterInCommitsFromSpecificDate(self, character, start_date):
        pattern = self.getPatternFromCharacter(character)
        commit_dates = self.getAllDatesForPattern(start_date, pattern)

        with open(self.filePath, 'w') as fp:
            fp.flush()
            for date in commit_dates:
                self.index.add([self.file])  # add a new file to the index
                self.index.commit(date, author_date=date, commit_date=date)

    def getPatternFromCharacter(self, character):
        try:
            return self.patterns[character]
        except Exception as e:
            print("Add the pattern {} to the patterns file".format(character))
            sys.exit(0)

    def writeSentence(self, sentence, month, year):
        commit_date = self.findFirstSunday(month, year)
        for c in sentence:
            self.writeCharacterInCommitsFromSpecificDate(c, commit_date)
            commit_date += datetime.timedelta(days=7*(len(self.getPatternFromCharacter(c))+1))

    def closeRepo(self):
        self.repo.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("Create a file with n commits")

    parser.add_argument("--path", "-f", action="store", required=False, default="./")
    parser.add_argument("--sentence", "-s", type=str, action="store", required=True)
    parser.add_argument("--month", "-m", type=int, action="store", required=True)
    parser.add_argument("--year", "-y", type=int, action="store", required=True)

    args = parser.parse_args()

    gp = GitPainter(args.path)
    gp.writeSentence(args.sentence, args.month, args.year)
    gp.closeRepo()
