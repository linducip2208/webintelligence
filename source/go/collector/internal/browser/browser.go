// Package browser dispatches render jobs back to the Python browser worker via Redis.
package browser

// Dispatch returns a marker result payload requesting Python-side rendering.
func Dispatch(jobID, url string) map[string]string {
	return map[string]string{"job_id": jobID, "strategy": "BROWSER", "url": url, "handler": "python-browser-worker"}
}
