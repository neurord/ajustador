#!/bin/zsh

# Script to automatically generate documentation and commit this to the gh-pages
# branch.

# check, if index is empty
if ! git diff-index --cached --quiet --ignore-submodules HEAD ; then
  echo "Fatal: cannot work with indexed files!"
  exit 1
fi

if ! git rev-parse gh-pages &> /dev/null ; then
    echo "Fatal: no local branch 'gh-pages exists!'"
    exit 2
fi

if [ -z $(git config branch.gh-pages.remote) ] ; then
    echo "Fatal: 'gh-pages' does not have a remote branch!'"
    exit 3
fi

if [ $(git rev-parse gh-pages) != $(git rev-parse $(git config branch.gh-pages.remote)/gh-pages) ] ; then
    echo "Fatal: local branch 'gh-pages' and "\
                "remote branch '$(git config  branch.gh-pages.remote)' are out of sync!"
    exit 4
fi

# get the 'git describe' output
git_describe=$(git describe --always)

# # make the documentation, hope it doesn't fail
# echo "Generating doc from $git_describe"
# if ! mvn site ; then
#     echo "Fatal: 'make'ing the docs failed cannot commit!"
#     exit 5
# fi

docdirectory=$(git config gh-pages.dir)
if [ -z "$docdirectory" ]; then
    echo "Fatal: git config gh-pages.dir not found"
    exit 5
fi

# Add a .nojekyll file
# This prevents the GitHub jekyll website generator from running
touch $docdirectory/.nojekyll

# Adding the doc files to the index
git add -f $docdirectory

# writing a tree using the current index
tree=$(git write-tree --prefix=$docdirectory)

# we’ll have a commit
commit=$(echo "site generated from $git_describe" | git commit-tree $tree -p gh-pages)

# move the branch to the commit we made, i.e. one up
git update-ref refs/heads/gh-pages $commit

# clean index
git reset HEAD

# try to checkout what we’ve done – does not matter much, if it fails
# it is purely informative
#git checkout gh-pages

# print the commit message
git log -1 --oneline gh-pages
