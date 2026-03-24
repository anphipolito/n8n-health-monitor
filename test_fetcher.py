from fetcher import fetch_workflows
wf = fetch_workflows("file", path="./workflows")
print(len(wf), 'workflows loaded')                                        
print(wf[0])  