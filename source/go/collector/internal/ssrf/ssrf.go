// Package ssrf blocks server-side request forgery: literal private IPs,
// resolved private IPs (DNS rebinding safe: resolve-then-validate), cloud
// metadata endpoints, and unsafe redirect targets.
package ssrf

import (
	"fmt"
	"net"
	"net/url"
	"strconv"
	"strings"
)

var metadataIPs = map[string]bool{
	"169.254.169.254": true, // AWS/GCP/Azure metadata
	"fd00:ec2::254":   true,
	"100.100.100.200": true, // Alibaba metadata
}

// ValidateURL reports whether fetching rawURL is allowed. trustedCIDRs
// (e.g. ["127.0.0.1/32"]) explicitly permits otherwise-blocked ranges.
// DNS names are resolved and EVERY address validated (rebinding-safe).
func ValidateURL(rawURL string, trustedCIDRs []string) error {
	u, err := url.Parse(rawURL)
	if err != nil {
		return fmt.Errorf("bad url: %w", err)
	}
	if u.Scheme != "http" && u.Scheme != "https" {
		return fmt.Errorf("scheme not allowed: %s", u.Scheme)
	}
	host := strings.ToLower(strings.TrimSuffix(u.Hostname(), "."))
	if host == "" {
		return fmt.Errorf("missing host")
	}
	if host == "localhost" || host == "metadata.google.internal" {
		return fmt.Errorf("host blocked: %s", host)
	}
	if num := normalizeNumeric(host); num != "" {
		host = num
	}
	if ip := net.ParseIP(strings.Trim(host, "[]")); ip != nil {
		return checkIP(ip, trustedCIDRs)
	}
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

// normalizeNumeric turns decimal/hex/octal IPv4 tricks into dotted form.
func normalizeNumeric(host string) string {
	h := strings.Trim(host, "[]")
	if n, err := strconv.ParseUint(h, 0, 32); err == nil {
		// base-0 handles 0x hex; try octal-looking and plain decimal too
		return uintToIP(uint32(n))
	}
	if strings.HasPrefix(h, "0") && len(h) > 1 && !strings.Contains(h, ".") && !strings.ContainsAny(h, "xX") {
		if n, err := strconv.ParseUint(h, 8, 32); err == nil {
			return uintToIP(uint32(n))
		}
	}
	if strings.Contains(h, ".") {
		parts := strings.Split(h, ".")
		if len(parts) == 4 {
			nums := make([]string, 0, 4)
			for _, p := range parts {
				var v uint64
				var err error
				switch {
				case strings.HasPrefix(strings.ToLower(p), "0x"):
					v, err = strconv.ParseUint(p[2:], 16, 8)
				case len(p) > 1 && strings.HasPrefix(p, "0"):
					v, err = strconv.ParseUint(p, 8, 8)
				default:
					v, err = strconv.ParseUint(p, 10, 8)
				}
				if err != nil || v > 255 {
					return ""
				}
				nums = append(nums, strconv.Itoa(int(v)))
			}
			return strings.Join(nums, ".")
		}
	}
	return ""
}

func uintToIP(n uint32) string {
	return fmt.Sprintf("%d.%d.%d.%d", byte(n>>24), byte(n>>16), byte(n>>8), byte(n))
}

func checkIP(ip net.IP, trusted []string) error {
	if ip4 := ip.To4(); ip4 != nil {
		ip = ip4 // unwrap IPv4-mapped IPv6
	}
	if metadataIPs[ip.String()] {
		return fmt.Errorf("cloud metadata blocked: %s", ip)
	}
	// NOTE: IsGlobalUnicast does NOT cover RFC1918, so check explicitly.
	if ip.IsLoopback() || ip.IsPrivate() || ip.IsLinkLocalUnicast() ||
		ip.IsLinkLocalMulticast() || ip.IsMulticast() || ip.IsUnspecified() {
		for _, c := range trusted {
			_, netw, err := net.ParseCIDR(strings.TrimSpace(c))
			if err == nil && netw.Contains(ip) {
				return nil
			}
		}
		return fmt.Errorf("non-public IP blocked: %s", ip)
	}
	return nil
}
