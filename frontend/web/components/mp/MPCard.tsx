import React from 'react';

export interface MP {
    id: string;
    name: string;
    constituency: string;
    party: string;
    performanceScore?: number;
}

interface MPCardProps {
    mp: MP;
    onSelect?: (mp: MP) => void;
    showPerformanceScore?: boolean;
}

export function MPCard({
    mp,
    onSelect,
    showPerformanceScore = true
}: MPCardProps) {
    const handleClick = () => {
        onSelect?.(mp);
    };

    const getPartyColor = (party: string): string => {
        const colors: Record<string, string> = {
            'UDA': '#FF6B35',
            'ODM': '#4A90E2',
            'JUBILEE': '#FFD23F',
            'WIPER': '#50C878',
        };
        return colors[party.toUpperCase()] || '#6B7280';
    };

    const getScoreColor = (score?: number): string => {
        if (!score) return 'gray';
        if (score >= 80) return 'green';
        if (score >= 60) return 'yellow';
        return 'red';
    };

    return (
        <div
            className="mp-card border border-gray-200 rounded-lg p-4 hover:shadow-md cursor-pointer transition-shadow"
            data-testid={`mp-card-${mp.id}`}
            onClick={handleClick}
        >
            <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-lg text-gray-900" data-testid="mp-name">
                    {mp.name}
                </h3>
                {showPerformanceScore && mp.performanceScore && (
                    <span
                        className={`performance-score px-2 py-1 rounded text-sm font-medium text-${getScoreColor(mp.performanceScore)}-600`}
                        data-testid="performance-score"
                    >
                        {mp.performanceScore}/100
                    </span>
                )}
            </div>

            <div className="text-gray-600 mb-2" data-testid="constituency-party">
                {mp.constituency} • {mp.party}
            </div>

            <div
                className="party-indicator w-full h-1 rounded"
                style={{ backgroundColor: getPartyColor(mp.party) }}
                data-testid="party-indicator"
            />
        </div>
    );
}

export default MPCard;
