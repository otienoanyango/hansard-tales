package shared

import (
	"fmt"
	"regexp"
	"strings"
	"time"
)

// MP represents a Member of Parliament
type MP struct {
	ID           string `json:"id"`
	Name         string `json:"name"`
	Constituency string `json:"constituency"`
	Party        string `json:"party"`
}

// HansardSession represents a parliamentary session
type HansardSession struct {
	ID          string    `json:"id"`
	Date        time.Time `json:"date"`
	Title       string    `json:"title"`
	PDFURL      string    `json:"pdf_url"`
	YouTubeURL  string    `json:"youtube_url,omitempty"`
	ProcessedAt time.Time `json:"processed_at,omitempty"`
}

// ValidateMP validates MP data
func ValidateMP(mp MP) error {
	if mp.Name == "" {
		return fmt.Errorf("MP name cannot be empty")
	}
	if mp.Constituency == "" {
		return fmt.Errorf("MP constituency cannot be empty")
	}
	if mp.Party == "" {
		return fmt.Errorf("MP party cannot be empty")
	}
	return nil
}

// ExtractDateFromText extracts date from Hansard text using common patterns
func ExtractDateFromText(text string) (time.Time, error) {
	// Common date patterns in Hansard titles
	patterns := []string{
		`(\d{1,2})\w{0,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})`,
		`(\d{4})-(\d{1,2})-(\d{1,2})`,
		`(\d{1,2})/(\d{1,2})/(\d{4})`,
	}

	for _, pattern := range patterns {
		re := regexp.MustCompile(pattern)
		matches := re.FindStringSubmatch(text)
		if len(matches) > 0 {
			// Try to parse the date - this is simplified, real implementation would be more robust
			if strings.Contains(matches[0], "-") {
				return time.Parse("2006-01-02", matches[0])
			}
		}
	}

	return time.Time{}, fmt.Errorf("no date found in text: %s", text)
}

// NormalizeMPName normalizes MP names for consistent matching
func NormalizeMPName(name string) string {
	// Remove common prefixes and normalize spacing
	name = strings.TrimSpace(name)
	name = strings.ReplaceAll(name, "Hon. ", "")
	name = strings.ReplaceAll(name, "(Dr) ", "")
	name = strings.ReplaceAll(name, "(Eng) ", "")
	name = regexp.MustCompile(`\s+`).ReplaceAllString(name, " ")
	return name
}

// CalculatePerformanceScore calculates a basic performance score for MP
func CalculatePerformanceScore(attendanceRate, billsSponsored, qualityScore float64) float64 {
	// Weighted average: 40% attendance, 30% bills, 30% quality
	score := (attendanceRate*0.4 + billsSponsored*0.3 + qualityScore*0.3)
	if score > 100 {
		return 100
	}
	if score < 0 {
		return 0
	}
	return score
}
