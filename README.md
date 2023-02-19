# Repo fiding tool
This tool finds repositories using github API based on given query and conditions and returns direct URLs to them. 

Currently using custom blacklist.
Usage:
```bash
python3 find_repos.py -q "stars:500..5000 language:Java created:>2017-10-11 sort:updated" -f /tmp/results.txt -s 10000
```

`-q/--query` - search query

`-f/--filename` - path and filename where results will be stored

`-s/--size` - filter repos bigger than given size in bytes
