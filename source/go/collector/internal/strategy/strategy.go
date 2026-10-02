package strategy

// Decide returns the ordered escalation plan. Mirrors Python decision engine.
func Decide(hasAPI, needsJS, rateLimited, blocked, geo bool, allowBrowser, allowProxy, allowBright, brightConfigured bool, history map[string]int) []string {
 plan := []string{}
 if hasAPI {
  plan = append(plan, "OFFICIAL_API")
 } else {
  plan = append(plan, "DIRECT_HTTP")
 }
 if (needsJS) && allowBrowser {
  plan = append(plan, "BROWSER")
 }
 if (rateLimited || blocked) && allowProxy {
  plan = append(plan, "OWN_PROXY")
  if allowBright && brightConfigured {
   plan = append(plan, "BRIGHT_DATA")
  }
 }
 if geo && allowProxy && !contains(plan, "OWN_PROXY") {
  plan = append(plan, "OWN_PROXY")
 }
 best, bestN := "", 0
 for k, v := range history {
  if v > bestN {
   best, bestN = k, v
  }
 }
 if best != "" && !contains(plan, best) {
  plan = append(plan, best)
 }
 return plan
}

func contains(s []string, v string) bool {
 for _, x := range s {
  if x == v {
   return true
  }
 }
 return false
}

// Validate: HTTP 200 is not auto-success.
func Validate(httpStatus int, contentType string, size int, parsedOK bool, completeness float64) (bool, map[string]string) {
 d := map[string]string{}
 if httpStatus != 200 {
  d["http"] = "non-200"
 }
 if size <= 0 {
  d["empty"] = "true"
 }
 if parsedOK == false {
  d["parse"] = "failed"
 }
 if completeness < 0.5 {
  d["incomplete"] = "true"
 }
 return len(d) == 0, d
}
