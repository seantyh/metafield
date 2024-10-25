from typing import Tuple
from collections import defaultdict, Counter
from itertools import combinations
from git import Repo

CommitHash = str
FilePath = str


class CommitFriends:
  def __init__(self):
    self.commit_tables = defaultdict(list)
    self.file_tables = defaultdict(list)

  def add_pair(self, pair: Tuple[CommitHash, FilePath]):
    commit_hash, file_path = pair
    self.commit_tables[commit_hash].append(file_path)
    self.file_tables[file_path].append(commit_hash)

  def file_friends(self, file_part: str):
    friends = Counter()
    file_list = list(self.file_tables.keys())

    file_mine = None
    for file_x in file_list:
      if file_part in file_x:
        file_mine = file_x

    if file_mine is None:
      return friends
    
    for file_other in file_list:      
      if file_other == file_mine:
        continue
      commits_x = self.file_tables[file_mine]
      commits_y = self.file_tables[file_other]
      n_common = len(set(commits_x).intersection(commits_y))
      if n_common > 0:
        friends[file_other] = n_common
    
    
    return friends.most_common()
  
def find_friends(friend_part:str, repo_dir:str="."):
  repo = Repo(repo_dir)
  commits = list(repo.iter_commits())
  friends = CommitFriends()
  for commit_x in commits:  
    if len(commit_x.parents) != 1:
      # skip merge commits
      continue
    parent = commit_x.parents[0]
    diff_files = parent.diff(commit_x)
    for diff_x in diff_files:
      friends.add_pair((commit_x.hexsha, diff_x.b_path))
  
  return friends.file_friends(friend_part)