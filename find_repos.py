import requests
import re
import json
import sys
from os import environ,path
from time import sleep
from argparse import ArgumentParser, RawTextHelpFormatter


try: 
    ACCESS_TOKEN = environ["GITHUB_ACCESS_TOKEN"]
except KeyError:
    print("No GITHUB_ACCESS_TOKEN environment variable.")
    sys.exit(1)

BASE_URL = "https://api.github.com/search"

def get_args(prog):
    helpm = f"Example: \r\n{prog} -q \"NOT in:descritpion library NOT in:readme exercise stars:500..5000 language:Java -f java_repos_semgrep.txt -s 10000\""
    parser = ArgumentParser(epilog=helpm, formatter_class=RawTextHelpFormatter)
    parser.add_argument('-q','--query',dest="searchQuery",action='store',type=str,required=True)
    parser.add_argument('-f','--filename',dest="storedFile",action='store',type=str,required=False)
    parser.add_argument('-s','--size',dest="sizeOfRepo",action='store',type=int,required=True)
    parser.add_argument('-d', '--docker', dest='hasDockerfile', action='store_const', const=True, default=False)
    return parser.parse_args()

def final(repoList):
    finalList = list(set(repoList))
    finalList.sort()
    if args.storedFile:
        if path.exists(f"{args.storedFile}"):
            with open(f"{args.storedFile}","a") as file:
                file.write('\n'.join(finalList))
        else: 
            with open(f"{args.storedFile}","w") as file :
                file.write('\n'.join(finalList))
    else:
        [print(i) for i in finalList]
    
    print(f'''
    Query used: {args.searchQuery}
    \r\nFiltering repos with size over {args.sizeOfRepo}
    Found {len(finalList)} repositories.
    Results saved to {args.storedFile}.
    ''')


if __name__ == "__main__":
    args = get_args(sys.argv[0])

    headers = {
        "Accept" : "application/vnd.github+json",
        "Authorization" : f"Bearer {ACCESS_TOKEN}",
        "X-GitHub-Api-Version":"2022-11-28"
        }

    s = requests.Session()

    query = args.searchQuery.replace("#","%23")
    r = s.get(f"{BASE_URL}/repositories?q={query}&page=1&per_page=100",headers=headers)
    
    data = json.loads(r.text)

    totalNumberOfRepos = data['total_count']
    print(f"The amount of repos based on the given query: {totalNumberOfRepos}")

    # Only the first 1000 search results are available
    if totalNumberOfRepos < 101:
        totalNumberOfPages = 1
    else:
        totalNumberOfPages = totalNumberOfRepos / 100
        totalNumberOfPages = round(totalNumberOfPages)
    

    print(f'''
    Github API provides only up to 1000 results for each search,
    to work around it split your query into small queries which will return less than 1000 results.
    The number of pages: {totalNumberOfPages}, picking only updated top 1000 results.
    ''')
    
    totalNumberOfRelevantPages = round(0.7 * totalNumberOfPages) if totalNumberOfPages <= 10 else 10
    print(f"Looping {totalNumberOfRelevantPages} time/s:")

    repoCounter = 0
    repoList = []
    reposCheckDocker = []
    #custom blacklist
    unwantedDescriptionKeywords = ["bootcamp", "bootcamps", "beginner", "beginners", "exercise" , "exercises" , "labs" , "course", "shellcode", "payload", "wrapper","installer","hacking","hacker","c2","multiplayer","player","minecraft"]
    unwantedRepoOwnerName = ["microsoft","dotnet","azure","tutorial","firefox","chrome","google","hacking","hacker","c2","multiplayer","player","minecraft","metamask","duckduckgo","owasp"]

    for page in range(0,totalNumberOfRelevantPages,1):
        r = s.get(f"{BASE_URL}/repositories?q={query}&page={page}",headers=headers)
        data = json.loads(r.text)
        for item in data['items']:
            repoDescription = item['description']
            repoLogin = item['html_url']
            if (item['size'] > args.sizeOfRepo):
                if not any(string in str(repoDescription).lower() for string in unwantedDescriptionKeywords):
                    if not any(string in str(repoLogin).lower() for string in unwantedRepoOwnerName):
                        repoCounter += 1
                        repoList.append(item['html_url'])

                        #Store results in case of docker arg set to true
                        reposCheckDocker.append(item['url'])
                        

        sleep(3) # sleep in case of rate limit

    #saving repos that only have docker/Dockerfile
    #regex to grab url of repo only from /contents/ API request
    getUrl = r'(https?://github\.com/[^\s/]+/[^\s/]+)'
    if args.hasDockerfile:
        listOfDockerRepos = []
        for i in reposCheckDocker:
            sleep(1)
            r = s.get(f"{i}/contents/",headers=headers)
            data = json.loads(r.text)
            for item in data:
                if "docker" in item["name"].lower():
                    listOfDockerRepos.append(re.search(getUrl,item["html_url"]).group(1))
            

        
        final(listOfDockerRepos)

    else:
        final(repoList)
        
