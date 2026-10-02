package parser

import "strings"

// Minimal metadata parser: content-type gate + expected-field presence.
func Check(contentType string, body []byte, expected []string) (bool, float64) {
 ct := strings.ToLower(contentType)
 okType := ct == "" || strings.Contains(ct, "html") || strings.Contains(ct, "json") || strings.Contains(ct, "xml") || strings.Contains(ct, "text")
 if !okType || len(body) == 0 {
  return false, 0
 }
 if len(expected) == 0 {
  return true, 1.0
 }
 low := strings.ToLower(string(body))
 hit := 0
 for _, f := range expected {
  if strings.Contains(low, strings.ToLower(f)) {
   hit++
  }
 }
 return hit > 0, float64(hit) / float64(len(expected))
}
