package storage

import (
 "os"
 "path/filepath"
)

// Save raw body under data/raw/<hash>. Returns path.
func Save(root string, hash string, body []byte) (string, error) {
 if err := os.MkdirAll(root, 0o755); err != nil {
  return "", err
 }
 p := filepath.Join(root, hash)
 if err := os.WriteFile(p, body, 0o644); err != nil {
  return "", err
 }
 return p, nil
}
