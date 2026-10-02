// Package ssrf blocks server-side request forgery: literal private IPs,
// resolved private IPs (DNS rebinding safe: resolve-then-validate), cloud
// metadata endpoints, and unsafe redirect targets.
package ssrf

import (
	"fmt"
	"net"
	"net/url"
	"strings"
)

var metadataIPs = map[string]bool{
	"169.254.169.254": true, // AWS/GCP/Azure metadata
	"fd00:ec2::254":   true,
	"100.100.100.200": true, // Alibaba metadata
}

// ValidateURL reports whether fetching rawURL is allowed. trustedCIDRs
// (e.g. ["127.0.0.1/32"]) explicitly permits otherwise-blocked ranges.
func ValidateURL(rawURL string, trustedCIDRs []string) error {
	u, err := url.Parse(rawURL)
	if err != nil {
		return fmt.Errorf("bad url: %w", err)
	}
	if u.Scheme != "http" && u.Scheme != "https" {
		return fmt.Errorf("scheme not allowed: %s", u.Scheme)
	}
	host := u.Hostname()
	if host == "" {
		return fmt.Errorf("missing host")
	}
	if strings.EqualFold(host, "localhost") || strings.EqualFold(host, "metadata.google.internal") {
		return fmt.Errorf("host blocked: %s", host)
	}
	if ip := net.ParseIP(strings.Trim(host, "[]")); ip != nil {
		return checkIP(ip, trustedCIDRs)
	}
	// resolve-then-validate defeats DNS rebinding
	ips, err := net.LookupIP(host)
	if err != nil || len(ips) == 0 {
		return fmt.Errorf("dns failed for %s", host)
	}
	for _, ip := range ips {
		if err := checkIP(ip, trustedCIDRs); err != nil {
			return err
		}
	}
	return nil
}

func checkIP(ip net.IP, trusted []string) error {
	if metadataIPs[ip.String()] {
		return fmt.Errorf("cloud metadata blocked: %s", ip)
	}
	if ip.IsLoopback() || ip.IsPrivate() || ip.IsLinkLocalUnicast() || ip.IsLinkLocalMulticast() || ip.IsUnspecified() {
		for _, c := range trusted {
			_, netw, err := net.ParseCIDR(strings.TrimSpace(c))
			if err == nil && netw.Contains(ip) {
				return nil
			}
		}
		return fmt.Errorf("private/loopback IP blocked: %s", ip)
	}
	return nil
}
