package shared_test

import (
	"testing"
	"time"

	"hansard-tales/data-processing/go-functions/shared"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestValidateMP(t *testing.T) {
	tests := []struct {
		name    string
		mp      shared.MP
		wantErr bool
	}{
		{
			name: "valid MP",
			mp: shared.MP{
				ID:           "mp001",
				Name:         "Hon. John Mbadi",
				Constituency: "Suba South",
				Party:        "ODM",
			},
			wantErr: false,
		},
		{
			name: "empty name",
			mp: shared.MP{
				ID:           "mp002",
				Name:         "",
				Constituency: "Test Constituency",
				Party:        "Test Party",
			},
			wantErr: true,
		},
		{
			name: "empty constituency",
			mp: shared.MP{
				ID:           "mp003",
				Name:         "Test MP",
				Constituency: "",
				Party:        "Test Party",
			},
			wantErr: true,
		},
		{
			name: "empty party",
			mp: shared.MP{
				ID:           "mp004",
				Name:         "Test MP",
				Constituency: "Test Constituency",
				Party:        "",
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := shared.ValidateMP(tt.mp)
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestNormalizeMPName(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "remove Hon. prefix",
			input:    "Hon. John Mbadi",
			expected: "John Mbadi",
		},
		{
			name:     "remove Dr prefix",
			input:    "Hon. (Dr) James Opiyo",
			expected: "James Opiyo",
		},
		{
			name:     "normalize spacing",
			input:    "John    Mbadi   Ng'ongo",
			expected: "John Mbadi Ng'ongo",
		},
		{
			name:     "trim whitespace",
			input:    "  John Mbadi  ",
			expected: "John Mbadi",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := shared.NormalizeMPName(tt.input)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestCalculatePerformanceScore(t *testing.T) {
	tests := []struct {
		name           string
		attendanceRate float64
		billsSponsored float64
		qualityScore   float64
		expected       float64
	}{
		{
			name:           "perfect scores",
			attendanceRate: 100,
			billsSponsored: 100,
			qualityScore:   100,
			expected:       100,
		},
		{
			name:           "mixed scores",
			attendanceRate: 80,
			billsSponsored: 60,
			qualityScore:   90,
			expected:       76, // (80*0.4 + 60*0.3 + 90*0.3)
		},
		{
			name:           "zero scores",
			attendanceRate: 0,
			billsSponsored: 0,
			qualityScore:   0,
			expected:       0,
		},
		{
			name:           "capped at 100",
			attendanceRate: 150,
			billsSponsored: 150,
			qualityScore:   150,
			expected:       100,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := shared.CalculatePerformanceScore(tt.attendanceRate, tt.billsSponsored, tt.qualityScore)
			assert.InDelta(t, tt.expected, result, 0.1) // Allow small floating point differences
		})
	}
}

func TestExtractDateFromText(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		wantErr  bool
		expected string
	}{
		{
			name:     "ISO date format",
			input:    "Hansard Report 2025-12-04",
			wantErr:  false,
			expected: "2025-12-04",
		},
		{
			name:    "no date found",
			input:   "Random text without date",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := shared.ExtractDateFromText(tt.input)
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				require.NoError(t, err)
				assert.Equal(t, tt.expected, result.Format("2006-01-02"))
			}
		})
	}
}

func TestHansardSessionStructure(t *testing.T) {
	// Test that HansardSession struct can be created and used
	session := shared.HansardSession{
		ID:         "session001",
		Date:       time.Now(),
		Title:      "Test Session",
		PDFURL:     "https://example.com/test.pdf",
		YouTubeURL: "https://youtube.com/watch?v=test",
	}

	assert.NotEmpty(t, session.ID)
	assert.NotEmpty(t, session.Title)
	assert.NotEmpty(t, session.PDFURL)
	assert.NotEmpty(t, session.YouTubeURL)
	assert.False(t, session.Date.IsZero())
}

func BenchmarkCalculatePerformanceScore(b *testing.B) {
	for i := 0; i < b.N; i++ {
		shared.CalculatePerformanceScore(85.5, 67.2, 78.9)
	}
}

func BenchmarkNormalizeMPName(b *testing.B) {
	for i := 0; i < b.N; i++ {
		shared.NormalizeMPName("Hon. (Dr) James Opiyo Wandayi")
	}
}
