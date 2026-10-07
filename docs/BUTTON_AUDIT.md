# Web Intelligence — Button Audit

_Every view branch: button label → handler → API calls → status. 0 dead buttons (enforced by test_frontend_audit)._

| Page | Button | Handler | API | Result | Status |
|---|---|---|---|---|---|
| `#projects` | + Add project | `projectAdd()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#projects` | Export CSV | `csvProjects()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#projects` | Open | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#projects` | Edit | `projectEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#projects` | Delete | `projectDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#project` | Open | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#project` | Edit | `projectEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#targets` | + Add target | `targetAdd()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#targets` | Delete selected | `targetBulkDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#targets` | Export CSV | `csvTargets()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#targets` | Open | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#targets` | Test | `testTarget()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#targets` | Scan now | `targetScan()` | 2 endpoint(s) | toast/reload/modal | OK |
| `#targets` | Edit | `targetEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#targets` | (icon) | `tgtCheckAll()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#target` | Scan now | `targetScan()` | 2 endpoint(s) | toast/reload/modal | OK |
| `#target` | Test connection | `testTarget()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#target` | Add to watchlist | `targetToWatchlist()` | 2 endpoint(s) | toast/reload/modal | OK |
| `#target` | Schedule scan | `targetToSchedule()` | 2 endpoint(s) | toast/reload/modal | OK |
| `#target` | Edit | `targetEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#target` | Risk score | `targetRisk()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#target` | Open | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#connectors` | + Add connector | `connAdd()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#connectors` | Test | `connTest()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#connectors` | Execute | `connExec()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#connectors` | ${r.enabled?'Disable':'Enable'} | `connToggle()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#connectors` | Edit | `connEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#connectors` | Delete | `connDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#jobs` | + New scan | `jobAdd()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#jobs` | Export CSV | `csvJobs()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#jobs` | Open | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#jobs` | Run | `runJob()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#jobs` | Retry | `jobRetry()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#jobs` | Cancel | `jobCancel()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#jobs` | Delete | `jobDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#job` | Run | `runJob()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#job` | Retry | `jobRetry()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#job` | Cancel | `jobCancel()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#schedules` | Run scheduler now | `tick()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#schedules` | + Add schedule | `schedAdd()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#schedules` | Run now | `schedRun()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#schedules` | ${r.status==='active'?'Disable':'Enable' | `schedToggle()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#schedules` | Edit | `schedEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#schedules` | Delete | `schedDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#documents` | Delete | `docDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#prices` | Export CSV | `csvPrices()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#articles` | Delete | `articleDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#entities` | Open | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#entity` | Open Investigation | `entInvestigate()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#entity` | Add to Watchlist | `entWatch()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#entity` | Explore Graph | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#entity` | Risk score | `entRisk()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#entity` | Resolve / Merge… | `entMerge()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#entity` | Add alias… | `entAlias()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#graph` | Render | `svg()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#graph` | Export JSON | `graphExport()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#evidence` | Verify | `evVerify()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#findings` | Confirm selected | `fndBulk()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#findings` | Open | `openFinding()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#findings` | Triage | `fndEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#findings` | Delete | `fndDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#findings` | (icon) | `fndCheckAll()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#finding` | Confirm | `findingStatus()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#finding` | Triage… | `fndEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#finding` | Summarize | `aiAssist()` | 2 endpoint(s) | toast/reload/modal | OK |
| `#feed` | All | `window()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#feed` | Subscribe… | `feedSubAdd()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#runs` | Analyze | `runAnalyze()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#runs` | Finish | `runFinish()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#runs` | Export | `runExport()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#reports` | View | `viewReport()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#reports` | .${f} | `reportExport()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#reports` | STIX | `stixExport()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#reports` | MISP | `mispExport()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#reports` | Regenerate | `reportRegen()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#reports` | Delete | `reportDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#watchlists` | Evaluate | `evalWl()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#watchlists` | Edit | `wlEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#watchlists` | Delete | `wlDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#alerts` | + New alert | `alertAdd()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#alerts` | Ack selected | `alertBulk()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#alerts` | Export CSV | `csvAlerts()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#alerts` | Open | `alertOpen()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#alerts` | Ack | `alertAck()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#alerts` | Resolve | `alertResolve()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#alerts` | Send | `sendAlert()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#alerts` | (icon) | `alCheckAll()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#alert` | Acknowledge | `alertAck()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#alert` | Resolve… | `alertResolve()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#alert` | Send now | `sendAlert()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#workflows` | + New workflow | `wfAdd()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#workflows` | Open | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#workflows` | Run | `runWf()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#workflows` | Retry | `wfRetry()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#workflows` | ${r.enabled?'Disable':'Enable'} | `wfToggle()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#workflows` | Duplicate | `wfDup()` | 2 endpoint(s) | toast/reload/modal | OK |
| `#workflows` | Delete | `wfDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#workflow` | Run | `runWf()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#workflow` | ${d.enabled?'Disable':'Enable'} | `wfToggle()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#workflow` | Edit | `wfEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#workflow` | Cancel | `wfCancel()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#webhooks` | + Add webhook | `whAdd()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#webhooks` | Open | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#webhooks` | Test | `testWh()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#webhooks` | ${r.enabled?'Disable':'Enable'} | `whToggle()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#webhooks` | Edit | `whEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#webhooks` | Delete | `whDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#webhook` | Test | `testWh()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#webhook` | Edit | `whEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#webhook` | Replay | `whReplay()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#datasets` | Open | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#datasets` | Import | `dsImport()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#datasets` | Publish | `dsPublish()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#datasets` | Export | `dsExport()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#datasets` | Edit | `dsEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#datasets` | Delete | `dsDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#dataset` | Rollback | `dsRollback()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#health` | Run system doctor | `sysDoctor()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#health` | Export diagnostics | `diagExport()` | 2 endpoint(s) | toast/reload/modal | OK |
| `#search` | Export | `searchExport()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#orgs` | Branding | `orgBrand()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#users` | Change role… | `memberRole()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#users` | Disable login | `userToggle()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#users` | Reset password | `userReset()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#users` | Remove | `memberDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#users` | + New role | `roleAdd()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#users` | Edit | `roleEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#users` | Delete | `roleDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#apikeys` | Revoke | `keyRevoke()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#external-apis` | Revoke | `keyRevoke()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#security-tools` | Test connection | `bdTest()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#security-tools` | Details | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#investigations` | + New investigation | `invAdd()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#investigations` | Open | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#investigations` | Edit | `invEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#investigations` | Delete | `invDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#investigation` | Edit | `invEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#investigation` | Add member | `invMember()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#investigation` | Open | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#investigation` | Link entities… | `invLink()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#investigation` | Open | `openFinding()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#investigation` | Start Collection | `invCollect()` | 3 endpoint(s) | toast/reload/modal | OK |
| `#investigation` | Toggle | `invTaskToggle()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#investigation` | Refresh | `load()` | 55 endpoint(s) | toast/reload/modal | OK |
| `#investigation` | Create Case | `invToCase()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#investigation` | Generate Report | `window()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#cases` | + New case | `caseAdd()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#cases` | Open | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#cases` | Edit | `caseEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#cases` | Delete | `caseDel()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#case` | Edit | `caseEdit()` | 1 endpoint(s) | toast/reload/modal | OK |
| `#case` | Open | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#case` | Link entities… | `caseLink()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#case` | Open | `openFinding()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#case` | Toggle | `caseTaskToggle()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#timeline` | Apply | `window()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#attack` | Investigate | `go()` | 0 endpoint(s) | toast/reload/modal | OK |
| `#attack` | Cancel | `closeModal()` | 0 endpoint(s) | toast/reload/modal | OK |